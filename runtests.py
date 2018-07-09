#!/usr/bin/env python

import argparse
import subprocess
import sys

parser = argparse.ArgumentParser(
    description="Run the test suite, or some tests")
parser.add_argument('--coverage', "-c", action='store_true',
                    help="Run with 'coverage'")
parser.add_argument('--verbose', '-v', action='store_true')
parser.add_argument('test', type=str, nargs="*",
                    help="Dotted path to a test module, case or method")

args = parser.parse_args()

cmd = ["-m", "unittest"]

if args.test:
    cmd.extend(args.test)
else:
    cmd.extend(["discover", "-t", ".", "-s", "tests"])

if args.verbose:
    cmd.append("-v")

if args.coverage:
    cmd = ["-m", "coverage", "run"] + cmd

cmd.insert(0, "python")

sys.exit(subprocess.call(cmd))
