import unittest
from .utils import patch_files
from os.path import isdir, isfile, join


class TestFileSimulate(unittest.TestCase):
    def test_basic(self):
        @patch_files(
            {
                "the.txt": "The",
                "en": {
                    "one.txt": "One",
                    "two.txt": "Two",
                },
            }
        )
        def patch_me(a, b, root):
            self.assertEqual(a, 10)
            self.assertEqual(b, "b")
            with open(join(root, "the.txt")) as f:
                self.assertEqual(f.read(), "The")
            with open(join(root, "en", "one.txt")) as f:
                self.assertEqual(f.read(), "One")
            with open(join(root, "en", "two.txt")) as f:
                self.assertEqual(f.read(), "Two")
            self.assertTrue(isdir(join(root, "en")))
            self.assertFalse(isfile(join(root, "none.txt")))
            self.assertFalse(isfile(join(root, "en", "three.txt")))

        patch_me(10, "b")
