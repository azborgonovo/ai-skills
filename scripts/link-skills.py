#!/usr/bin/env python3
"""Link this repo's skills into ~/.claude/skills (cross-platform).

By default only local skills (this repo's own, under skills/) are linked. Pass
--include-external (--ie) to also clone/update and link the third-party skills
listed in personal/external-skills.conf.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO       = SCRIPT_DIR.parent
DEST       = Path.home() / ".claude" / "skills"
CONF_FILE  = SCRIPT_DIR / "personal" / "external-skills.conf"

INCLUDE_EXTERNAL = any(arg in ("--include-external", "--ie") for arg in sys.argv[1:])


def step(msg):  print(f"\n==> {msg}")
def item(msg):  print(f"    {msg}")
def warn(msg):  print(f"    [warn] {msg}", file=sys.stderr)
def abort(msg): print(f"\n[error] {msg}", file=sys.stderr); sys.exit(1)


def points_to(target: Path, src: Path) -> bool:
    """True if target is a symlink already resolving to src (ignoring path-casing noise)."""
    if not target.is_symlink():
        return False
    try:
        return os.path.samefile(target, src)
    except OSError:
        return False  # dangling link, or src missing


def derive_local_name(url: str) -> str:
    """Return <owner>-<repo> from a repo URL."""
    path  = re.sub(r"^[^:]+://[^/]+/", "", url).rstrip("/")
    parts = path.split("/")
    return f"{parts[0]}-{parts[-1]}"


def is_junction(path: Path) -> bool:
    # os.path.isjunction lands in 3.12; Windows junctions aren't reported by is_symlink().
    return getattr(os.path, "isjunction", lambda _p: False)(path)


def make_symlink(src: Path, target: Path) -> str:
    """Link target -> src, returning 'up-to-date' if it already pointed there, else 'linked'."""
    if points_to(target, src):
        return "up-to-date"

    if target.is_symlink() or is_junction(target):
        try:
            target.unlink()
        except OSError:
            os.rmdir(target)  # directory symlinks/junctions unlink as dirs
    elif target.exists():
        shutil.rmtree(target)

    if sys.platform == "win32" and src.is_dir():
        # Directory junctions need no elevated privileges, unlike directory symlinks.
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(src)],
            check=True, capture_output=True,
        )
    else:
        target.symlink_to(src, target_is_directory=src.is_dir())
    return "linked"


# --- Parse external-skills.conf ---

clone_dir: Path | None = None
skill_entries: list[str] = []

if CONF_FILE.exists():
    for line in CONF_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^CLONE_DIR=(.+)$", line)
        if m:
            clone_dir = Path(m.group(1).replace("~", str(Path.home()), 1))
        elif re.match(r"^https?://", line):
            skill_entries.append(line)

# --- Clone or pull each unique external repository (only with --include-external) ---

if INCLUDE_EXTERNAL and clone_dir and skill_entries:
    step("Updating external skill repos")
    clone_dir.mkdir(parents=True, exist_ok=True)

    unique_urls = sorted({entry.split()[0] for entry in skill_entries})
    for url in unique_urls:
        local_name  = derive_local_name(url)
        clone_dest  = clone_dir / local_name
        if (clone_dest / ".git").is_dir():
            result = subprocess.run(
                ["git", "-C", str(clone_dest), "pull"],
                capture_output=True, text=True,
            )
            output = result.stdout + result.stderr
            status = "up-to-date" if "Already up to date" in output else "updated"
            item(f"[{status:<10}] {local_name}")
        else:
            subprocess.run(["git", "clone", url, str(clone_dest)], check=True)
            item(f"[{'cloned':<10}] {local_name}")

# --- Guard: DEST must not be a symlink into this repo ---

if DEST.is_symlink():
    resolved = DEST.resolve()
    try:
        resolved.relative_to(REPO)
        abort(f"{DEST} is a symlink into this repo ({resolved}). Remove it and re-run.")
    except ValueError:
        pass

DEST.mkdir(parents=True, exist_ok=True)

step(f"Linking skills to {DEST}")

managed: set[str] = set()
linked_count = up_to_date_count = 0


def report(name: str, status: str, note: str = "") -> None:
    """Print a per-skill line and tally the run-wide counts."""
    global linked_count, up_to_date_count
    if status == "linked":
        linked_count += 1
    else:
        up_to_date_count += 1
    tail = f"  ({note})" if note else ""
    item(f"[{status:<10}] {name}{tail}")


# Local skills all live under skills/: published ones nested inside a plugin
# folder (skills/<plugin>/<skill>), draft ones under skills/drafts/<skill>. Every
# skill is the directory holding a SKILL.md; -workspace scratch dirs are skipped.
def local_skill_dirs() -> list[Path]:
    dirs = (
        d.parent
        for d in (REPO / "skills").rglob("SKILL.md")
        if not any(part.endswith("-workspace") for part in d.parts)
    )
    return sorted(set(dirs), key=lambda d: d.name)


for skill_dir in local_skill_dirs():
    managed.add(skill_dir.name)
    report(skill_dir.name, make_symlink(skill_dir, DEST / skill_dir.name))

# External skills (only with --include-external)
if INCLUDE_EXTERNAL and clone_dir:
    for entry in skill_entries:
        parts      = entry.split(maxsplit=1)
        url        = parts[0]
        skill_path = parts[1].strip() if len(parts) > 1 else ""
        skill_name = Path(skill_path).name
        local_name = derive_local_name(url)
        src        = clone_dir / local_name / "skills" / skill_path
        target     = DEST / skill_name

        if not src.is_dir():
            warn(f"external skill '{skill_path}' not found at {src}")
            continue

        managed.add(skill_name)
        report(skill_name, make_symlink(src, target), f"external: {local_name}")
elif skill_entries:
    item(f"[{'skipped':<10}] {len(skill_entries)} external skill(s)  (re-run with --include-external to include)")

# --- Report skills present in DEST that this run did not manage ---

def describe_other(path: Path) -> str:
    """Classify an unmanaged DEST entry for the listing."""
    if path.is_symlink():
        dest = os.readlink(path)
        kind = "external symlink" if path.exists() else "broken symlink"
        return f"{kind} -> {dest}"
    return "directory"


others = sorted(
    p for p in DEST.iterdir()
    if p.name not in managed and (p.is_dir() or p.is_symlink()) and not p.name.startswith(".")
)
broken_count = 0
if others:
    step("Other skills present (not managed by this script)")
    for path in others:
        desc = describe_other(path)
        if desc.startswith("broken"):
            broken_count += 1
        item(f"{path.name}  ({desc})")

# --- Summary ---

parts = [f"{linked_count} linked", f"{up_to_date_count} up-to-date"]
if others:
    other_note = f"{len(others)} other"
    if broken_count:
        other_note += f", {broken_count} broken"
    parts.append(other_note)
step("Summary")
item(" · ".join(parts))
print()
