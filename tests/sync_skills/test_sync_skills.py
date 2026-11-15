import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import sync_skills  # noqa: E402


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sync_skills.main(list(argv))
    return code, out.getvalue()


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.is_symlink()) for p in Path(root).rglob("*"))


class SyncSkillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        h = self.home = Path(self.tmp.name).resolve()
        for d in (".claude/skills", ".pi/agent/skills", ".hermes/skills", ".hermes/profiles/default",
                  ".hermes/profiles/theo/skills/tdd", ".agents/skills/tdd"):
            (h / d).mkdir(parents=True)
        (h / ".agents/skills/tdd/SKILL.md").write_text("old pocock tdd\n")
        (h / ".hermes/profiles/theo/skills/tdd/SKILL.md").write_text("theo copy\n")
        self.args = ("--home", str(h))

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_changes_nothing(self):
        before = snapshot(self.home)
        code, out = run(*self.args)
        self.assertEqual(code, 0)
        self.assertIn("dry run", out)
        self.assertEqual(snapshot(self.home), before)

    def test_apply_installs_links_backs_up_and_is_idempotent(self):
        code, out = run(*self.args, "--apply")
        self.assertEqual(code, 0, out)
        canon = self.home / ".agents/skills"
        self.assertNotEqual((canon / "tdd/SKILL.md").read_text(), "old pocock tdd\n")
        self.assertFalse((canon / "debug/evals").exists(), "evals must not be installed")
        for rdir in (".claude/skills", ".pi/agent/skills", ".hermes/skills", ".hermes/profiles/theo/skills"):
            link = self.home / rdir / "grill"
            self.assertTrue(link.is_symlink() and Path(os.readlink(link)) == canon / "grill", rdir)
        self.assertFalse((self.home / ".hermes/profiles/default/skills").exists())
        backups = list((self.home / "backups").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / ".agents/skills/tdd/SKILL.md").read_text(), "old pocock tdd\n")
        self.assertEqual((backups[0] / ".hermes/profiles/theo/skills/tdd/SKILL.md").read_text(), "theo copy\n")
        code, out = run(*self.args)
        self.assertIn(" 0 changes", out)
        self.assertEqual(run("check", *self.args)[0], 0)

    def test_category_dir_is_never_replaced(self):
        cat = self.home / ".hermes/skills/research"
        (cat / "grounded-citations").mkdir(parents=True)
        (cat / "SKILL.md").write_text("category skill\n")
        (cat / "grounded-citations/SKILL.md").write_text("nested\n")
        code, out = run(*self.args, "--apply")
        self.assertEqual(code, 0, out)
        self.assertIn("conflict", out)
        self.assertFalse(cat.is_symlink())
        self.assertEqual((cat / "grounded-citations/SKILL.md").read_text(), "nested\n")
        self.assertTrue((self.home / ".pi/agent/skills/research").is_symlink())
        code, out = run("check", *self.args)
        self.assertEqual(code, 0, out)
        self.assertIn("NOTE", out)
        self.assertIn(" 0 changes", run(*self.args)[1])

    def test_same_name_elsewhere_is_a_conflict_and_our_link_is_removed(self):
        theo = self.home / ".hermes/profiles/theo/skills"
        (theo / "software-development/plan").mkdir(parents=True)
        (theo / "software-development/plan/SKILL.md").write_text("---\nname: plan\ndescription: x\n---\n")
        (theo / "plan").symlink_to(self.home / ".agents/skills/plan")  # left by an earlier sync
        code, out = run(*self.args, "--apply")
        self.assertEqual(code, 0, out)
        self.assertFalse((theo / "plan").is_symlink(), "our same-named link must be removed")
        self.assertTrue((theo / "tdd").is_symlink(), "a plain copy at the link path is still replaced")
        self.assertTrue((self.home / ".pi/agent/skills/plan").is_symlink())
        self.assertEqual(run("check", *self.args)[0], 0)
        self.assertIn(" 0 changes", run(*self.args)[1])

    def test_retired_names_are_moved_out_and_stay_out(self):
        h = self.home
        (h / ".agents/skills/triage").mkdir()
        (h / ".agents/skills/triage/SKILL.md").write_text("old triage\n")
        (h / ".pi/agent/skills/triage").symlink_to(h / ".agents/skills/triage")
        (h / ".hermes/profiles/theo/skills/triage").mkdir()
        (h / ".hermes/profiles/theo/skills/triage/SKILL.md").write_text("theo triage\n")
        code, out = run(*self.args, "--apply")
        self.assertEqual(code, 0, out)
        for p in (".agents/skills/triage", ".pi/agent/skills/triage", ".hermes/profiles/theo/skills/triage"):
            self.assertFalse((h / p).exists() or (h / p).is_symlink(), p)
        backup = next((h / "backups").iterdir())
        self.assertEqual((backup / ".hermes/profiles/theo/skills/triage/SKILL.md").read_text(), "theo triage\n")
        self.assertEqual(run("check", *self.args)[0], 0)
        (h / ".hermes/skills/triage").mkdir()
        (h / ".hermes/skills/triage/SKILL.md").write_text("back again\n")
        code, out = run("check", *self.args)
        self.assertEqual(code, 1)
        self.assertIn("retired skill is back", out)

    def test_blocks_splice_preserve_text_and_detect_edits(self):
        h = self.home
        claude = h / ".claude/CLAUDE.md"
        claude.write_text("# Global\n\n<!-- homelab-policy-20260910:start -->\nold policy\n"
                          "<!-- homelab-policy-20260910:end -->\n\n## Mine\nkeep me\n")
        soul = h / ".hermes/profiles/theo/SOUL.md"
        soul.write_text("I am Theo.\n")
        overlay = h / "overlay.md"
        overlay.write_text("## Host\nhost rule\n")
        args = (*self.args, "--blocks", "--overlay", str(overlay))
        code, out = run(*args, "--apply")
        self.assertEqual(code, 0, out)
        text = claude.read_text()
        self.assertTrue(text.startswith("# Global\n\n<!-- agent-core:start"))
        self.assertNotIn("old policy", text)
        self.assertIn("host rule", text)
        self.assertIn("~/.agents/core/LOOP.md", text)
        self.assertTrue(text.rstrip().endswith("## Mine\nkeep me"))
        self.assertTrue((h / ".agents/core/LOOP.md").is_file())
        theo = soul
        self.assertTrue(theo.read_text().startswith("I am Theo.\n\n<!-- agent-core:start"))
        self.assertFalse((h / ".hermes/profiles/sage/SOUL.md").exists())
        self.assertFalse((h / ".hermes/profiles/theo/AGENTS.md").exists())
        run(*args, "--core-only", "theo", "--apply")
        self.assertNotIn("host rule", theo.read_text())
        self.assertIn("host rule", claude.read_text())
        self.assertEqual(run("check", *self.args)[0], 0)
        args = (*args, "--core-only", "theo")
        self.assertIn("0 instruction files change", run(*args)[1])
        self.assertEqual(run("check", *self.args)[0], 0)
        claude.write_text(claude.read_text() + "\nmore of mine\n")  # outside the block: fine
        self.assertEqual(run("check", *self.args)[0], 0)
        claude.write_text(claude.read_text().replace("host rule", "host rule, edited"))
        code, out = run("check", *self.args)
        self.assertEqual(code, 1)
        self.assertIn("block edited since sync", out)
        overlay.write_text("## Host\nnew rule\n")
        run(*args, "--apply")
        self.assertIn("new rule", claude.read_text())
        self.assertIn("more of mine", claude.read_text())

    def test_two_applies_in_the_same_second_do_not_collide(self):
        from unittest import mock
        (self.home / ".hermes/profiles/theo/SOUL.md").write_text("I am Theo.\n")
        args = (*self.args, "--blocks")
        with mock.patch.object(sync_skills.time, "strftime", return_value="20990101-000000"):
            self.assertEqual(run(*args, "--apply")[0], 0)
            (self.home / ".hermes/profiles/theo/SOUL.md").write_text("I am Theo, edited.\n")
            (self.home / ".agents/skills/grill/SKILL.md").write_text("edited\n")
            self.assertEqual(run(*args, "--apply")[0], 0)
        souls = sorted(p.read_text() for p in (self.home / "backups").rglob("SOUL.md"))
        self.assertIn("I am Theo.\n", souls, "the first backup of SOUL.md must survive the second apply")
        self.assertTrue(any("edited" in t for t in souls))

    def test_check_detects_edits_and_broken_links(self):
        self.assertEqual(run("check", *self.args)[0], 1)  # never synced
        run(*self.args, "--apply")
        skill = self.home / ".agents/skills/grill/SKILL.md"
        skill.write_text(skill.read_text() + "local edit\n")
        code, out = run("check", *self.args)
        self.assertEqual(code, 1)
        self.assertIn("grill: edited since sync", out)
        run(*self.args, "--apply")
        (self.home / ".pi/agent/skills/plan").unlink()
        code, out = run("check", *self.args)
        self.assertEqual(code, 1)
        self.assertIn(".pi/agent/skills/plan: not a link", out)


if __name__ == "__main__":
    unittest.main()
