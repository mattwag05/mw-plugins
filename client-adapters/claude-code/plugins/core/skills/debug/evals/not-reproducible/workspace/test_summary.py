import unittest
from summary import monthly_total


class T(unittest.TestCase):
    def test_total(self):
        self.assertEqual(monthly_total([(1, 5), (2, 7)]), 12)
        self.assertEqual(monthly_total([]), 0)


if __name__ == "__main__":
    unittest.main()
