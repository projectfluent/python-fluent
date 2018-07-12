To run the benchmarks, do:

    $ pip install pytest pytest-benchmark
    $ ./tools/benchmark/benchmark.py

To profile a specific test in the benchmark suite, we recommend pyflame as a
good tool. Install pyflame: https://github.com/uber/pyflame

You will need to ensure that you have Python headers installed for the version
of Python that you want to test.

Also install flamegraph: https://github.com/brendangregg/FlameGraph

Then do something like this to profile the `test_plural_form_select_fluent_compiler` benchmark.

    $ pyflame -o prof.txt -t py.test ./tools/benchmarks/benchmark.py --benchmark-warmup=on -k test_plural_form_select_fluent_compiler
    $ flamegraph.pl prof.txt > prof.svg

And look at prof.svg in a browser. Note that this diagram includes the fixture
setup, warmup and calibration phases which you should ignore.
