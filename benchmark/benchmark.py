"""Compare five username lookup algorithms on reproducible datasets.

Run four dataset sizes, seven trials per algorithm, and save raw and
median results as CSV in the project's results/ directory.
"""

from pathlib import Path
import csv
import math
import random
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from cuckoo_filter import CuckooFilter
from bloom_filter import BloomFilter
from hash_table import HashTable
from linear_search import linear_search
from binary_search import binary_search


# Four sizes x five algorithms x seven trials = 140 raw benchmark records.
DATASET_SIZES = (100, 1000, 5000, 10000)
REPEATS = 7
NEGATIVE_QUERY_COUNT = 10000


def next_prime(number):
    """
    Find the smallest prime greater than or equal to number.
    Input: number (integer).
    Output: Prime number (integer).
    """

    def is_prime(n):
        """
        Check whether a number is prime.
        Input: n (integer).
        Output: True if prime, otherwise False.
        """
        if n < 2:
            return False

        for i in range(2, math.isqrt(n) + 1):
            if n % i == 0:
                return False

        return True

    while not is_prime(number):
        number += 1

    return number


def generate_dataset(n, seed=2026):
    """
    Generate reproducible positive and negative usernames.
    Input: n (dataset size), seed (random seed).
    Output: Positive and negative username lists.
    """
    rng = random.Random(seed)

    usernames = []
    existing = set()

    while len(usernames) < n:
        username = f"user{rng.getrandbits(32):08x}"

        if username not in existing:
            usernames.append(username)
            existing.add(username)

    negative_queries = []
    negative_set = set()

    while len(negative_queries) < NEGATIVE_QUERY_COUNT:
        username = f"user{rng.getrandbits(32):08x}"

        if username not in existing and username not in negative_set:
            negative_queries.append(username)
            negative_set.add(username)

    return usernames, negative_queries


def benchmark_cuckoo(usernames, negative_queries):
    """
    Measure Cuckoo filter construction and lookup performance.
    Input: Positive and negative username lists.
    Output: Build time, lookup times, and false positive count.
    """
    n = len(usernames)
    bucket_size = 4

    required_buckets = math.ceil(
        n / (bucket_size * 0.8)
    )

    capacity = 1 << (
        required_buckets - 1
    ).bit_length()

    # Include data-structure initialization in build time.
    start = time.perf_counter()

    cf = CuckooFilter(
        capacity=capacity,
        bucket_size=bucket_size,
        fingerprint_bits=12,
    )

    successful = 0

    for username in usernames:
        if cf.insert(username):
            successful += 1

    build_time = time.perf_counter() - start

    start = time.perf_counter()

    positive_hits = 0

    for username in usernames:
        if cf.contains(username):
            positive_hits += 1

    positive_time = time.perf_counter() - start

    start = time.perf_counter()

    false_positives = 0

    for username in negative_queries:
        if cf.contains(username):
            false_positives += 1

    negative_time = time.perf_counter() - start

    assert successful == len(
        usernames
    ), "Cuckoo Filter insertion failed"

    assert positive_hits == len(
        usernames
    ), "Cuckoo Filter had false negatives"

    return (
        build_time * 1000,
        positive_time / len(usernames) * 1e6,
        negative_time / len(negative_queries) * 1e6,
        false_positives,
    )


def benchmark_bloom(usernames, negative_queries):
    """
    Measure Bloom filter construction and lookup performance.
    Input: Positive and negative username lists.
    Output: Build time, lookup times, and false positive count.
    """
    # Parameter selection is outside timing;
    # initialization is included.
    m = next_prime(
        10 * len(usernames)
    )

    start = time.perf_counter()

    bf = BloomFilter(
        m=m,
        k=7
    )

    for username in usernames:
        bf.add(username)

    build_time = time.perf_counter() - start

    start = time.perf_counter()

    positive_hits = 0

    for username in usernames:
        if bf.contains(username):
            positive_hits += 1

    positive_time = time.perf_counter() - start

    start = time.perf_counter()

    false_positives = 0

    for username in negative_queries:
        if bf.contains(username):
            false_positives += 1

    negative_time = time.perf_counter() - start

    assert positive_hits == len(
        usernames
    ), "Bloom Filter had false negatives"

    return (
        build_time * 1000,
        positive_time / len(usernames) * 1e6,
        negative_time / len(negative_queries) * 1e6,
        false_positives,
    )


def benchmark_hash_table(usernames, negative_queries):
    """
    Measure hash table construction and lookup performance.
    Input: Positive and negative username lists.
    Output: Build time, lookup times, and false positive count.
    """
    start = time.perf_counter()

    ht = HashTable(
        capacity=10
    )

    for username in usernames:
        ht.insert(username)

    build_time = time.perf_counter() - start

    start = time.perf_counter()

    positive_hits = 0

    for username in usernames:
        if ht.contains(username):
            positive_hits += 1

    positive_time = time.perf_counter() - start

    start = time.perf_counter()

    false_positives = 0

    for username in negative_queries:
        if ht.contains(username):
            false_positives += 1

    negative_time = time.perf_counter() - start

    assert ht.size == len(usernames)
    assert positive_hits == len(usernames)
    assert false_positives == 0

    return (
        build_time * 1000,
        positive_time / len(usernames) * 1e6,
        negative_time / len(negative_queries) * 1e6,
        false_positives,
    )


def benchmark_linear(usernames, negative_queries):
    """
    Measure linear search construction and lookup performance.
    Input: Positive and negative username lists.
    Output: Build time and positive and negative lookup times.
    """
    start = time.perf_counter()

    data = list(usernames)

    build_time = time.perf_counter() - start

    start = time.perf_counter()

    positive_hits = 0

    for username in usernames:
        if linear_search(
            data,
            username
        ):
            positive_hits += 1

    positive_time = time.perf_counter() - start

    start = time.perf_counter()

    negative_hits = 0

    for username in negative_queries:
        if linear_search(
            data,
            username
        ):
            negative_hits += 1

    negative_time = time.perf_counter() - start

    assert positive_hits == len(usernames)
    assert negative_hits == 0

    return (
        build_time * 1000,
        positive_time / len(usernames) * 1e6,
        negative_time / len(negative_queries) * 1e6,
    )


def benchmark_binary(usernames, negative_queries):
    """
    Measure binary search construction and lookup performance.
    Input: Positive and negative username lists.
    Output: Build time and positive and negative lookup times.
    """
    start = time.perf_counter()

    data = sorted(usernames)

    build_time = time.perf_counter() - start

    start = time.perf_counter()

    positive_hits = 0

    for username in usernames:
        if binary_search(
            data,
            username
        ):
            positive_hits += 1

    positive_time = time.perf_counter() - start

    start = time.perf_counter()

    negative_hits = 0

    for username in negative_queries:
        if binary_search(
            data,
            username
        ):
            negative_hits += 1

    negative_time = time.perf_counter() - start

    assert positive_hits == len(usernames)
    assert negative_hits == 0

    return (
        build_time * 1000,
        positive_time / len(usernames) * 1e6,
        negative_time / len(negative_queries) * 1e6,
    )


def save_csv(filepath, rows, fieldnames):
    """
    Save benchmark results to a CSV file.
    Input: File path, data rows, and column names.
    Output: None.
    """
    with filepath.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)


def main():
    """
    Run all benchmark experiments and save their results.
    Input: None.
    Output: None.
    """
    algorithms = [
        (
            "Linear Search",
            benchmark_linear
        ),
        (
            "Binary Search",
            benchmark_binary
        ),
        (
            "Hash Table",
            benchmark_hash_table
        ),
        (
            "Bloom Filter",
            benchmark_bloom
        ),
        (
            "Cuckoo Filter",
            benchmark_cuckoo
        ),
    ]

    raw_results = []
    summary_results = []

    for n in DATASET_SIZES:

        # All algorithms and runs at this size
        # use the same test queries.
        users, negatives = generate_dataset(n)

        assert len(users) == n

        assert (
            len(negatives)
            == NEGATIVE_QUERY_COUNT
        )

        assert not (
            set(users)
            & set(negatives)
        )

        print(
            f"\n===== Dataset size: {n} ====="
        )

        print(
            f"Negative queries: {len(negatives)}"
        )

        for name, benchmark_func in algorithms:

            runs = []

            for run_index in range(REPEATS):

                # Repeatable Cuckoo Filter eviction
                # decisions for each trial.
                if name == "Cuckoo Filter":
                    random.seed(
                        2026 + run_index
                    )

                result = benchmark_func(
                    users,
                    negatives
                )

                false_positives = (
                    result[3]
                    if len(result) == 4
                    else 0
                )

                record = {
                    "dataset_size": n,
                    "algorithm": name,
                    "run": run_index + 1,
                    "build_ms": result[0],
                    "positive_us": result[1],
                    "negative_us": result[2],
                    "false_positives": false_positives,
                    "fpr_pct":
                        false_positives
                        / len(negatives)
                        * 100,
                }

                runs.append(record)
                raw_results.append(record)

            summary = {
                "dataset_size": n,
                "algorithm": name,
                "build_ms": statistics.median(
                    row["build_ms"]
                    for row in runs
                ),
                "positive_us": statistics.median(
                    row["positive_us"]
                    for row in runs
                ),
                "negative_us": statistics.median(
                    row["negative_us"]
                    for row in runs
                ),
                "fpr_pct": statistics.median(
                    row["fpr_pct"]
                    for row in runs
                ),
            }

            summary_results.append(summary)

            print(
                f"{name}: "
                f"Build={summary['build_ms']:.3f} ms, "
                f"Positive={summary['positive_us']:.3f} us/query, "
                f"Negative={summary['negative_us']:.3f} us/query, "
                f"FPR={summary['fpr_pct']:.4f}%"
            )

    results_dir = ROOT / "results"

    results_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    raw_path = (
        results_dir
        / "benchmark_raw.csv"
    )

    summary_path = (
        results_dir
        / "benchmark_summary.csv"
    )

    save_csv(
        raw_path,
        raw_results,
        (
            "dataset_size",
            "algorithm",
            "run",
            "build_ms",
            "positive_us",
            "negative_us",
            "false_positives",
            "fpr_pct",
        ),
    )

    save_csv(
        summary_path,
        summary_results,
        (
            "dataset_size",
            "algorithm",
            "build_ms",
            "positive_us",
            "negative_us",
            "fpr_pct",
        ),
    )

    print(
        f"\nSaved {len(raw_results)} "
        f"raw records: {raw_path}"
    )

    print(
        f"Saved {len(summary_results)} "
        f"median records: {summary_path}"
    )


if __name__ == "__main__":
    main()