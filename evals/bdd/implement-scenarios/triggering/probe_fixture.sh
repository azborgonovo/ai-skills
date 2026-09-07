#!/usr/bin/env bash
# Builds what the automation probes assume: feature files with no step
# definitions behind them, and a test project ready to hold them.
set -euo pipefail

mkdir -p features tests

cat > features/checkout.feature <<'EOF'
Feature: Checkout

  Scenario: A shopper pays for a basket with one item
    Given a basket with 1 item priced at 20.00 EUR
    When the shopper pays with a valid card
    Then the order is confirmed
    And the shopper receives a confirmation email

  Scenario: A declined card leaves the basket untouched
    Given a basket with 1 item priced at 20.00 EUR
    When the shopper pays with a card that the issuer declines
    Then the order is not created
    And the basket still holds 1 item
EOF

cat > features/booking.feature <<'EOF'
Feature: Room booking

  Scenario: A guest books an available room
    Given room 101 is free on 2026-03-01
    When the guest books room 101 for 2026-03-01
    Then the booking is confirmed

  Scenario: A guest cannot double book a room
    Given room 101 is booked on 2026-03-01
    When another guest books room 101 for 2026-03-01
    Then the booking is refused
    And the guest is told the room is taken
EOF

cat > features/pricing.feature <<'EOF'
Feature: Pricing

  Scenario: Tax is added on top of the subtotal
    Given a basket subtotal of 100.00 EUR
    And the shopper is in the Netherlands
    When the total is calculated
    Then the total is 121.00 EUR
EOF

cat > tests/Booking.Tests.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Reqnroll.xUnit" Version="2.1.0" />
    <PackageReference Include="Testcontainers" Version="3.10.0" />
  </ItemGroup>
</Project>
EOF

cat > README.md <<'EOF'
# Booking service

The scenarios in features/ are the specification. Nothing automates them yet.
EOF
