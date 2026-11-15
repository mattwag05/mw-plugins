import unittest

from sync import fetch


class TestFetch(unittest.TestCase):
    def test_fetch_succeeds(self):
        # Fails about 3% of runs in CI.
        self.assertEqual(fetch("https://example.invalid/a"), "ok")


if __name__ == "__main__":
    unittest.main()
