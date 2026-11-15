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

    def test_missing_skill_is_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(eval_skill.main([str(HERE)]), 2)


if __name__ == "__main__":
    unittest.main()
