#!/usr/bin/env bash
# The case runs in an empty sandbox working directory, so every fixture the
# prompt names has to be copied in first.
set -euo pipefail

cp -R "$(dirname "$0")/../fixtures/docs-change.diff" ./docs-change.diff
cp -R "$(dirname "$0")/../fixtures/retry_config.py" ./retry_config.py
