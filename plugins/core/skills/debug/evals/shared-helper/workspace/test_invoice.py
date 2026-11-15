import unittest
from invoice import total_cents


class T(unittest.TestCase):
    def test_round_prices(self):
        self.assertEqual(total_cents([("10.00", 2)]), 2000)


if __name__ == "__main__":
    unittest.main()
