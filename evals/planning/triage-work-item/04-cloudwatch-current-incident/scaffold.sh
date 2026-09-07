#!/usr/bin/env bash
# The case runs in an empty sandbox working directory, so every fixture the
# prompt names has to be copied in first.
set -euo pipefail

cp -R "$(dirname "$0")/../fixtures/bin" ./bin
cp -R "$(dirname "$0")/../fixtures/exports-app" ./exports-app
cp -R "$(dirname "$0")/../fixtures/tracker" ./tracker
cp -R "$(dirname "$0")/../fixtures/observability" ./observability
