#!/usr/bin/env python3
"""Check every SKILL.md under the given paths against the mechanical authoring rules.

Only rules a machine can settle without judgment live here: the frontmatter limits
Anthropic's skill schema states, and the formatting conventions this repo has fixed.
Anything needing a reading — whether a sentence is a no-op, whether a description reads
as third person, whether a British spelling is a quote — stays with the reviewer, because
a checker that reports false positives gets ignored and takes the true findings with it.

Usage:
    check_skills.py                 # this repo: skills/ and .claude/skills/
    check_skills.py <path> [...]    # any directory tree, or a SKILL.md directly

Exits 0 when everything passes, 1 when any check fails. Advisory: it reports, it does
not gate — wire it into a hook only once it has proven quiet on legitimate edits.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DESCRIPTION_MAX = 1024
NAME_MAX = 64
BODY_MAX_LINES = 500
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
KEY_LINE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:")
LIST_OR_HEADING = re.compile(r"^(#|-|\*|\||>|\d+\.)")
DEFAULT_ROOTS = ("skills", ".claude/skills")


def split_frontmatter(text: str) -> tuple[list[str], list[str]] | None:
    """Return (frontmatter lines, body lines), or None when the file has no frontmatter."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    return lines[1:end], lines[end + 1 :]


def folded_value(frontmatter: list[str], key: str) -> str | None:
    """Read one frontmatter value, joining a `>` folded block the way YAML would."""
    collecting = False
    parts: list[str] = []
    for line in frontmatter:
        if not collecting:
            match = re.match(rf"{key}:\s*(.*)$", line)
            if not match:
                continue
            inline = match.group(1).strip()
            if inline not in (">", ">-", "|", "|-"):
                return inline.strip("\"'")
            collecting = True
        else:
            if KEY_LINE.match(line):
                break
            parts.append(line.strip())
    if not collecting:
        return None
    return " ".join(p for p in parts if p)


def wrapped_paragraph_lines(body: list[str], offset: int) -> list[int]:
    """Line numbers where a prose paragraph continues onto the next line."""
    hits: list[int] = []
    in_code = False
    previous: str | None = None
    previous_line = 0
    for index, line in enumerate(body, start=offset):
        if line.strip().startswith("```"):
            in_code = not in_code
            previous = None
            continue
        if in_code:
            continue
        stripped = line.strip()
        is_prose = bool(stripped) and not LIST_OR_HEADING.match(stripped)
        if is_prose and previous and not previous.rstrip().endswith((".", ":", "!", "?", '"')):
            hits.append(previous_line)
        previous, previous_line = (line, index) if is_prose else (None, 0)
    return hits


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    split = split_frontmatter(text)
    if split is None:
        return ["missing YAML frontmatter delimited by `---`"]
    frontmatter, body = split
    problems: list[str] = []

    name = folded_value(frontmatter, "name")
    if not name:
        problems.append("frontmatter has no `name`")
    else:
        if len(name) > NAME_MAX:
            problems.append(f"`name` is {len(name)} chars, over the {NAME_MAX} limit")
        if not NAME_PATTERN.match(name):
            problems.append(f"`name` {name!r} must be lowercase letters, numbers, and hyphens only")
        if name != path.parent.name:
            problems.append(f"`name` {name!r} does not match its directory {path.parent.name!r}")

    description = folded_value(frontmatter, "description")
    if not description:
        problems.append("frontmatter has no `description`")
    elif len(description) > DESCRIPTION_MAX:
        problems.append(f"`description` is {len(description)} chars, over the {DESCRIPTION_MAX} limit")
    elif "TRIGGER" in description:
        problems.append("`description` uses a `TRIGGER` marker; this repo phrases triggers as `Use when …`")

    if text.count("\n---\n") + text.startswith("---\n") != 2:
        separators = len([line for line in text.split("\n") if line.strip() == "---"])
        problems.append(f"{separators} `---` lines; only the two frontmatter delimiters belong in a SKILL.md")

    if len(body) > BODY_MAX_LINES:
        problems.append(f"body is {len(body)} lines, over the {BODY_MAX_LINES} limit")

    wrapped = wrapped_paragraph_lines(body, len(frontmatter) + 3)
    if wrapped:
        shown = ", ".join(str(line) for line in wrapped[:5])
        problems.append(f"hard-wrapped prose at line(s) {shown} — write one line per paragraph")

    return problems


def collect(targets: list[str]) -> list[Path]:
    found: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_file():
            found.append(path)
        elif path.is_dir():
            found.extend(sorted(path.rglob("SKILL.md")))
    return found


def main() -> int:
    targets = sys.argv[1:] or [root for root in DEFAULT_ROOTS if Path(root).is_dir()]
    if not targets:
        print("no SKILL.md files found — pass a path to check a tree elsewhere")
        return 1
    files = collect(targets)
    if not files:
        print(f"no SKILL.md files under: {', '.join(targets)}")
        return 1

    failed = 0
    for path in files:
        problems = check(path)
        if problems:
            failed += 1
            print(f"\n{path}")
            for problem in problems:
                print(f"  - {problem}")

    print(f"\n{len(files)} skill(s) checked, {failed} with problems")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
