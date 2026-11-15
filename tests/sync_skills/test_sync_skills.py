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
