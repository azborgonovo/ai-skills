#!/usr/bin/env bash
# Builds a feature suite that has genuinely drifted, because every probe of this
# skill asks about drift across files: mixed vocabulary, duplicated steps,
# contradictory scenarios, mixed tag spellings and inconsistent data formats.
set -euo pipefail

mkdir -p features

cat > features/checkout.feature <<'EOF'
@regression @checkout
Feature: Checkout

  Scenario: A shopper completes an order
    Given a basket with 1 item priced at €72
    When the shopper submits the order
    Then the order is complete

  Scenario: A shopper pays with a declined card
    Given a basket with 1 item priced at €72
    When the shopper pays with a declined card
    Then the order is rejected
EOF

cat > features/payments.feature <<'EOF'
@regresion @smoke
Feature: Payments

  Scenario: A customer completes a purchase
    Given a cart with 1 product priced at 72 euros
    When the customer submits the purchase
    Then the purchase is finished

  Scenario: A customer pays with a card that is declined
    Given a cart with 1 product priced at 72 euros
    When the customer pays with a declined card
    Then the purchase is rejected
EOF

cat > features/basket.feature <<'EOF'
@smoke-test
Feature: Basket

  Scenario: A shopper adds an item
    Given an empty basket
    When the shopper adds 1 item priced at €72
    Then the basket holds 1 item

  Scenario: A buyer empties the trolley
    Given a trolley with 2 products
    When the buyer empties the trolley
    Then the trolley is empty
EOF

cat > features/refunds.feature <<'EOF'
@regression
Feature: Refunds

  Scenario: A full refund returns the whole amount
    Given a completed order of 72 euros
    When the agent refunds the order in full
    Then the shopper is repaid 72 euros

  Scenario: A refund is refused after ninety days
    Given a completed order placed 91 days ago
    When the agent refunds the order in full
    Then the refund is refused
EOF

cat > features/returns.feature <<'EOF'
@regresion @returns
Feature: Returns

  Scenario: A full refund returns the whole amount
    Given a finished purchase of €72
    When the support agent returns the purchase in full
    Then the customer is repaid €72

  Scenario: A return is allowed within one year
    Given a completed order placed 91 days ago
    When the agent refunds the order in full
    Then the refund is accepted
EOF

cat > features/delivery.feature <<'EOF'
@smoke
Feature: Delivery

  Scenario: A parcel under ten kilos ships at the flat rate
    Given a parcel weighing 4 kg
    When delivery is priced
    Then the delivery cost is €4.95

  Scenario: A heavy parcel ships at the heavy rate
    Given a parcel weighing 12 kilograms
    When shipping is priced
    Then the shipping cost is 12.50 euros
EOF
