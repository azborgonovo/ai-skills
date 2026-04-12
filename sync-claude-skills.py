#!/usr/bin/env python3
import shutil
from pathlib import Path

repo = Path(__file__).parent / "skills"
dest = Path.home() / ".claude" / "skills"
dest.mkdir(parents=True, exist_ok=True)

for skill in repo.iterdir():
    if skill.is_dir():
        shutil.copytree(skill, dest / skill.name, dirs_exist_ok=True)
        print(f"Synced: {skill.name}")

print("Done.")