@checkout @regression
Feature: Checkout discount codes
  As a shopper
  I want to apply a discount code to my order
  So that I pay the reduced price I was promised

  Scenario: Valid code reduces the order total
    Given a shopper has €80 of items in their cart
    When they apply the code "SPRING10"
    Then the order total drops to €72

  Scenario: Unknown code is rejected and leaves the total unchanged
    Given a shopper has €80 of items in their cart
    When they apply the code "BOGUS"
    Then the code is rejected with the message "We don't recognise that code"
    And the order total stays at €80
