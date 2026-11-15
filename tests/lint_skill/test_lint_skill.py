import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "lint_skill", ROOT / "plugins/core/skills/skill-authoring/scripts/lint_skill.py")
lint_skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_skill)

BODY = "\n# X\n\n1. Do it.\n\n## Done when\n\n- done\n"


def make_skill(root, description):
    d = Path(root) / "demo"
    (d / "evals/a").mkdir(parents=True)
    (d / "evals/b").mkdir(parents=True)
    for c in ("a", "b"):
        (d / f"evals/{c}/task.md").write_text("t\n")
        chk = d / f"evals/{c}/check"
        chk.write_text("#!/bin/sh\nexit 0\n")
        chk.chmod(0o755)
    (d / "PROVENANCE.md").write_text("- none\n")
    (d / "SKILL.md").write_text(f"---\nname: demo\ndescription: {description}\n---\n{BODY}")
    return str(d)


class YamlSafety(unittest.TestCase):
    def errs(self, description):
        with tempfile.TemporaryDirectory() as t:
            return [e for e in lint_skill.lint(make_skill(t, description)) if "frontmatter" in e]

    def test_unquoted_colon_space_fails(self):
        self.assertTrue(self.errs("Close a session: update docs. Use at the end."))

    def test_unquoted_hash_and_trailing_colon_fail(self):
        self.assertTrue(self.errs("Tag issues #1 and #2 then stop"))
        self.assertTrue(self.errs("Use it for:"))

    def test_double_quoted_passes(self):
        self.assertEqual(self.errs('"Close a session: update docs, say \\"done\\". Use at the end."'), [])

    def test_plain_safe_value_passes(self):
        self.assertEqual(self.errs("Fix a bug by reproducing it first. Use when broken."), [])

    def test_unescaped_inner_quote_fails(self):
        self.assertTrue(self.errs('"say "done" now"'))


if __name__ == "__main__":
    unittest.main()
