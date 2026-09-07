"""Nightly reconciliation of the orders table against the ledger.

The write path maintains orders.updated_at on every insert and update.
"""

from time import time


def run_nightly(db, ledger, state):
    orders = db.query("SELECT * FROM orders")
    ledger_rows = ledger.fetch_all()
    mismatches = compare(orders, ledger_rows)
    state.write("last_run_at", time())
    return mismatches


def compare(orders, ledger_rows):
    by_id = {row["order_id"]: row for row in ledger_rows}
    return [o for o in orders if by_id.get(o["id"], {}).get("total") != o["total"]]
