#!/usr/bin/env bash
# The case runs in an empty sandbox working directory, so every fixture the
# prompt names has to be copied in first.
set -euo pipefail

cp -R "$(dirname "$0")/../fixtures/." ./.
cp -R "$(dirname "$0")/../fixtures/checkout.feature" ./checkout.feature
cp -R "$(dirname "$0")/../fixtures/promotions.feature" ./promotions.feature
cp -R "$(dirname "$0")/../fixtures/sign-in.feature" ./sign-in.feature
cp -R "$(dirname "$0")/../fixtures/editor-content.feature" ./editor-content.feature
