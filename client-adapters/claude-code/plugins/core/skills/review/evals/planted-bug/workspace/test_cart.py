import unittest
from cart import total


class T(unittest.TestCase):
    def test_discount(self):
        self.assertEqual(total([60.0, 60.0]), 108.0)

    def test_no_discount(self):
        self.assertEqual(total([50.0]), 50.0)


if __name__ == "__main__":
    unittest.main()
