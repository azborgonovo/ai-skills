#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$HOME/.claude/skills"
CONF_FILE="$SCRIPT_DIR/external-skills.conf"

# Derives a local folder name from a repo URL as <owner>-<repo>
# e.g. https://github.com/mattpocock/skills -> mattpocock-skills
derive_local_name() {
  local path="${1#*://*/}"   # strip https://hostname/
  local owner="${path%%/*}"
  local repo="${path##*/}"
  echo "${owner}-${repo}"
}

# --- Parse external-skills.conf ---

CLONE_DIR=""
declare -a SKILL_ENTRIES=()

if [ -f "$CONF_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# || -z "${line// }" ]] && continue
    if [[ "$line" =~ ^CLONE_DIR=(.+)$ ]]; then
      CLONE_DIR="${BASH_REMATCH[1]}"
      CLONE_DIR="${CLONE_DIR/#\~/$HOME}"
    elif [[ "$line" =~ ^https?:// ]]; then
      SKILL_ENTRIES+=("$line")
    fi
  done < "$CONF_FILE"
fi

# --- Clone or pull each unique external repository ---

if [ -n "$CLONE_DIR" ] && [ ${#SKILL_ENTRIES[@]} -gt 0 ]; then
  mkdir -p "$CLONE_DIR"
  declare -A SEEN_REPOS=()
  for entry in "${SKILL_ENTRIES[@]}"; do
    url="${entry%% *}"
    [ -n "${SEEN_REPOS[$url]+x}" ] && continue
    SEEN_REPOS[$url]=1
    local_name="$(derive_local_name "$url")"
    dest="$CLONE_DIR/$local_name"
    if [ -d "$dest/.git" ]; then
      echo "pulling $local_name..."
      git -C "$dest" pull
    else
      echo "cloning $local_name into $dest..."
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
  if [ -e "$target" ] && [ ! -L "$target" ]; then rm -rf "$target"; fi
  ln -sfn "$skill_dir" "$target"
  echo "linked $name -> $skill_dir"
done

# --- Symlink selected external skills ---

if [ -n "$CLONE_DIR" ]; then
  for entry in "${SKILL_ENTRIES[@]}"; do
    url="${entry%% *}"
    skill_path="${entry#* }"
    skill_name="$(basename "$skill_path")"
    local_name="$(derive_local_name "$url")"
    src="$CLONE_DIR/$local_name/skills/$skill_path"
    target="$DEST/$skill_name"

    if [ ! -d "$src" ]; then
      echo "warning: external skill '$skill_path' not found at $src" >&2
      continue
    fi

    if [ -e "$target" ] && [ ! -L "$target" ]; then rm -rf "$target"; fi
    ln -sfn "$src" "$target"
    echo "linked (external) $skill_name -> $src"
  done
fi
