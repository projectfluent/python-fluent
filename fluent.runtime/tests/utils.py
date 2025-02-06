"""Utilities for testing."""

import textwrap
from pathlib import PurePath
from unittest import mock
from io import StringIO
import functools


def dedent_ftl(text):
    return textwrap.dedent(f"{text.rstrip()}\n")


# Unify path separator, default path separator on Windows is \ not /
# Supports only relative paths
# Needed in test_falllback.py because it uses dict + string compare to make a virtual file structure
def _normalize_path(path):
    path = PurePath(path)
    if path.is_absolute():
        raise ValueError("Absolute paths are not supported in file simulation yet. ("
                         + str(path) + ")")
    if "." not in path.parts and ".." not in path.parts:
        return "/".join(PurePath(path).parts)
    else:
        res_parts = []
        length = len(path.parts)
        i = 0
        while i < length:
            if path.parts[i] == ".":
                i += 1
            elif i < length - 1 and path.parts[i+1] == "..":
                i += 2
            else:
                res_parts.append(path.parts[i])
                i += 1
        return "/".join(res_parts)


def patch_files(files: dict):
    """Decorate a function to simulate files ``files`` during the function.

    The keys of ``files`` are file names and must use '/' for path separator.
    The values are file contents. Directories or relative paths are not supported.
    Example: ``{"en/one.txt": "One", "en/two.txt": "Two"}``

    The implementation may be changed to match the mechanism used.
    """
    if files is None:
        files = {}

    def then(func):
        @mock.patch("os.path.isfile", side_effect=lambda p: _normalize_path(p) in files)
        @mock.patch("codecs.open", side_effect=lambda p, _, __: StringIO(files[_normalize_path(p)]))
        @functools.wraps(func)  # Make ret look like func to later decorators
        def ret(*args, **kwargs):
            func(*args[:-2], **kwargs)
        return ret
    return then
