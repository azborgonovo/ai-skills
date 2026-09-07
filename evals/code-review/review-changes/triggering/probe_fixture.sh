#!/usr/bin/env bash
# Builds the repository that the triggering probes of this skill assume: a main
# branch with enough history for HEAD~6, a develop branch, a v3.2 tag, and a
# feature branch that is ahead of main and carries uncommitted work.
set -euo pipefail

git init -q -b main .
git config user.email eval@example.com
git config user.name "Eval Fixture"

mkdir -p src tests

commit() { git add -A; git commit -qm "$1"; }

cat > README.md <<'EOF'
# Orders Service

Handles order capture and pricing.
EOF
commit "chore: scaffolded the orders service"

cat > src/pricing.py <<'EOF'
def subtotal(lines):
    return sum(line["qty"] * line["unit_price"] for line in lines)
EOF
commit "feat: added subtotal pricing"

cat > src/discounts.py <<'EOF'
def apply_discount(total, percent):
    return total - (total * percent / 100)
EOF
commit "feat: added percentage discounts"

cat > tests/test_pricing.py <<'EOF'
from src.pricing import subtotal


def test_subtotal_sums_lines():
    assert subtotal([{"qty": 2, "unit_price": 5}]) == 10
EOF
commit "test: covered the subtotal calculation"

cat > src/tax.py <<'EOF'
RATES = {"NL": 0.21, "DE": 0.19}


def tax_for(country, amount):
    return amount * RATES[country]
EOF
commit "feat: added country tax rates"

git tag v3.2

cat > src/shipping.py <<'EOF'
def shipping_cost(weight_kg):
    return 4.95 if weight_kg < 10 else 12.50
EOF
commit "feat: added flat shipping bands"

cat > src/orders.py <<'EOF'
from src.pricing import subtotal
from src.tax import tax_for


def total(order):
    net = subtotal(order["lines"])
    return net + tax_for(order["country"], net)
EOF
commit "feat: assembled the order total"

git branch develop

cat > src/refunds.py <<'EOF'
def refund(order, amount):
    if amount > order["total"]:
        raise ValueError("refund exceeds order total")
    return {"order_id": order["id"], "amount": amount}
EOF
commit "feat: added partial refunds"

git checkout -q -b feature/loyalty-tiers

cat > src/loyalty.py <<'EOF'
TIERS = {"bronze": 0, "silver": 5, "gold": 10}


def tier_discount(tier, total):
    percent = TIERS[tier]
    return total - (total * percent / 100)
EOF
commit "feat: added loyalty tier discounts"

cat > src/loyalty_rules.py <<'EOF'
def upgrade_tier(spend_last_year):
    if spend_last_year > 5000:
        return "gold"
    if spend_last_year > 1000:
        return "silver"
    return "bronze"
EOF
commit "feat: added tier upgrade thresholds"

# Uncommitted work, so a probe about work-in-progress changes finds some.
cat >> src/loyalty.py <<'EOF'


def stacked_discount(tier, total, promo_percent):
    after_tier = tier_discount(tier, total)
    return after_tier - (after_tier * promo_percent / 100)
EOF
