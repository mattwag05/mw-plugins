import unittest

import stats


class TestCount(unittest.TestCase):
    def test_count(self):
        self.assertEqual(stats.count_words(__file__)["import"], 2)


if __name__ == "__main__":
    unittest.main()
