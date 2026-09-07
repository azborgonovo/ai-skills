#!/usr/bin/env bash
# Builds the git checkouts that the triage-work-item eval suite copies into a
# case working directory. Git history does not survive a commit into this
# repository, so run this script once before the suite runs.
#
# Everything is local. The script clones from a bare repository on disk, so it
# needs no network and it contacts no host.
#
#   exports-repo/frontend, exports-repo/backend  two checkouts, both current
#   stale-repo/app                               a checkout two commits behind
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$here/exports-app"
git_c=(git -c user.name="Fixture Bot" -c user.email="fixture@example.com" -c commit.gpgsign=false -c init.defaultBranch=main)

commit_all() {
    "${git_c[@]}" -C "$1" add -A
    "${git_c[@]}" -C "$1" commit -q -m "$2"
}

# --- two current checkouts, one per deployable ------------------------------
rm -rf "${here:?}/exports-repo"
mkdir -p "$here/exports-repo"
for part in frontend backend; do
    work="$here/exports-repo/$part"
    mkdir -p "$work"
    cp -R "$src/$part/." "$work/"
    cp "$src/README.md" "$work/README.md"
    "${git_c[@]}" init -q "$work"
    commit_all "$work" "feat: order export $part"
    "${git_c[@]}" init -q --bare "$here/exports-repo/$part.git"
    "${git_c[@]}" -C "$work" remote add origin "../$part.git"
    "${git_c[@]}" -C "$work" push -q origin main
    "${git_c[@]}" -C "$work" branch -q --set-upstream-to=origin/main main
done

# --- one checkout that is two commits behind its remote ---------------------
# The missing commits carry the export code, so an investigation that skips the
# refresh reports that this repository holds no export code at all.
rm -rf "${here:?}/stale-repo"
mkdir -p "$here/stale-repo"
seed="$here/stale-repo/.seed"
mkdir -p "$seed/backend"
cp "$src/README.md" "$seed/README.md"
cp "$src/backend/reconcile_job.py" "$seed/backend/reconcile_job.py"
"${git_c[@]}" init -q "$seed"
commit_all "$seed" "chore: nightly reconciliation job"
behind_at="$("${git_c[@]}" -C "$seed" rev-parse HEAD)"

mkdir -p "$seed/frontend"
cp "$src/frontend/export-button.js" "$seed/frontend/export-button.js"
commit_all "$seed" "feat: export button on the orders screen"
cp "$src/backend/export_service.py" "$seed/backend/export_service.py"
commit_all "$seed" "feat: order export endpoint"

"${git_c[@]}" init -q --bare "$here/stale-repo/app.git"
"${git_c[@]}" -C "$seed" remote add origin "$here/stale-repo/app.git"
"${git_c[@]}" -C "$seed" push -q origin main
rm -rf "$seed"

# --no-hardlinks: a hard-linked git object under the eval directory makes
# `claude plugin eval` refuse the run, because a case definition must not be
# reachable by a second name.
"${git_c[@]}" clone -q --no-hardlinks "$here/stale-repo/app.git" "$here/stale-repo/app"
"${git_c[@]}" -C "$here/stale-repo/app" remote set-url origin "../app.git"
"${git_c[@]}" -C "$here/stale-repo/app" reset -q --hard "$behind_at"

echo "built: $here/exports-repo (current), $here/stale-repo/app (two commits behind)"
