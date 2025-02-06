"""Utilities for testing.

Import this module before patching libraries.
"""

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
    """Note: Does not support absolute paths or paths that
    contain '.' or '..' parts."""
    path = PurePath(path)
    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise ValueError(f"Unsupported path: {path}")
    return "/".join(path.parts)


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
