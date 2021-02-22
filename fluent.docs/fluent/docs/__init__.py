from pathlib import Path
from .build import DocBuilder


def finalize_builddir(repo_name):
    'Bookkeeping on the docs build directory'
    root = Path('_build') / repo_name
    with open(root / '.nojekyll', 'w') as fh:
        fh.write('')


def build_root(repo_name):
    '''Build the top-level documentation.

    See :py:mod:`.build` on building sub-projects.
    '''
    with DocBuilder(repo_name, '.') as builder:
        builder.build()
