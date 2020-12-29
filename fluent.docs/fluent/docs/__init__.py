from pathlib import Path
from .build import DocBuilder


def finalize_builddir(repo_name):
    root = Path('_build') / repo_name
    with open(root / '.nojekyll', 'w') as fh:
        fh.write('')


def build_root(repo_name):
    with DocBuilder(repo_name, '.') as builder:
        builder.build()
