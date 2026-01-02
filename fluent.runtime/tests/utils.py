"""Utilities for testing."""

import textwrap
from functools import wraps
from os import mkdir
from os.path import join
from tempfile import TemporaryDirectory


def dedent_ftl(text):
    return textwrap.dedent(f"{text.rstrip()}\n")


def patch_files(tree: dict):
    def build_file_tree(root: str, tree: dict) -> None:
        for name, value in tree.items():
            path = join(root, name)
            if isinstance(value, str):
                with open(path, "x", encoding="utf-8", newline="\n") as file:
                    if value:
                        file.write(value)
            else:
                mkdir(path)
                build_file_tree(path, value)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with TemporaryDirectory() as root:
                build_file_tree(root, tree)
                return fn(*args, root, **kwargs)

        return wrapper

    return decorator
