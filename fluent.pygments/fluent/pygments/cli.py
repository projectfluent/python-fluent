from __future__ import absolute_import, print_function, unicode_literals

import argparse
import sys

from pygments import highlight
from pygments.formatters import Terminal256Formatter
from fluent.pygments.lexer import FluentLexer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    args = parser.parse_args()
    with open(args.path) as fh:
        code = fh.read()
    highlight(code, FluentLexer(), Terminal256Formatter(), sys.stdout)


if __name__ == '__main__':
    main()
