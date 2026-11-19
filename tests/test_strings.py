import unittest

from textkit.strings import squeeze


class SqueezeTest(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual(squeeze("  a \n b\t c "), "a b c")


if __name__ == "__main__":
    unittest.main()
