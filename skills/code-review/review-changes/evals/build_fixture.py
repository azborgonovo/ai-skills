#!/usr/bin/env python3
"""Build the orders-service fixture repo used to eval the review-changes skill.

Three variants, all sharing one base commit on `main`:

  defective        feature branch with known planted defects across all 5 pyramid
                   layers, plus specs/ORD-104 so conformance can be checked
  defective-nospec same feature branch, but the repo never had a spec file and the
                   commit messages carry no ticket reference
  clean            the same feature implemented correctly: all ACs met, tested,
                   documented, standards followed

Usage: build_fixture.py <dest-dir> <variant>
"""

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- base commit

STANDARDS = """\
# Coding standards

These are the conventions every change to this service is expected to follow.
Reviewers treat a breach as a blocking problem, not a preference.

## Money

All monetary values are integers in minor units (cents). Every field, parameter,
and variable holding one ends in `_cents`. Floats are never used for money.

## Database access

All SQL goes through `db.query(sql, params)` with bound parameters. String
interpolation or f-strings inside a SQL statement is prohibited.

## Public functions

Every function exported from a module under `src/orders/` carries full type hints
on its parameters and its return value.

## Errors

Invalid input is rejected by raising `RefundError` with a machine-readable
`code`. Returning `None` to signal failure is not allowed.

## Tests

Every acceptance criterion in a spec gets at least one test. Tests are never
committed skipped or disabled.
"""

SPEC = """\
# ORD-104 — Partial refunds

## Context

Support agents can currently only refund an order in full. When a customer is
unhappy with one item out of several, the agent has to refund everything and
re-charge, which loses the original payment authorization.

## Acceptance criteria

- **AC-1** A refund request may specify an amount lower than the order total,
  creating a partial refund.
- **AC-2** The sum of all refunds recorded against an order must never exceed the
  order total. A request that would exceed it is rejected with the code
  `refund_exceeds_total`.
- **AC-3** A partial refund records the agent's free-text reason against the
  refund row.
- **AC-4** A refund is rejected with the code `refund_window_expired` when the
  order was placed more than 90 days ago.
- **AC-5** Existing full-refund behavior is unchanged for callers that do not
  pass an amount.

## Out of scope

Notifying customers, support agents, or internal chat channels when a refund is
issued. Multi-currency orders.
"""

README_BASE = """\
# orders-service

Order and refund management for the storefront.

## HTTP API

### `POST /orders/{order_id}/refund`

Refunds an order in full.

Response:

```json
{
  "order_id": "ord_123",
  "amount_cents": 4999,
  "reason": null
}
```

`amount_cents` is an integer in minor units. Clients depend on these field
names; see `CODING_STANDARDS.md`.

## Development

The virtualenv in `.venv` already has the test dependencies installed. Run the
suite with:

    .venv/bin/python -m pytest

There is no CI pipeline for this service yet, so the local suite is the only
signal.
"""

DB_PY = '''\
"""Tiny in-memory stand-in for the production database.

Only the query shapes the refund flow needs are recognized; anything else
returns an empty result. Tests seed rows with `seed_order` and `reset`.
"""

_ORDERS: dict[str, dict] = {}
_REFUNDS: list[dict] = []


def reset() -> None:
    """Drop all seeded state. Called between tests."""
    _ORDERS.clear()
    _REFUNDS.clear()


def seed_order(order: dict) -> None:
    """Insert an order row directly, bypassing the API."""
    _ORDERS[order["id"]] = dict(order)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute SQL with bound parameters and return the resulting rows."""
    normalized = " ".join(sql.split())
    if normalized.startswith("SELECT * FROM orders"):
        order = _ORDERS.get(params[0])
        return [dict(order)] if order else []
    if normalized.startswith("SELECT * FROM refunds"):
        return [dict(r) for r in _REFUNDS if r["order_id"] == params[0]]
    if normalized.startswith("INSERT INTO refunds"):
        _REFUNDS.append(
            {"order_id": params[0], "amount_cents": params[1], "reason": params[2]}
        )
        return []
    return []
'''

REFUNDS_BASE = '''\
"""Refund processing."""

from . import db


class RefundError(Exception):
    """A refund was rejected. `code` is stable and safe to match on."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def refund_order(order_id: str) -> dict:
    """Refund an order in full."""
    order = _load_order(order_id)
    if _refunded_total_cents(order_id) > 0:
        raise RefundError("already_refunded", "order has already been refunded")
    return _record_refund(order_id, order["total_cents"], None)


def _load_order(order_id: str) -> dict:
    rows = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not rows:
        raise RefundError("order_not_found", "no such order")
    return rows[0]


def _refunded_total_cents(order_id: str) -> int:
    rows = db.query("SELECT * FROM refunds WHERE order_id = ?", (order_id,))
    return sum(row["amount_cents"] for row in rows)


def _record_refund(order_id: str, amount_cents: int, reason: str | None) -> dict:
    db.query(
        "INSERT INTO refunds (order_id, amount_cents, reason) VALUES (?, ?, ?)",
        (order_id, amount_cents, reason),
    )
    return {"order_id": order_id, "amount_cents": amount_cents, "reason": reason}
'''

API_BASE = '''\
"""HTTP-facing serialization. Field names here are the public contract."""

from . import refunds


def serialize_refund(refund: dict) -> dict:
    """Render a refund as the JSON body clients receive."""
    return {
        "order_id": refund["order_id"],
        "amount_cents": refund["amount_cents"],
        "reason": refund["reason"],
    }


def post_refund(order_id: str) -> dict:
    """Handle `POST /orders/{order_id}/refund`."""
    return serialize_refund(refunds.refund_order(order_id))
'''

TESTS_BASE = '''\
import pytest

from src.orders import db, refunds


@pytest.fixture(autouse=True)
def clean_db():
    db.reset()
    yield
    db.reset()


def test_full_refund_records_the_order_total():
    db.seed_order({"id": "ord_1", "total_cents": 4999, "placed_days_ago": 3})
    result = refunds.refund_order("ord_1")
    assert result["amount_cents"] == 4999


def test_refunding_twice_is_rejected():
    db.seed_order({"id": "ord_1", "total_cents": 4999, "placed_days_ago": 3})
    refunds.refund_order("ord_1")
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund_order("ord_1")
    assert excinfo.value.code == "already_refunded"


def test_unknown_order_is_rejected():
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund_order("nope")
    assert excinfo.value.code == "order_not_found"
'''

# ------------------------------------------------------- defective feature diff

REFUNDS_DEFECTIVE = '''\
"""Refund processing."""

import json
import os
import urllib.request

from . import db


class RefundError(Exception):
    """A refund was rejected. `code` is stable and safe to match on."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def refund(order_id: str, amount_cents: int = None, reason=None):
    """Refund an order, in full or in part."""
    order = _load_order(order_id)
    if amount_cents is None:
        amount_cents = order["total_cents"]
    if amount_cents > order["total_cents"]:
        raise RefundError("refund_exceeds_total", "refund exceeds order total")
    _log_refund_audit(order_id, reason)
    _notify_slack(order_id, amount_cents)
    return _record_refund(order_id, amount_cents, reason)


def refund_order(order_id: str) -> dict:
    """Refund an order in full."""
    order = _load_order(order_id)
    if _refunded_total_cents(order_id) > 0:
        raise RefundError("already_refunded", "order has already been refunded")
    return _record_refund(order_id, order["total_cents"], None)


def _log_refund_audit(order_id, reason):
    db.query(
        f"INSERT INTO refund_audit (order_id, reason) VALUES ('{order_id}', '{reason}')"
    )


def _notify_slack(order_id, amount_cents):
    webhook = os.environ.get("SLACK_REFUND_WEBHOOK")
    if not webhook:
        return
    payload = json.dumps({"text": f"Refunded {amount_cents} on {order_id}"})
    urllib.request.urlopen(webhook, payload.encode())


def _load_order(order_id: str) -> dict:
    rows = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not rows:
        raise RefundError("order_not_found", "no such order")
    return rows[0]


def _refunded_total_cents(order_id: str) -> int:
    rows = db.query("SELECT * FROM refunds WHERE order_id = ?", (order_id,))
    return sum(row["amount_cents"] for row in rows)


def _record_refund(order_id: str, amount_cents: int, reason: str | None) -> dict:
    db.query(
        "INSERT INTO refunds (order_id, amount_cents, reason) VALUES (?, ?, ?)",
        (order_id, amount_cents, reason),
    )
    return {"order_id": order_id, "amount_cents": amount_cents, "reason": reason}
'''

API_DEFECTIVE = '''\
"""HTTP-facing serialization. Field names here are the public contract."""

from . import refunds


def serialize_refund(refund: dict) -> dict:
    """Render a refund as the JSON body clients receive."""
    return {
        "order_id": refund["order_id"],
        "amount": refund["amount_cents"],
        "reason": refund["reason"],
    }


def post_refund(order_id, amount=None, reason=None):
    """Handle `POST /orders/{order_id}/refund`."""
    return serialize_refund(refunds.refund(order_id, amount, reason))
'''

TESTS_DEFECTIVE = TESTS_BASE + '''

def test_partial_refund_records_the_requested_amount():
    db.seed_order({"id": "ord_2", "total_cents": 4999, "placed_days_ago": 3})
    result = refunds.refund("ord_2", 1500, "one item damaged")
    assert result["amount_cents"] == 1500
    assert result["reason"] == "one item damaged"


@pytest.mark.skip(reason="flaky on CI, will fix in a follow-up")
def test_refunds_cannot_exceed_the_order_total():
    db.seed_order({"id": "ord_3", "total_cents": 4999, "placed_days_ago": 3})
    refunds.refund("ord_3", 4000, "partial")
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_3", 2000, "too much")
    assert excinfo.value.code == "refund_exceeds_total"
'''

# ------------------------------------------------------- regression feature diff
#
# This variant looks clean on a read-through: every acceptance criterion is
# implemented, tested and documented, SQL is parameterized, naming and type hints
# follow the standards. The defect is one level down — `refund_order` keeps the
# `already_refunded` guard, but `post_refund` was rerouted to `refund`, which does
# not have it. A second full refund through the HTTP path therefore returns 200
# with a zero-cent refund row where `main` rejected it, breaking AC-5. Nothing in
# the diff looks wrong in isolation and the suite passes; finding it takes running
# both branches. Negative amounts are unbounded for the same reason.

REFUNDS_REGRESSION = '''\
"""Refund processing."""

from . import db

REFUND_WINDOW_DAYS = 90


class RefundError(Exception):
    """A refund was rejected. `code` is stable and safe to match on."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def refund(
    order_id: str, amount_cents: int | None = None, reason: str | None = None
) -> dict:
    """Refund an order, in full or in part.

    Omitting `amount_cents` refunds the whole order total, which is what the
    original full-refund path did.
    """
    order = _load_order(order_id)
    if order["placed_days_ago"] > REFUND_WINDOW_DAYS:
        raise RefundError(
            "refund_window_expired",
            f"orders older than {REFUND_WINDOW_DAYS} days cannot be refunded",
        )
    if amount_cents is None:
        amount_cents = order["total_cents"] - _refunded_total_cents(order_id)
    remaining_cents = order["total_cents"] - _refunded_total_cents(order_id)
    if amount_cents > remaining_cents:
        raise RefundError(
            "refund_exceeds_total",
            "refund would take the order past its total",
        )
    return _record_refund(order_id, amount_cents, reason)


def refund_order(order_id: str) -> dict:
    """Refund an order in full.

    Retained so existing callers keep working unchanged; `refund` is the one
    entry point that does the work.
    """
    if _refunded_total_cents(order_id) > 0:
        raise RefundError("already_refunded", "order has already been refunded")
    return refund(order_id)


def _load_order(order_id: str) -> dict:
    rows = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not rows:
        raise RefundError("order_not_found", "no such order")
    return rows[0]


def _refunded_total_cents(order_id: str) -> int:
    rows = db.query("SELECT * FROM refunds WHERE order_id = ?", (order_id,))
    return sum(row["amount_cents"] for row in rows)


def _record_refund(order_id: str, amount_cents: int, reason: str | None) -> dict:
    db.query(
        "INSERT INTO refunds (order_id, amount_cents, reason) VALUES (?, ?, ?)",
        (order_id, amount_cents, reason),
    )
    return {"order_id": order_id, "amount_cents": amount_cents, "reason": reason}
'''

TESTS_REGRESSION = TESTS_BASE + '''

def test_partial_refund_records_the_requested_amount():
    """AC-1, AC-3."""
    db.seed_order({"id": "ord_2", "total_cents": 4999, "placed_days_ago": 3})
    result = refunds.refund("ord_2", 1500, "one item damaged")
    assert result["amount_cents"] == 1500
    assert result["reason"] == "one item damaged"


def test_refunds_cannot_exceed_the_order_total():
    """AC-2."""
    db.seed_order({"id": "ord_3", "total_cents": 4999, "placed_days_ago": 3})
    refunds.refund("ord_3", 4000, "partial")
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_3", 2000, "too much")
    assert excinfo.value.code == "refund_exceeds_total"


def test_refund_outside_the_window_is_rejected():
    """AC-4."""
    db.seed_order({"id": "ord_4", "total_cents": 4999, "placed_days_ago": 120})
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_4", 100, "too late")
    assert excinfo.value.code == "refund_window_expired"


def test_full_refund_path_is_unchanged():
    """AC-5."""
    db.seed_order({"id": "ord_5", "total_cents": 2500, "placed_days_ago": 1})
    assert refunds.refund_order("ord_5")["amount_cents"] == 2500
'''

# ----------------------------------------------------------- clean feature diff

REFUNDS_CLEAN = '''\
"""Refund processing."""

from . import db

REFUND_WINDOW_DAYS = 90


class RefundError(Exception):
    """A refund was rejected. `code` is stable and safe to match on."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def refund(
    order_id: str, amount_cents: int | None = None, reason: str | None = None
) -> dict:
    """Refund an order, in full or in part.

    Omitting `amount_cents` refunds the whole order total, which is what the
    original full-refund path did.
    """
    order = _load_order(order_id)
    if order["placed_days_ago"] > REFUND_WINDOW_DAYS:
        raise RefundError(
            "refund_window_expired",
            f"orders older than {REFUND_WINDOW_DAYS} days cannot be refunded",
        )
    remaining_cents = order["total_cents"] - _refunded_total_cents(order_id)
    if remaining_cents <= 0:
        raise RefundError("already_refunded", "order has already been refunded")
    if amount_cents is None:
        amount_cents = remaining_cents
    if amount_cents <= 0:
        raise RefundError(
            "invalid_amount", "refund amount must be a positive number of cents"
        )
    if amount_cents > remaining_cents:
        raise RefundError(
            "refund_exceeds_total",
            "refund would take the order past its total",
        )
    return _record_refund(order_id, amount_cents, reason)


def refund_order(order_id: str) -> dict:
    """Refund an order in full.

    Retained so existing callers keep working unchanged; `refund` is the one
    entry point that does the work, and the guards it applies are the same ones
    this path applied before.
    """
    return refund(order_id)


def _load_order(order_id: str) -> dict:
    rows = db.query("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not rows:
        raise RefundError("order_not_found", "no such order")
    return rows[0]


def _refunded_total_cents(order_id: str) -> int:
    rows = db.query("SELECT * FROM refunds WHERE order_id = ?", (order_id,))
    return sum(row["amount_cents"] for row in rows)


def _record_refund(order_id: str, amount_cents: int, reason: str | None) -> dict:
    db.query(
        "INSERT INTO refunds (order_id, amount_cents, reason) VALUES (?, ?, ?)",
        (order_id, amount_cents, reason),
    )
    return {"order_id": order_id, "amount_cents": amount_cents, "reason": reason}
'''

API_CLEAN = '''\
"""HTTP-facing serialization. Field names here are the public contract."""

from . import refunds


def serialize_refund(refund: dict) -> dict:
    """Render a refund as the JSON body clients receive."""
    return {
        "order_id": refund["order_id"],
        "amount_cents": refund["amount_cents"],
        "reason": refund["reason"],
    }


def post_refund(
    order_id: str, amount_cents: int | None = None, reason: str | None = None
) -> dict:
    """Handle `POST /orders/{order_id}/refund`."""
    return serialize_refund(refunds.refund(order_id, amount_cents, reason))
'''

TESTS_CLEAN = (TESTS_BASE + '''

def test_partial_refund_records_the_requested_amount():
    """AC-1, AC-3."""
    db.seed_order({"id": "ord_2", "total_cents": 4999, "placed_days_ago": 3})
    result = refunds.refund("ord_2", 1500, "one item damaged")
    assert result["amount_cents"] == 1500
    assert result["reason"] == "one item damaged"


def test_refunds_cannot_exceed_the_order_total():
    """AC-2."""
    db.seed_order({"id": "ord_3", "total_cents": 4999, "placed_days_ago": 3})
    refunds.refund("ord_3", 4000, "partial")
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_3", 2000, "too much")
    assert excinfo.value.code == "refund_exceeds_total"


def test_refund_outside_the_window_is_rejected():
    """AC-4."""
    db.seed_order({"id": "ord_4", "total_cents": 4999, "placed_days_ago": 120})
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_4", 100, "too late")
    assert excinfo.value.code == "refund_window_expired"


def test_full_refund_path_is_unchanged():
    """AC-5."""
    db.seed_order({"id": "ord_5", "total_cents": 2500, "placed_days_ago": 1})
    assert refunds.refund_order("ord_5")["amount_cents"] == 2500


def test_negative_refund_amount_is_rejected():
    db.seed_order({"id": "ord_6", "total_cents": 4999, "placed_days_ago": 1})
    with pytest.raises(refunds.RefundError) as excinfo:
        refunds.refund("ord_6", -500, "typo")
    assert excinfo.value.code == "invalid_amount"


def test_endpoint_rejects_a_second_full_refund():
    """AC-5, exercised through the HTTP path rather than the module function."""
    db.seed_order({"id": "ord_7", "total_cents": 4999, "placed_days_ago": 1})
    assert api.post_refund("ord_7")["amount_cents"] == 4999
    with pytest.raises(refunds.RefundError) as excinfo:
        api.post_refund("ord_7")
    assert excinfo.value.code == "already_refunded"
''').replace(
    "from src.orders import db, refunds", "from src.orders import api, db, refunds"
)

README_CLEAN = README_BASE.replace(
    """### `POST /orders/{order_id}/refund`

Refunds an order in full.

Response:

```json
{
  "order_id": "ord_123",
  "amount_cents": 4999,
  "reason": null
}
```
""",
    """### `POST /orders/{order_id}/refund`

Refunds an order in full, or in part when `amount_cents` is supplied.

Request:

```json
{
  "amount_cents": 1500,
  "reason": "one item damaged"
}
```

Both fields are optional. Omitting `amount_cents` refunds whatever is left of
the order total.

Response:

```json
{
  "order_id": "ord_123",
  "amount_cents": 1500,
  "reason": "one item damaged"
}
```

Rejections carry a stable `code`: `refund_exceeds_total` when the request would
take total refunds past the order total, `refund_window_expired` for orders
placed more than 90 days ago, `already_refunded` when nothing is left to refund,
and `invalid_amount` for a zero or negative amount.
""",
)


# The regression variant never implements an `invalid_amount` rejection, so its
# README must not advertise one — otherwise the doc/code mismatch becomes a
# finding on its own and the branch stops reading as clean.
README_REGRESSION = README_CLEAN.replace(
    """`refund_window_expired` for orders
placed more than 90 days ago, `already_refunded` when nothing is left to refund,
and `invalid_amount` for a zero or negative amount.""",
    """and `refund_window_expired` for orders
placed more than 90 days ago.""",
)


# --------------------------------------------------------------------- plumbing


def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def write(root: Path, rel: str, content: str):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def build(dest: Path, variant: str):
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    dest.mkdir(parents=True)

    run(["git", "init", "-q", "-b", "main"], dest)
    run(["git", "config", "user.email", "dev@example.com"], dest)
    run(["git", "config", "user.name", "Fixture Author"], dest)

    with_spec = variant != "defective-nospec"

    write(dest, "README.md", README_BASE)
    write(dest, "CODING_STANDARDS.md", STANDARDS)
    write(dest, ".gitignore", ".venv\n__pycache__/\n.pytest_cache/\n")
    write(dest, "src/orders/__init__.py", "")
    write(dest, "src/orders/db.py", DB_PY)
    write(dest, "src/orders/refunds.py", REFUNDS_BASE)
    write(dest, "src/orders/api.py", API_BASE)
    write(dest, "tests/__init__.py", "")
    write(dest, "tests/test_refunds.py", TESTS_BASE)
    if with_spec:
        write(dest, "specs/ORD-104-partial-refunds.md", SPEC)
    run(["git", "add", "-A"], dest)
    run(["git", "commit", "-q", "-m", "chore: initial orders-service"], dest)

    branch = "feature/partial-refunds"
    run(["git", "checkout", "-q", "-b", branch], dest)

    if variant in ("clean", "regression"):
        regression = variant == "regression"
        write(
            dest,
            "src/orders/refunds.py",
            REFUNDS_REGRESSION if regression else REFUNDS_CLEAN,
        )
        write(dest, "src/orders/api.py", API_CLEAN)
        write(
            dest,
            "tests/test_refunds.py",
            TESTS_REGRESSION if regression else TESTS_CLEAN,
        )
        write(dest, "README.md", README_REGRESSION if regression else README_CLEAN)
        run(["git", "add", "-A"], dest)
        run(
            [
                "git", "commit", "-q", "-m",
                "feat(refunds): allow partial refunds so agents keep the original "
                "authorization\n\nCloses ORD-104",
            ],
            dest,
        )
    else:
        write(dest, "src/orders/refunds.py", REFUNDS_DEFECTIVE)
        run(["git", "add", "-A"], dest)
        msg = (
            "feat(refunds): allow partial refunds so agents keep the original "
            "authorization"
        )
        if with_spec:
            msg += "\n\nCloses ORD-104"
        run(["git", "commit", "-q", "-m", msg], dest)

        write(dest, "src/orders/api.py", API_DEFECTIVE)
        write(dest, "tests/test_refunds.py", TESTS_DEFECTIVE)
        run(["git", "add", "-A"], dest)
        run(
            [
                "git", "commit", "-q", "-m",
                "feat(api): expose the refund amount and reason on the refund endpoint",
            ],
            dest,
        )

    print(f"built {variant} at {dest}")


if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve(), sys.argv[2])
