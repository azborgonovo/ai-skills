#!/usr/bin/env bash
# The case runs in an empty sandbox working directory. The prompt sends the new
# record to docs/decisions/, so the two neighbouring records have to be there.
set -euo pipefail

cp -R "$(dirname "$0")/../fixtures/docs" ./docs
