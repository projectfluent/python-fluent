To run the benchmarks, do:

    $ pip install -r tools/benchmarks/requirements.txt
    $ py.test ./tools/benchmarks/fluent_benchmark.py::TestBenchmark --benchmark-warmup=on

To profile the benchmark suite, we recommend py-spy as a
good tool. Install py-spy: https://github.com/benfred/py-spy

Then do something like this to profile the benchmark. Depending on your
platform, you might need to use `sudo`.

    $ py-spy -f prof.svg -- py.test ./tools/benchmarks/fluent_benchmark.py::TestBenchmark --benchmark-warmup=off

And look at prof.svg in a browser. Note that this diagram includes the fixture
setup, warmup and calibration phases which you should ignore.
