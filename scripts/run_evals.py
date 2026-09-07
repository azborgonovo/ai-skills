#!/usr/bin/env python3
"""Runs the eval suites with `claude plugin eval`.

One eval directory per plugin holds every case, grouped by skill. A tag decides
which arm shape a case wants, and `--ablation` is set per invocation, so each
plugin needs one invocation per tag that it has cases for:

    behavior    an Auto skill, measured against a no-plugin baseline arm
    mechanics   a Manual skill, which the baseline arm cannot reach, so no arm
    triggering  a probe that measures whether the description fires

The result document of each invocation lands in the plugin's results directory
as `<tag>.json`. `scripts/eval_report.py` turns those into the README strings.

Nothing here reimplements the harness. Arm construction, config isolation, the
judge, retries and aggregation all belong to `claude plugin eval`.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVALS = REPO / "evals"

# Tag -> the ablation mode that tag's cases are authored for.
ABLATION = {"behavior": "with-without", "mechanics": "none", "triggering": "none"}

# Tools beyond the free read-only set that a plugin's cases need. The child runs
# in dontAsk mode, so Bash, Write, Edit and WebFetch only reach it through an
# operator grant. Keep each entry as narrow as its cases actually need.
GRANTS: dict[str, list[str]] = {
    "agent-docs": ["Write", "Edit"],
    "bdd": ["Write", "Edit", "Bash"],
    "code-review": ["Write", "Edit", "Bash", "ToolSearch"],  # stub CLIs, git, MCP lookup
    "decisions": ["Write", "Edit"],
    "engineering-practices": ["Write", "Edit"],
    "planning": ["Write", "Edit", "Bash", "ToolSearch"],
}


def plugins() -> list[str]:
    """Every plugin that has a suite under evals/.

    The suites live outside the plugins on purpose: a plugin's whole directory
    is copied into the install cache, and eval cases have no business shipping
    to whoever installs the plugin. Each case names its own plugin in its
    `plugins:` frontmatter, so the plugin still resolves from out here.
    """
    return [d.name for d in sorted(EVALS.iterdir())
            if d.is_dir() and (REPO / "skills" / d.name /
                               ".claude-plugin" / "plugin.json").exists()]


def build_fixtures(plugin: str) -> None:
    """Rebuilds the fixture repositories a suite's cases scaffold from.

    Git metadata does not survive a commit into this repository, so these are
    gitignored and rebuilt on demand. A scaffold copies the result into its
    sandbox working directory, so the build has to happen first.
    """
    for build in sorted((EVALS / plugin).glob("*/fixtures/build.sh")):
        print(f"    building {build.parent.parent.name} fixtures", flush=True)
        r = subprocess.run(["bash", str(build)], cwd=build.parent,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            raise SystemExit(f"fixture build failed: {build}")


def tags_present(evals: Path, tag: str) -> bool:
    """True when at least one case under `evals` carries `tag`.

    An invocation whose tag matches nothing exits 1 with "no cases found", which
    would read as a failure, so the tag is checked before the CLI is called.
    """
    for prompt in evals.rglob("prompt.md"):
        head = prompt.read_text(errors="replace").split("---", 2)
        if len(head) >= 3 and tag in head[1]:
            return True
    return False


def run(plugin: str, tag: str, args: argparse.Namespace) -> int:
    evals = EVALS / plugin
    results = evals / "results"
    results.mkdir(parents=True, exist_ok=True)

    # The target is the repository root, and --eval-dir scopes the run to one
    # plugin's suite so the tool grants stay as narrow as that plugin needs.
    cmd = [
        "claude", "plugin", "eval", ".",
        "--eval-dir", str(evals.relative_to(REPO)),
        "--tag", tag,
        "--ablation", ABLATION[tag],
        "--runs", str(args.runs),
        "--judge-model", args.judge_model,
        "--json", str((results / f"{tag}.json").relative_to(REPO)),
        "--output-dir", str((results / tag).relative_to(REPO)),
        "--no-publish",
        "--max-cost-usd", str(args.max_cost_usd),
    ]
    if args.scaffold:
        cmd.append("--scaffold")
    grants = GRANTS.get(plugin, [])
    if grants:
        cmd += ["--allow-tools", *grants]
    if args.model:
        cmd += ["--model", args.model]

    print(f"\n=== {plugin} :: {tag} ({ABLATION[tag]})", flush=True)
    print("    " + " ".join(cmd), flush=True)
    if args.dry_run:
        return 0

    env = dict(os.environ)
    # Early access. An enabled organization needs nothing; every other client,
    # including CI, needs this. See the plugin-eval availability rules.
    env.setdefault("CLAUDE_CODE_WALNUT_SPIRE", "1")
    return subprocess.run(cmd, cwd=REPO, env=env).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plugin", nargs="*", help="plugin names; default is every one")
    ap.add_argument("--tag", action="append", choices=sorted(ABLATION),
                    help="repeatable; default is every tag")
    ap.add_argument("--runs", type=int, default=1,
                    help="runs per case (default 1; use 3 near a threshold)")
    ap.add_argument("--judge-model", default="sonnet",
                    help="LLM-grader model (default sonnet; the CLI default is haiku)")
    ap.add_argument("--model", help="pin the agent model, as CI should")
    ap.add_argument("--max-cost-usd", type=float, default=25.0)
    ap.add_argument("--no-scaffold", dest="scaffold", action="store_false",
                    help="skip every case's scaffold_script")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the commands and exit")
    ap.add_argument("--no-build", dest="build", action="store_false",
                    help="skip rebuilding fixture repositories")
    args = ap.parse_args()

    wanted = args.tag or list(ABLATION)
    targets = plugins()
    if args.plugin:
        unknown = sorted(set(args.plugin) - set(targets))
        if unknown:
            ap.error(f"no suite under evals/ named: {', '.join(unknown)}")
        targets = [n for n in targets if n in args.plugin]

    worst = 0
    ran = 0
    for plugin in targets:
        if args.build and not args.dry_run:
            build_fixtures(plugin)
        for tag in wanted:
            if not tags_present(EVALS / plugin, tag):
                continue
            ran += 1
            code = run(plugin, tag, args)
            # 2 is a partial run: the cost ceiling was hit, or the credential
            # was rejected. It is worth reporting and not worth masking.
            worst = max(worst, code)
    if not ran:
        print("no cases matched", file=sys.stderr)
        return 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
