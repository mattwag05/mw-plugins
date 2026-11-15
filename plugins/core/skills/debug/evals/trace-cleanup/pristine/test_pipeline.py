import unittest
from pipeline import render


class T(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(render("a, b"), "a | b")


if __name__ == "__main__":
    unittest.main()
