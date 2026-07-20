#!/usr/bin/env python3
"""Summarize collected turn costs, and test whether prompts predict them.

Two modes:

    report_usage.py                 what has been spent, by session and project
    report_usage.py --predictive    does anything here actually predict cost?

The second mode exists because the premise behind estimating a prompt's cost
before running it is unproven. It reports cost split by turn depth, so you can
see how much of the variance is explained by position in the session rather than
by what was asked. If the spread within a depth band is still wide, prompt-based
estimation has nothing to stand on and should not be built.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from collect_usage import data_dir  # noqa: E402

DEPTH_BANDS = [(0, 4), (5, 14), (15, 39), (40, 10**9)]


def load_sessions() -> list:
    sessions = data_dir() / "sessions"
    records = []
    if not sessions.is_dir():
        return records
    for path in sorted(sessions.glob("*.json")):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return records


def percentile(values: list, fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(int(len(ordered) * fraction), len(ordered) - 1)]


def fmt(n: float) -> str:
    return f"{n / 1000:,.0f}k" if n < 1_000_000 else f"{n / 1_000_000:.2f}M"


def report(records: list) -> None:
    if not records:
        print("No sessions recorded yet. The collector writes one file per session on Stop.")
        return

    all_turns = [t for r in records for t in r.get("turns", [])]
    total = sum(t.get("weighted", 0.0) for t in all_turns)
    print(f"Sessions: {len(records)}   Turns: {len(all_turns)}   Total: {fmt(total)} weighted tokens\n")

    by_project = {}
    for record in records:
        project = record.get("project") or "?"
        by_project.setdefault(project, []).append(
            sum(t.get("weighted", 0.0) for t in record.get("turns", []))
        )
    print("By project:")
    for project, costs in sorted(by_project.items(), key=lambda kv: -sum(kv[1])):
        print(f"  {project:<28} {fmt(sum(costs)):>10}  ({len(costs)} sessions)")

    print("\nMost expensive turns:")
    for turn in sorted(all_turns, key=lambda t: -t.get("weighted", 0.0))[:8]:
        excerpt = turn.get("prompt_excerpt", "")[:64]
        print(f"  {fmt(turn.get('weighted', 0.0)):>10}  #{turn.get('index', 0):<4} {excerpt}")


def predictive(records: list) -> None:
    """Split cost by turn depth to expose the session-position confound."""
    all_turns = [t for r in records for t in r.get("turns", [])]
    costs = [t.get("weighted", 0.0) for t in all_turns if t.get("weighted", 0.0) > 0]
    if len(costs) < 30:
        print(f"Only {len(costs)} scored turns. Too few to conclude anything -- keep collecting.")
        if not costs:
            return

    print(f"All turns (n={len(costs)}):")
    print(f"  p10={fmt(percentile(costs, 0.1))}  p50={fmt(statistics.median(costs))}  "
          f"p90={fmt(percentile(costs, 0.9))}  max={fmt(max(costs))}")
    print(f"  p90/p50 spread: {percentile(costs, 0.9) / max(statistics.median(costs), 1):.1f}x\n")

    print("By turn depth (does position explain the cost?):")
    print(f"  {'depth':<10} {'n':>5} {'p50':>10} {'p90':>10} {'p90/p50':>9}")
    for low, high in DEPTH_BANDS:
        band = [
            t.get("weighted", 0.0)
            for t in all_turns
            if low <= t.get("index", 0) <= high and t.get("weighted", 0.0) > 0
        ]
        if not band:
            continue
        label = f"{low}-{high}" if high < 10**9 else f"{low}+"
        median = statistics.median(band)
        p90 = percentile(band, 0.9)
        print(f"  {label:<10} {len(band):>5} {fmt(median):>10} {fmt(p90):>10} "
              f"{p90 / max(median, 1):>8.1f}x")

    print(
        "\nHow to read this: if p90/p50 stays wide *within* each depth band, then what you\n"
        "asked for explains little once position is controlled for, and estimating a prompt's\n"
        "cost up front will not work. A narrow within-band spread is what would justify it."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictive", action="store_true",
                        help="test whether cost is predictable rather than just summarizing it")
    args = parser.parse_args()

    records = load_sessions()
    if args.predictive:
        predictive(records)
    else:
        report(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
