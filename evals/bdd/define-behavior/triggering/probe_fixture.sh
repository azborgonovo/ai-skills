#!/usr/bin/env bash
# Builds what the authoring probes assume: a ticket with acceptance criteria, a
# SpecFlow project, and existing scenarios that leak UI and API mechanics or
# check several things at once.
set -euo pipefail

mkdir -p features docs specs

cat > docs/TICKET-4412.md <<'EOF'
# TICKET-4412: Discount codes at checkout

## Acceptance criteria

- A shopper can apply one discount code per order.
- A percentage code reduces the order subtotal before tax.
- An expired code is rejected with a message that names the code.
- A code restricted to one category applies only to lines in that category.
- A second code replaces the first rather than stacking.
EOF

cat > docs/STORY-loyalty-tiers.md <<'EOF'
# Loyalty tiers

As a returning shopper I want my tier to be recognized at checkout so that I get
the discount I earned.

Tiers are bronze, silver and gold. Silver is five percent. Gold is ten percent.
A shopper moves up a tier when spend in the last year passes a threshold. A
shopper never moves down inside a calendar year.
EOF

cat > features/checkout.feature <<'EOF'
Feature: Checkout

  Scenario: Submit the order
    Given I am on /checkout
    When I click #submit
    And I POST to /api/orders with {"lines": 2}
    And I wait for the spinner to disappear
    Then the response status is 201
    And the div.order-confirmation shows the order id
EOF

cat > features/password_reset.feature <<'EOF'
Feature: Password reset

  Scenario: Reset flow
    Given a user exists
    When the user requests a reset
    And the user opens the email
    And the user sets a new password
    Then the password is changed
    And a confirmation email is sent
EOF

cat > specs/Checkout.Specs.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="SpecFlow" Version="3.9.74" />
    <PackageReference Include="SpecFlow.xUnit" Version="3.9.74" />
  </ItemGroup>
</Project>
EOF
