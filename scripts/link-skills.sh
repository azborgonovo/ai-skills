#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$HOME/.claude/skills"
CONF_FILE="$SCRIPT_DIR/external-skills.conf"

step()  { echo; echo "==> $*"; }
item()  { echo "    $*"; }
warn()  { echo "    [warn] $*" >&2; }
error() { echo; echo "[error] $*" >&2; exit 1; }

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
  step "Updating external skill repos"
  mkdir -p "$CLONE_DIR"
  while IFS= read -r url; do
    local_name="$(derive_local_name "$url")"
    dest="$CLONE_DIR/$local_name"
    if [ -d "$dest/.git" ]; then
      output="$(git -C "$dest" pull 2>&1)"
      if echo "$output" | grep -q "Already up to date"; then
        item "$local_name  (already up to date)"
      else
        item "$local_name  (updated)"
      fi
    else
      item "$local_name  (cloning...)"
      git clone "$url" "$dest"
    fi
  done < <(printf '%s\n' "${SKILL_ENTRIES[@]}" | awk '{print $1}' | sort -u)
fi

# --- Symlink personal and external skills ---

if [ -L "$DEST" ]; then
  resolved="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      error "$DEST is a symlink into this repo ($resolved). Remove it and re-run."
      ;;
  esac
fi

mkdir -p "$DEST"

step "Linking skills to $DEST"

for skill_dir in "$REPO/skills"/*/; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  target="$DEST/$name"
  if [ -e "$target" ] && [ ! -L "$target" ]; then rm -rf "$target"; fi
  ln -sfn "$skill_dir" "$target"
  item "$name"
done

if [ -n "$CLONE_DIR" ]; then
  for entry in "${SKILL_ENTRIES[@]}"; do
    url="${entry%% *}"
    skill_path="${entry#* }"
    skill_name="$(basename "$skill_path")"
    local_name="$(derive_local_name "$url")"
    src="$CLONE_DIR/$local_name/skills/$skill_path"
    target="$DEST/$skill_name"

    if [ ! -d "$src" ]; then
      warn "external skill '$skill_path' not found at $src"
      continue
    fi

    if [ -e "$target" ] && [ ! -L "$target" ]; then rm -rf "$target"; fi
    ln -sfn "$src" "$target"
    item "$skill_name  (external: $local_name)"
  done
fi

echo
