import unittest
from shipcode import make_code


class H(unittest.TestCase):
    def test_values(self):
        for n, want in [(42, "SC-0042-4"), (1234, "SC-1234-8"), (0, "SC-0000-0"),
                        (9999, "SC-9999-2"), (7, "SC-0007-7"), (305, "SC-0305-8"), (5050, "SC-5050-0")]:
            self.assertEqual(make_code(n), want)
    def test_errors(self):
        for bad in (-1, 10000, 1.5, "7"):
            with self.assertRaises(ValueError):
                make_code(bad)


if __name__ == "__main__":
    unittest.main()
