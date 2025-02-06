import unittest
from .utils import patch_files
import os
import codecs


class TestFileSimulate(unittest.TestCase):
    def test_basic(self):
        @patch_files({
            "the.txt": "The",
            "en/one.txt": "One",
            "en/two.txt": "Two"
        })
        def patch_me(a, b):
            self.assertEqual(a, 10)
            self.assertEqual(b, "b")
            self.assertFileIs(os.path.basename(__file__), None)
            self.assertFileIs("the.txt", "The")
            self.assertFileIs("en/one.txt", "One")
            self.assertFileIs("en\\one.txt", "One")
            self.assertFileIs("en/two.txt", "Two")
            self.assertFileIs("en\\two.txt", "Two")
            self.assertFileIs("en/three.txt", None)
            self.assertFileIs("en\\three.txt", None)
        patch_me(10, "b")

    def assertFileIs(self, filename, expect_contents):
        """
        expect_contents is None: Expect file does not exist
        expect_contents is a str: Expect file to exist and contents to match
        """
        if expect_contents is None:
            self.assertFalse(os.path.isfile(filename),
                             f"Expected {filename} to not exist.")
        else:
            self.assertTrue(os.path.isfile(filename),
                            f"Expected {filename} to exist.")
            with codecs.open(filename, "r", "utf-8") as f:
                self.assertEqual(f.read(), expect_contents)
