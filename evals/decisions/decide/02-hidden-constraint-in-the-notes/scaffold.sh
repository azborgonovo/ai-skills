#!/usr/bin/env bash
# The case runs in an empty sandbox working directory, so the notes file the
# prompt names has to be copied in. The prompt reads it from the working
# directory root, and not from the suite's fixtures directory.
set -euo pipefail

cp "$(dirname "$0")/../fixtures/platform-notes.md" ./platform-notes.md
