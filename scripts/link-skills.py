#!/usr/bin/env python3
"""Cross-platform replacement for link-skills.sh."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO       = SCRIPT_DIR.parent
DEST       = Path.home() / ".claude" / "skills"
CONF_FILE  = SCRIPT_DIR / "external-skills.conf"


def step(msg):  print(f"\n==> {msg}")
def item(msg):  print(f"    {msg}")
def warn(msg):  print(f"    [warn] {msg}", file=sys.stderr)
def abort(msg): print(f"\n[error] {msg}", file=sys.stderr); sys.exit(1)


def derive_local_name(url: str) -> str:
    """Return <owner>-<repo> from a repo URL."""
    path  = re.sub(r"^[^:]+://[^/]+/", "", url).rstrip("/")
    parts = path.split("/")
    return f"{parts[0]}-{parts[-1]}"


def is_junction(path: Path) -> bool:
    # os.path.isjunction lands in 3.12; Windows junctions aren't reported by is_symlink().
    return getattr(os.path, "isjunction", lambda _p: False)(path)


def make_symlink(src: Path, target: Path) -> None:
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

# --- Clone or pull each unique external repository ---

if clone_dir and skill_entries:
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
            suffix = "(already up to date)" if "Already up to date" in output else "(updated)"
            item(f"{local_name}  {suffix}")
        else:
            item(f"{local_name}  (cloning...)")
            subprocess.run(["git", "clone", url, str(clone_dest)], check=True)

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

# Personal skills
for skill_dir in sorted((REPO / "skills").iterdir()):
    if not skill_dir.is_dir():
        continue
    make_symlink(skill_dir, DEST / skill_dir.name)
    item(skill_dir.name)

# External skills
if clone_dir:
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

        make_symlink(src, target)
        item(f"{skill_name}  (external: {local_name})")

print()
