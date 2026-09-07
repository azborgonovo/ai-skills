@checkout
Feature: Checkout discount codes
  As a shopper
  I want a discount code applied to my order
  So that I pay the price I was promised

  @SCN-0001
  Scenario: A valid code reduces the order total
    Given a shopper has an order of €80
    When they apply the code "SPRING10"
    Then the order total drops to €72

  Scenario: A rejected code leaves the total unchanged
    Given a shopper has an order of €80
    When they apply the code "BOGUS"
    Then the code is rejected with the message "We do not recognise that code"
    And the order total stays at €80

  Scenario: An abandoned order survives a restart of the order service
    Given a shopper has an order of €80
    When the order service restarts
    Then the shopper still has an order of €80

  Scenario: A shopper sees the confirmation page after checking out
    Given a shopper is signed in with an order of €80
    When they complete the checkout in the storefront
    Then the storefront shows a confirmation page with the order number
