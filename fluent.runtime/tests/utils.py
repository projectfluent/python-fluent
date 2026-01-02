"""Utilities for testing."""

import textwrap
from os import mkdir
from os.path import join


def dedent_ftl(text):
    return textwrap.dedent(f"{text.rstrip()}\n")


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
