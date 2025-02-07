"""Utilities for testing."""

import textwrap
from pathlib import PureWindowsPath, PurePosixPath
from unittest import mock
from io import StringIO
import functools


def dedent_ftl(text):
    return textwrap.dedent(f"{text.rstrip()}\n")


# Needed in test_falllback.py because it uses dict + string compare to make a virtual file structure
def _normalize_file_path(path):
    """Note: Does not support absolute paths or paths that
    contain '.' or '..' parts."""
    # Cannot use os.path or PurePath, because they only recognize
    # one kind of path separator
    if PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute():
        raise ValueError(f"Unsupported path: {path}")
    parts = path.replace("\\", "/").split("/")
    if "." in parts or ".." in parts:
        # path ends with a trailing pathsep
        raise ValueError(f"Unsupported path: {path}")
    if parts and parts[-1] == "":
        raise ValueError(f"Path appears to be a directory, not a file: {path}")
    return "/".join(parts)


def patch_files(files: dict):
    """Decorate a function to simulate files ``files`` during the function.

    The keys of ``files`` are file names and must use '/' for path separator.
    The values are file contents. Directories or relative paths are not supported.
    Example: ``{"en/one.txt": "One", "en/two.txt": "Two"}``

    The implementation may be changed to match the mechanism used.
    """

    # Here it is possible to validate file names, but skipped

    def then(func):
        @mock.patch("os.path.isfile", side_effect=lambda p: _normalize_file_path(p) in files)
        @mock.patch("codecs.open", side_effect=lambda p, _, __: StringIO(files[_normalize_file_path(p)]))
        @functools.wraps(func)  # Make ret look like func to later decorators
        def ret(*args, **kwargs):
            func(*args[:-2], **kwargs)
        return ret
    return then
