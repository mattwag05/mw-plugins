import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
import eval_skill  # noqa: E402

SKILL = HERE / "fixture-skill"
FAKE = f"{sys.executable} {HERE / 'fake_agent.py'}"


def run(*extra):
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(out):
        code = eval_skill.main([str(SKILL), "--agent-cmd", FAKE, "--out", d, *extra])
    return code, out.getvalue()


class EvalSkillTest(unittest.TestCase):
    def test_good_case_passes(self):
        code, out = run("--case", "good")
        self.assertEqual(code, 0, out)
        self.assertIn("PASS good run 1/1", out)

    def test_known_bad_case_fails(self):
        code, out = run("--case", "bad")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL bad run 1/1", out)

    def test_summary_counts_failed_cases(self):
        code, out = run("--runs", "2")
        self.assertEqual(code, 1, out)
        self.assertIn("1/2 cases passed", out)

    def test_failing_agent_is_a_fail(self):
        with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()) as out:
            code = eval_skill.main([str(SKILL), "--agent-cmd", "false", "--out", d, "--case", "good"])
        self.assertEqual(code, 1)
        self.assertIn("agent exited 1", out.getvalue())

    def test_setup_runs_before_agent(self):
        with tempfile.TemporaryDirectory() as d:
            skill = Path(d) / "s"
            case = skill / "evals" / "prep"
            case.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: s\ndescription: x\n---\n")
            (case / "task.md").write_text("noop\n")
            for name, body in (("setup", "touch prepared"), ("check", "test -f prepared && test -f agent_saw_it")):
                (case / name).write_text(f"#!/bin/sh\n{body}\n")
                (case / name).chmod(0o755)
            agent = "sh -c 'test -f prepared && touch agent_saw_it' agent"
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = eval_skill.main([str(skill), "--agent-cmd", agent, "--out", str(Path(d) / "out")])
            self.assertEqual(code, 0, out.getvalue())

    def test_write_into_skill_dir_fails_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            skill = Path(d) / "s"
            case = skill / "evals" / "stray"
            case.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: s\ndescription: x\n---\n")
            (case / "task.md").write_text("noop\n")
            (case / "check").write_text("#!/bin/sh\ntrue\n")
            (case / "check").chmod(0o755)
            agent = "sh -c 'touch \"$1/evals/stray/leaked\"' agent"
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = eval_skill.main([str(skill), "--agent-cmd", agent, "--out", str(Path(d) / "out")])
            self.assertEqual(code, 1, out.getvalue())
            self.assertIn("wrote outside the workspace: evals/stray/leaked", out.getvalue())

    def test_missing_skill_is_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(eval_skill.main([str(HERE)]), 2)


if __name__ == "__main__":
    unittest.main()
