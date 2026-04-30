#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$HOME/.claude/skills"
CONF_FILE="$SCRIPT_DIR/external-repos.conf"
EXTERNAL_SKILLS_FILE="$SCRIPT_DIR/external-skills.md"

# --- Parse external-repos.conf ---

CLONE_DIR=""
declare -a REPO_ENTRIES=()

if [ -f "$CONF_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# || -z "${line// }" ]] && continue
    if [[ "$line" =~ ^CLONE_DIR=(.+)$ ]]; then
      CLONE_DIR="${BASH_REMATCH[1]}"
      CLONE_DIR="${CLONE_DIR/#\~/$HOME}"
    elif [[ "$line" =~ ^https?:// ]]; then
      REPO_ENTRIES+=("$line")
    fi
  done < "$CONF_FILE"
fi

if [ -n "$CLONE_DIR" ] && [ ${#REPO_ENTRIES[@]} -gt 0 ]; then
  mkdir -p "$CLONE_DIR"
  for entry in "${REPO_ENTRIES[@]}"; do
    url="${entry%% *}"
    name="${entry##* }"
    dest="$CLONE_DIR/$name"
    if [ -d "$dest/.git" ]; then
      echo "pulling $name..."
      git -C "$dest" pull
    else
      echo "cloning $name into $dest..."
      git clone "$url" "$dest"
    fi
  done
fi

# --- Symlink personal skills ---

if [ -L "$DEST" ]; then
  resolved="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$DEST")"
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

# --- Symlink selected external skills ---

if [ -f "$EXTERNAL_SKILLS_FILE" ] && [ -n "$CLONE_DIR" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)+$ ]] || continue

    source="${line%%/*}"
    skill_path="${line#*/}"
    skill_name="$(basename "$skill_path")"
    src="$CLONE_DIR/$source/skills/$skill_path"
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
