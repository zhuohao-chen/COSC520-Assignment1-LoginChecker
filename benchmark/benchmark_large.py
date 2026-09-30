"""Independent, fixed-size sampled-query benchmark up to 10 million usernames.

Install as benchmark/benchmark_large.py; also install
src/cuckoo_filter_large.py from the companion file.

Run from the project root, one stage at a time:
    python benchmark/benchmark_large.py --sizes 100000
    python benchmark/benchmark_large.py --sizes 1000000
    python benchmark/benchmark_large.py --sizes 10000000

Optional quick integration check:
    python benchmark/benchmark_large.py --sizes 1000 --repeats 1

This intentionally differs from the original seven-repeat benchmark:
- it samples 1,000 shared positive and 1,000 shared negative queries;
- every algorithm uses the same 1,000 positive and 1,000 negative queries;
- the large Cuckoo Filter uses transaction-log rollback, not bucket copies;
- the largest scale defaults to one run because of its construction cost.
- the 1,000 negative samples are NOT adequate for a precise low-FPR estimate;
  retain the original 10,000-negative-query experiment for FPR analysis.

Do NOT combine the resulting timings with the original benchmark in one plot
without distinguishing the different protocols/implementations.
"""

import argparse
import csv
import gc
import math
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "benchmark"))

from benchmark import generate_dataset, next_prime
from linear_search import linear_search
from binary_search import binary_search
from hash_table import HashTable
from bloom_filter import BloomFilter
from cuckoo_filter_large import LargeCuckooFilter

RESULTS_DIR = ROOT / "results"
RAW_PATH = RESULTS_DIR / "benchmark_large_raw.csv"
SUMMARY_PATH = RESULTS_DIR / "benchmark_large_summary.csv"
FIELDNAMES = (
    "dataset_size", "algorithm", "run", "build_s", "positive_us",
    "negative_us", "positive_queries", "negative_queries", "fpr_queries",
    "false_positives", "fpr_pct",
)
ALGOS = ("Linear Search", "Binary Search", "Hash Table", "Bloom Filter", "Cuckoo Filter")


def make_structure(name, usernames):
    """Construct an algorithm's structure; count initialization in build timing."""
    n = len(usernames)
    if name == "Linear Search":
        data = list(usernames)
        return data, lambda value: linear_search(data, value)
    if name == "Binary Search":
        data = sorted(usernames)
        return data, lambda value: binary_search(data, value)
    if name == "Hash Table":
        table = HashTable(capacity=10)
        for value in usernames:
            table.insert(value)
        if table.size != n:
            raise AssertionError("Hash Table did not store all usernames")
        return table, table.contains
    if name == "Bloom Filter":
        bf = BloomFilter(m=next_prime(10 * n), k=7)
        for value in usernames:
            bf.add(value)
        return bf, bf.contains
    if name == "Cuckoo Filter":
        required = math.ceil(n / (4 * 0.80))
        capacity = 1 << (required - 1).bit_length()
        cf = LargeCuckooFilter(capacity=capacity, bucket_size=4,
                               fingerprint_bits=12, max_kicks=100)
        for index, value in enumerate(usernames):
            if not cf.insert(value):
                raise RuntimeError(f"Cuckoo insertion failed at {index + 1}/{n}; "
                                   "partial timings must not be reported")
        if cf.size != n:
            raise AssertionError("Cuckoo Filter size mismatch")
        return cf, cf.contains
    raise ValueError(name)


def timed_lookups(contains, queries):
    """Return average microseconds/query and count of True responses."""
    start = time.perf_counter()
    hits = sum(bool(contains(query)) for query in queries)
    elapsed = time.perf_counter() - start
    return elapsed * 1e6 / len(queries), hits


def save_results(rows):
    """Write after each run, so interrupted long experiments retain results."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    by_group = {}
    for row in rows:
        key = (int(row["dataset_size"]), row["algorithm"])
        by_group.setdefault(key, []).append(row)

    summary_fields = ("dataset_size", "algorithm", "runs", "build_s",
                      "positive_us", "negative_us", "positive_queries",
                      "negative_queries", "fpr_queries", "fpr_pct")
    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary_fields)
        writer.writeheader()
        for (size, name), records in sorted(by_group.items()):
            output = {"dataset_size": size, "algorithm": name,
                      "runs": len(records),
                      "positive_queries": records[0]["positive_queries"],
                      "negative_queries": records[0]["negative_queries"],
                      "fpr_queries": records[0]["fpr_queries"]}
            for key in ("build_s", "positive_us", "negative_us", "fpr_pct"):
                output[key] = statistics.median(float(row[key]) for row in records)
            writer.writerow(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+",
                        default=[100_000, 1_000_000, 10_000_000],
                        help="Data sizes to benchmark (run each size separately first)")
    parser.add_argument("--repeats", type=int, default=None,
                        help="Override default repeats: 3 up to 100k, 2 up to 1M, 1 above")
    args = parser.parse_args()
    if any(n < 1 for n in args.sizes) or (args.repeats is not None and args.repeats < 1):
        parser.error("sizes and repeats must be positive")

    existing_rows = []
    if RAW_PATH.exists():
        with RAW_PATH.open(newline="", encoding="utf-8") as stream:
            existing_rows = list(csv.DictReader(stream))
    selected = set(args.sizes)
    # Rerunning a size replaces its old records without losing other sizes.
    rows = [row for row in existing_rows if int(row["dataset_size"]) not in selected]
    save_results(rows)

    for n in args.sizes:
        repeats = args.repeats or (3 if n <= 100_000 else 2 if n <= 1_000_000 else 1)
        slow_count = min(n, 1000)
        fast_count = min(n, 1000)
        print(f"\nGenerating reproducible dataset: n={n:,}", flush=True)
        usernames, negatives = generate_dataset(n, seed=2026)
        rng = random.Random(2026 + n)
        fast_positive = rng.sample(usernames, fast_count)
        fast_negative = negatives[:1000]  # Use the same 1,000 negatives for every method.
        slow_positive = fast_positive[:slow_count]
        slow_negative = fast_negative[:slow_count]
        print(f"Ready. Linear: {len(slow_positive)} positive and "
              f"{len(slow_negative)} negative; other methods: "
              f"{len(fast_positive)} positive and {len(fast_negative)} negative. "
              f"Repeats={repeats}", flush=True)

        for name in ALGOS:
            for run in range(1, repeats + 1):
                if name == "Cuckoo Filter":
                    random.seed(2026 + run - 1)
                gc.collect()
                print(f"Building {name} for n={n:,}, run={run}/{repeats}", flush=True)
                start = time.perf_counter()
                structure, contains = make_structure(name, usernames)
                build_s = time.perf_counter() - start
                if name == "Linear Search":
                    positive, negative = slow_positive, slow_negative
                else:
                    positive, negative = fast_positive, fast_negative
                positive_us, positive_hits = timed_lookups(contains, positive)
                negative_us, negative_hits = timed_lookups(contains, negative)
                if positive_hits != len(positive):
                    raise AssertionError(f"{name}: false negative detected")
                if name in ("Linear Search", "Binary Search", "Hash Table") and negative_hits:
                    raise AssertionError(f"{name}: incorrect positive for absent username")

                fpr_queries = len(negative) if name in ("Bloom Filter", "Cuckoo Filter") else 0
                row = {
                    "dataset_size": n, "algorithm": name, "run": run,
                    "build_s": build_s, "positive_us": positive_us,
                    "negative_us": negative_us,
                    "positive_queries": len(positive),
                    "negative_queries": len(negative),
                    "fpr_queries": fpr_queries,
                    "false_positives": negative_hits if fpr_queries else 0,
                    "fpr_pct": 100 * negative_hits / fpr_queries if fpr_queries else 0.0,
                }
                rows.append(row)
                save_results(rows)
                print(f"DONE: build={build_s:.3f}s, positive={positive_us:.3f}us, "
                      f"negative={negative_us:.3f}us, FPR={row['fpr_pct']:.3f}%",
                      flush=True)
                del contains, structure
                gc.collect()
        del usernames, negatives, fast_positive, fast_negative, slow_positive, slow_negative
        gc.collect()
    print(f"\nSaved {RAW_PATH} and {SUMMARY_PATH}", flush=True)


if __name__ == "__main__":
    main()
