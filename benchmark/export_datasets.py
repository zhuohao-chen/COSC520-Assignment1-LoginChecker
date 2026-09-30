
from pathlib import Path
from benchmark.benchmark import generate_dataset, DATASET_SIZES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

for n in DATASET_SIZES:
    positive, negative = generate_dataset(n, seed=2026)

    positive_file = DATA_DIR / f"benchmark_positive_{n}.txt"
    negative_file = DATA_DIR / f"benchmark_negative_{n}.txt"

    positive_file.write_text(
        "\n".join(positive) + "\n",
        encoding="utf-8"
    )

    negative_file.write_text(
        "\n".join(negative) + "\n",
        encoding="utf-8"
    )

    print(f"Exported dataset n={n}")
    print(f"  Positive: {len(positive)}")
    print(f"  Negative: {len(negative)}")
