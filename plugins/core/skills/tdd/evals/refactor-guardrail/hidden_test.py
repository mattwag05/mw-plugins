import unittest
from shipping import shipping_cost as s

CASES = [('local', 0.5, 5.0), ('local', 1, 5.0), ('local', 3, 9.0), ('local', 5, 13.0), ('local', 8, 17.5),
         ('national', 0.5, 8.0), ('national', 1, 8.0), ('national', 3, 14.0), ('national', 5, 20.0), ('national', 8, 27.5),
         ('intl', 0.5, 20.0), ('intl', 1, 20.0), ('intl', 3, 32.0), ('intl', 5, 44.0), ('intl', 8, 59.0)]


class H(unittest.TestCase):
    def test_values(self):
        for z, w, want in CASES:
            self.assertEqual(s(w, z), want)
    def test_unknown_zone(self):
        with self.assertRaises(ValueError):
            s(1, "moon")


if __name__ == "__main__":
    unittest.main()
