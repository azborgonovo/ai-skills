#!/usr/bin/env bash
# Builds the orders-service fixture repositories that the review-changes eval
# suite copies into each case working directory. Git history does not survive a
# commit into this repository, so the suite cannot run until this script has run.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
builder="$here/../build_fixture.py"

for variant in defective defective-nospec regression clean; do
    # build_fixture.py refuses a destination that exists, so clear it first.
    rm -rf "${here:?}/$variant"
    python3 "$builder" "$here/$variant" "$variant"
done
