#!/usr/bin/env bash
# Seeds what the probes assume the working directory already holds.
set -euo pipefail

bash "$(dirname "$0")/../probe_fixture.sh"
