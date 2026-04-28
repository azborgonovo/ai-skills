#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$HOME/.claude/skills"

resolve_path() {
  python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$1"
}

if [ -L "$DEST" ]; then
  resolved="$(resolve_path "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

for skill_dir in "$REPO/skills"/*/; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    rm -rf "$target"
  fi

  ln -sfn "$skill_dir" "$target"
  echo "linked $name -> $skill_dir"
done

EXTERNAL_SKILLS_FILE="$SCRIPT_DIR/external-skills.md"

if [ -f "$EXTERNAL_SKILLS_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)+$ ]] || continue

    source="${line%%/*}"
    skill_path="${line#*/}"
    skill_name="$(basename "$skill_path")"
    src="$REPO/external/$source/skills/$skill_path"
    target="$DEST/$skill_name"

    if [ ! -d "$src" ]; then
      echo "warning: external skill '$line' not found at $src" >&2
      continue
    fi

    if [ -e "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    fi

    ln -sfn "$src" "$target"
    echo "linked (external) $skill_name -> $src"
  done < "$EXTERNAL_SKILLS_FILE"
fi
