import unittest
from pipeline import render, first_word


class H(unittest.TestCase):
    def test_render(self):
        self.assertEqual(render("Apple, banana, apple"), "Apple | banana")
        self.assertEqual(render("x, X, y, Y, x"), "x | y")
    def test_first(self):
        self.assertEqual(first_word("Zed, zed"), "Zed")


if __name__ == "__main__":
    unittest.main()
