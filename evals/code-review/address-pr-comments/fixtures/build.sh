#!/usr/bin/env bash
# Builds the orders-service fixture: a bare origin plus a clone that sits on the
# source branch of the pull request. Everything is local, so no network is used.
set -euo pipefail

DEST="${1:-eval-workspace}"
CLONE="$DEST/orders-service"
ORIGIN="$DEST/origin/orders-service.git"

if [ -d "$CLONE" ]; then
  echo "clone already built at $CLONE"
  exit 0
fi

mkdir -p "$DEST/origin"
git init --quiet --bare -b main "$ORIGIN"
ORIGIN_ABS="$(cd "$ORIGIN" && pwd)"

git init --quiet -b main "$CLONE"
git -C "$CLONE" config user.name "Robin Fixture"
git -C "$CLONE" config user.email "robin@example.invalid"
git -C "$CLONE" config commit.gpgsign false

mkdir -p "$CLONE/src" "$CLONE/tests"

cat > "$CLONE/README.md" <<'MD'
# orders-service

Checkout pricing for the orders API.

Run the suite from the repo root:

    python3 -m unittest discover -s tests -t .
MD

cat > "$CLONE/.gitignore" <<'MD'
__pycache__/
MD

cat > "$CLONE/CODING_STANDARDS.md" <<'MD'
# Coding standards

## Money

Every monetary value is an integer number of cents. A function that returns money
returns an `int`. A float never holds money.

## Validation

`src/api.py` maps the HTTP payload onto the domain call. It validates nothing of
its own. Each rule lives in the module that owns the value.

## Tests

Run `python3 -m unittest discover -s tests -t .` from the repo root. Every fix
lands with a test that fails without it.
MD

: > "$CLONE/src/__init__.py"
: > "$CLONE/tests/__init__.py"

cat > "$CLONE/src/api.py" <<'PY'
MAX_ITEMS = 50


def checkout(payload):
    if len(payload["items"]) > MAX_ITEMS:
        raise ValueError("too many items")
    return {"total_cents": sum(item["price_cents"] for item in payload["items"])}
PY

cat > "$CLONE/tests/test_api.py" <<'PY'
import unittest

from src.api import checkout


class CheckoutTests(unittest.TestCase):
    def test_sums_the_line_items(self):
        payload = {"items": [{"price_cents": 1200}, {"price_cents": 800}]}
        self.assertEqual(checkout(payload)["total_cents"], 2000)
PY

git -C "$CLONE" add -A
git -C "$CLONE" commit --quiet -m "chore: added the checkout skeleton"
git -C "$CLONE" remote add origin "$ORIGIN_ABS"
git -C "$CLONE" push --quiet -u origin main

git -C "$CLONE" checkout --quiet -b feat/discount-codes

cat > "$CLONE/src/discount.py" <<'PY'
"""Percentage discount codes."""

MAX_PERCENT = 60


def apply_discount(total_cents, percent):
    if percent < 0 or percent > MAX_PERCENT:
        raise ValueError("percent out of range")
    return total_cents - (total_cents * percent / 100)
PY

cat > "$CLONE/src/api.py" <<'PY'
from src.discount import apply_discount

MAX_ITEMS = 50
MAX_PERCENT = 60


def discount_limits():
    return {"max_percent": MAX_PERCENT}


def checkout(payload):
    if len(payload["items"]) > MAX_ITEMS:
        raise ValueError("too many items")
    total_cents = sum(item["price_cents"] for item in payload["items"])
    return {"total_cents": apply_discount(total_cents, payload.get("percent", 0))}
PY

cat > "$CLONE/tests/test_discount.py" <<'PY'
import unittest

from src.discount import apply_discount


class ApplyDiscountTests(unittest.TestCase):
    def test_applies_the_percentage(self):
        self.assertEqual(apply_discount(2000, 10), 1800)

    def test_rejects_a_negative_percent(self):
        with self.assertRaises(ValueError):
            apply_discount(2000, -5)

    def test_rejects_a_percent_over_the_cap(self):
        with self.assertRaises(ValueError):
            apply_discount(2000, 90)
PY

git -C "$CLONE" add -A
git -C "$CLONE" commit --quiet -m "feat: added percentage discount codes at checkout"

cat > "$CLONE/src/api.py" <<'PY'
from src.discount import MAX_PERCENT, apply_discount

MAX_ITEMS = 50


def discount_limits():
    return {"max_percent": MAX_PERCENT}


def checkout(payload):
    if len(payload["items"]) > MAX_ITEMS:
        raise ValueError("too many items")
    total_cents = sum(item["price_cents"] for item in payload["items"])
    return {"total_cents": apply_discount(total_cents, payload.get("percent", 0))}
PY

git -C "$CLONE" add -A
git -C "$CLONE" commit --quiet -m "refactor: read the cap from the discount module so one value governs it"
git -C "$CLONE" push --quiet -u origin feat/discount-codes

echo "clone:  $(cd "$CLONE" && pwd)"
echo "origin: $ORIGIN_ABS"
echo "branch: feat/discount-codes"
