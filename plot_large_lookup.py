import csv
from pathlib import Path
import matplotlib.pyplot as plt

INPUT_FILE = Path("results/benchmark_large_summary.csv")
OUTPUT_FILE = Path("results/large_scale_lookup_both.png")

positive_data = {}
negative_data = {}

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        n = int(row["dataset_size"])
        algorithm = row["algorithm"]
        positive_us = float(row["positive_us"])
        negative_us = float(row["negative_us"])

        positive_data.setdefault(algorithm, []).append((n, positive_us))
        negative_data.setdefault(algorithm, []).append((n, negative_us))

for algorithm in positive_data:
    positive_data[algorithm].sort(key=lambda x: x[0])

for algorithm in negative_data:
    negative_data[algorithm].sort(key=lambda x: x[0])

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

# Left: Positive lookup
ax = axes[0]
for algorithm, values in positive_data.items():
    xs = [v[0] for v in values]
    ys = [v[1] for v in values]
    ax.plot(xs, ys, marker="o", label=algorithm)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Dataset size")
ax.set_ylabel("Positive lookup time (μs/query)")
ax.set_title("Large-scale Positive Lookup")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend()

# Right: Negative lookup
ax = axes[1]
for algorithm, values in negative_data.items():
    xs = [v[0] for v in values]
    ys = [v[1] for v in values]
    ax.plot(xs, ys, marker="o", label=algorithm)

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Dataset size")
ax.set_ylabel("Negative lookup time (μs/query)")
ax.set_title("Large-scale Negative Lookup")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend()

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
print(f"Saved figure to: {OUTPUT_FILE}")