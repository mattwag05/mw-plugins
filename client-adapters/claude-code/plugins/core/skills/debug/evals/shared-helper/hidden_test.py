import unittest
from invoice import total_cents
from refund import refund_cents


class H(unittest.TestCase):
    def test_invoice(self):
        self.assertEqual(total_cents([("0.29", 1)]), 29)
        self.assertEqual(total_cents([("1.15", 2), ("10.00", 1)]), 1230)
    def test_refund(self):
        self.assertEqual(refund_cents("0.57", 1), 57)
        self.assertEqual(refund_cents("4.35", 3, 50), 1255)


if __name__ == "__main__":
    unittest.main()
