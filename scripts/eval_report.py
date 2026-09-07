#!/usr/bin/env python3
"""Turns `claude plugin eval` result documents into this repository's records.

Reads `evals/<plugin>/results/{behavior,mechanics,triggering}.json`, which
`scripts/run_evals.py` writes, and groups each document's cases by skill. A case
directory is `evals/<plugin>/<skill>/<case>` for a behavior or mechanics case,
and `evals/<plugin>/<skill>/triggering/<fire|hold>-NN` for a probe, so the skill
is the third segment.

Writes `evals/SWEEP.md` and `evals/TRIGGERING.md`, and prints the score
strings that README.md carries per skill: `+N pts vs. no skill` from a
behavior document, and `Scores N%` from a mechanics one. A partial document
yields no string, because a partial run is not a measurement.

Every table carries pass@k and pass^k beside the mean score, because the agent
is not deterministic. `aggregates.passRate` is the fraction of a case's runs
that scored a full 1.0, so pass@k, the case passing at least once, is that
fraction above zero, and pass^k, the case passing every time, is that fraction
at exactly one. A wide gap between the two names a flaky case, and a wide gap
across a whole skill names a flaky skill. Read pass^k for a skill that has to
work every time, and pass@k for one where a single good answer is enough. Both
collapse into the mean score at `--runs 1`, which is why one run is a smoke run
and not a measurement.

The result document is an additive-only public contract: field names are
camelCase, and a reader tolerates unknown fields. A document marked `partial`
did not finish, so it is reported and never presented as a measurement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVALS = REPO / "evals"
TAGS = ("behavior", "mechanics", "triggering")


def skill_of(case: dict) -> str:
    parts = Path(case["dir"]).parts
    # evals/<plugin>/<skill>/<case>
    return parts[2] if len(parts) > 2 and parts[0] == "evals" else parts[-1]


def probe_kind(case: dict) -> str | None:
    """`fire`, `hold`, or None when the case is not a triggering probe."""
    parts = Path(case["dir"]).parts
    if "triggering" not in parts:
        return None
    leaf = parts[-1]
    return "fire" if leaf.startswith("fire") else "hold" if leaf.startswith("hold") else None


def documents() -> dict[tuple[str, str], dict]:
    found = {}
    for path in sorted(REPO.glob("evals/*/results/*.json")):
        if path.stem not in TAGS:
            continue
        doc = json.loads(path.read_text())
        if doc.get("schemaVersion") != 1:
            print(f"warning: {path} has schemaVersion "
                  f"{doc.get('schemaVersion')!r}, expected 1", file=sys.stderr)
        found[(path.parents[1].name, path.stem)] = doc
    return found


def plugin_problems(doc: dict) -> list[str]:
    """Problem codes that mean the with-arm ran without the plugin.

    `identity_unverified` and `archive_not_probed` say nothing about loading, so
    they are not problems here.
    """
    blocking = {"manifest_invalid", "disabled_by_default", "will_not_load"}
    plugins = doc.get("suite", {}).get("plugins", [])
    if not plugins:
        return ["no plugin resolved"]
    return [f"{p['name']}: {p['problem']}" for p in plugins
            if p.get("problem") in blocking]


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def runs_of(case: dict) -> int:
    """How many times the with-arm ran, which is the k in pass@k and pass^k."""
    return len(case["arms"]["with"])


def pass_at_k(case: dict) -> bool:
    """The case scored a full 1.0 in at least one run."""
    return case["aggregates"]["passRate"] > 0


def pass_pow_k(case: dict) -> bool:
    """The case scored a full 1.0 in every run."""
    return case["aggregates"]["passRate"] == 1.0


def behavior_rows(doc: dict) -> dict[str, dict]:
    """Per-skill score, baseline score and delta."""
    by_skill: dict[str, list[dict]] = {}
    for case in doc["cases"]:
        if probe_kind(case):
            continue
        by_skill.setdefault(skill_of(case), []).append(case)

    rows = {}
    for skill, cases in sorted(by_skill.items()):
        agg = [c["aggregates"] for c in cases]
        rows[skill] = {
            "cases": len(cases),
            "runs": max(runs_of(c) for c in cases),
            "score": mean([a["score"] for a in agg]),
            # scoreWithout and delta are absent when the arms are not comparable.
            "without": mean([a["scoreWithout"] for a in agg if "scoreWithout" in a]),
            "delta": mean([a["delta"] for a in agg if "delta" in a]),
            "at_k": sum(1 for c in cases if pass_at_k(c)),
            "pow_k": sum(1 for c in cases if pass_pow_k(c)),
            "fired": sum(1 for c in cases if case_fired(c)),
        }
    return rows


def case_fired(case: dict) -> bool:
    """Whether the with-arm's plugin-fired indicator passed in every run."""
    runs = case["arms"]["with"]
    indicators = [g for r in runs for g in r["graders"]
                  if g["name"] == "fires-the-skill"]
    return bool(indicators) and all(g["passed"] for g in indicators)


def triggering_rows(doc: dict) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for case in doc["cases"]:
        kind = probe_kind(case)
        if not kind:
            continue
        row = rows.setdefault(skill_of(case),
                              {"fire": [0, 0, 0], "hold": [0, 0, 0], "runs": 1})
        row["runs"] = max(row["runs"], runs_of(case))
        row[kind][2] += 1
        row[kind][0] += int(pass_pow_k(case))
        row[kind][1] += int(pass_at_k(case))
    return dict(sorted(rows.items()))


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def signed(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:+.1f}%"


def readme_string(tag: str, row: dict) -> str | None:
    """The score string README.md carries, or None when there is none to carry."""
    if tag == "behavior" and row["delta"] is not None:
        return f"{row['delta'] * 100:+.0f} pts vs. no skill"
    if tag == "mechanics" and row["score"] is not None:
        return f"Scores {row['score'] * 100:.0f}%"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="write evals/SWEEP.md and evals/TRIGGERING.md")
    args = ap.parse_args()

    docs = documents()
    if not docs:
        print("no result documents under evals/*/results/", file=sys.stderr)
        return 1

    sweep = ["# Sweep", "",
             "Generated by `scripts/eval_report.py`. Do not edit by hand.", ""]
    trig = ["# Triggering", "",
            "Generated by `scripts/eval_report.py`. Do not edit by hand.", ""]
    readme: list[str] = []
    warnings: list[str] = []

    for (plugin, tag) in sorted(docs):
        doc = docs[(plugin, tag)]
        head = (f"{plugin} · {tag} · {doc['claudeVersion']} · "
                f"{doc['startedAt']} · ${doc['costUsd']:.2f}")
        if doc.get("partial"):
            warnings.append(f"{plugin}/{tag}: partial run "
                            f"({doc.get('partialReason')}) — not a measurement")
        for problem in plugin_problems(doc):
            warnings.append(f"{plugin}/{tag}: {problem} — the with-arm ran "
                            "without the plugin")

        if tag == "triggering":
            trig += [f"## {head}", "",
                     "| Skill | Runs | Fires (pass^k) | Fires (pass@k) | "
                     "Holds (pass^k) | Holds (pass@k) |",
                     "|---|---|---|---|---|---|"]
            for skill, row in triggering_rows(doc).items():
                fp, fa, ft = row["fire"]
                hp, ha, ht = row["hold"]
                trig.append(f"| {skill} | {row['runs']} | {fp}/{ft} | {fa}/{ft} | "
                            f"{hp}/{ht} | {ha}/{ht} |")
            trig.append("")
        else:
            sweep += [f"## {head}", "",
                      "| Skill | Cases | Runs | Score | Baseline | Delta | "
                      "pass@k | pass^k | Fired |",
                      "|---|---|---|---|---|---|---|---|---|"]
            for skill, row in behavior_rows(doc).items():
                sweep.append(
                    f"| {skill} | {row['cases']} | {row['runs']} | "
                    f"{pct(row['score'])} | {pct(row['without'])} | "
                    f"{signed(row['delta'])} | {row['at_k']}/{row['cases']} | "
                    f"{row['pow_k']}/{row['cases']} | "
                    f"{row['fired']}/{row['cases']} |")
                string = readme_string(tag, row)
                if string and not doc.get("partial"):
                    readme.append(f"{plugin}/{skill}: {string}")
            sweep.append("")

    if warnings:
        block = ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
        sweep += block
        trig += block

    out = "\n".join(sweep) + "\n"
    tout = "\n".join(trig) + "\n"
    if args.write:
        (EVALS / "SWEEP.md").write_text(out)
        (EVALS / "TRIGGERING.md").write_text(tout)
        print(f"wrote {EVALS/'SWEEP.md'} and {EVALS/'TRIGGERING.md'}")
    else:
        print(out)
        print(tout)

    if readme:
        print("README strings:")
        for line in readme:
            print(f"  {line}")
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
