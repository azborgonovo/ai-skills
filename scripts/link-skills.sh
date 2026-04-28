#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
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
