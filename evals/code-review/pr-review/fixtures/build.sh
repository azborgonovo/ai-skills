#!/usr/bin/env bash
# Builds the offline fixtures that the pr-review eval suite copies into each case
# working directory. Git history does not survive a commit into this repository, so the
# suite cannot run until this script has run.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$here/../build_fixture.py" "$@"
