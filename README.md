
# COSC 520 Assignment 1: The Login Checker Problem

This project implements and compares five approaches to checking username uniqueness:

1. Linear Search
2. Binary Search
3. Separate-Chaining Hash Table
4. Bloom Filter
5. Cuckoo Filter

## Environment

- Python 3.9 or later
- No third-party Python packages are required for the algorithms and benchmarks.

The experiments reported in the assignment were conducted using Python 3.9.0 on Windows with an Intel Core i9-14900HX processor and 64 GB of RAM.

## Project Structure

- `src/`: Implementations of the five algorithms.
- `tests/`: Unit tests.
- `benchmark/benchmark.py`: Performance evaluation.
- `benchmark/export_datasets.py`: Export the benchmark datasets.
- `benchmark/generate_data.py`: Generate a separate example dataset.
- `data/`: Public datasets.
- `results/`: Benchmark results in CSV format.

## Running Unit Tests

From the project root directory, run:

```bash
python -m unittest discover -s tests -v
```

## Generating Benchmark Datasets

Run:

```bash
python -m benchmark.export_datasets
```

This generates datasets containing 100, 1,000, 5,000, and 10,000 unique usernames. Each dataset has an additional 10,000 negative queries.

Username generation uses a fixed random seed of 2026.

Note that `generate_data.py` produces a separate example dataset. The formal benchmark uses `generate_dataset()` in `benchmark.py`.

## Running the Benchmark

From the project root directory, run:

```bash
python benchmark/benchmark.py
```

The benchmark evaluates all five methods across four dataset sizes, with seven repetitions per method.

Measured metrics include:
- Construction time (milliseconds)
- Positive lookup time (microseconds per query)
- Negative lookup time (microseconds per query)
- False positive rate

The benchmark saves its results to:

- `results/benchmark_raw.csv`
- `results/benchmark_summary.csv`

Runtime measurements may vary depending on the computer and execution environment.

## Notes

Linear Search, Binary Search, and the Hash Table perform exact membership checks.

Bloom Filters and Cuckoo Filters perform approximate membership checks and may produce false positives. Consequently, they cannot independently guarantee username uniqueness.

## Large-scale Evaluation

The additional benchmark evaluates 100,000, 1,000,000, and 10,000,000 usernames using 1,000 positive and 1,000 negative queries per method.

Run each dataset size separately from the project root:

```bash
python benchmark/benchmark_large.py --sizes 100000
python benchmark/benchmark_large.py --sizes 1000000
python benchmark/benchmark_large.py --sizes 10000000
```

The large-scale experiment uses a separate Cuckoo Filter implementation with optimized rollback. Its results are saved to `results/benchmark_large_raw.csv` and `results/benchmark_large_summary.csv`.

To regenerate the large-scale comparison figure, install Matplotlib and run:

```bash
python plot_large_lookup.py
```
