"""Run: python3 -m unittest discover -s plugins/doc-harvest/tests"""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "skills/doc-harvest/scripts"))
import apple_json  # noqa: E402
import harvest  # noqa: E402

REFS = {"doc://x/design/Human-Interface-Guidelines/toggles": {"title": "Toggles", "url": "/design/human-interface-guidelines/toggles"}}


class Convert(unittest.TestCase):
    def test_blocks(self):
        doc = {"abstract": [{"type": "text", "text": "Intro."}], "references": REFS, "primaryContentSections": [{"content": [
            {"type": "heading", "level": 2, "text": "Style"},
            {"type": "paragraph", "inlineContent": [{"type": "strong", "inlineContent": [{"type": "text", "text": "Do."}]},
                {"type": "text", "text": " See "}, {"type": "reference", "identifier": "doc://x/design/Human-Interface-Guidelines/toggles"}]},
            {"type": "unorderedList", "items": [{"content": [{"type": "paragraph", "inlineContent": [{"type": "text", "text": "a"}]}]}]},
            {"type": "image", "identifier": "x.png"}]}]}
        md = apple_json.to_markdown(doc)
        self.assertIn("### Style", md)
        self.assertIn("**Do.** See [Toggles](https://developer.apple.com/design/human-interface-guidelines/toggles)", md)
        self.assertIn("- a", md)
        self.assertNotIn("x.png", md)

    def test_child_paths(self):
        doc = {"topicSections": [{"identifiers": ["doc://com.apple.HIG/design/Human-Interface-Guidelines/Foo-Bar"]}]}
        self.assertEqual(apple_json.child_paths(doc, "/design/human-interface-guidelines"),
                         ["/design/human-interface-guidelines/foo-bar"])


def page(d: Path, rel: str, url: str, name: str, body="x" * 300):
    f = d / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"---\nname: {name}\nsource_url: {url}\n---\n\n# {name}\n\n{body}\n")


class Update(unittest.TestCase):
    def test_diff_and_validate(self):
        with tempfile.TemporaryDirectory() as t:
            old, new = Path(t) / "old", Path(t) / "new"
            page(old, "a/same.md", "https://h/same", "Same")
            page(old, "a/gone.md", "https://h/gone", "Gone")
            page(old, "a/iap.md", "https://h/iap", "In-App Purchase")
            page(new, "a/same.md", "https://h/same", "Same")
            page(new, "a/iap.md", "https://h/apple-iap", "In-App Purchase")
            page(new, "a/fresh.md", "https://h/fresh", "Fresh")
            self.assertEqual(set(harvest._pages(new)), {"https://h/same", "https://h/apple-iap", "https://h/fresh"})
            page(new, "a/bad.md", "https://h/bad", "Bad", body="Skip Navigation doc://x short")
            r = harvest.cmd_validate  # exit code 1 on problems
            with self.assertRaises(SystemExit) as cm:
                r(type("A", (), {"dir": str(new), "manifest": None, "min_chars": 200})())
            self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
