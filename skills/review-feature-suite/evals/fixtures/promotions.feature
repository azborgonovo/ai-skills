@promotions @regresion
Feature: Seasonal promotions
  As a customer
  I want seasonal promo codes applied to my purchase
  So that I benefit from the current campaign

  Scenario: Spring campaign code gives the customer a discount
    Given a customer has 80 euros of items in their purchase
    When they apply the code "SPRING10"
    Then the purchase total drops to 68 euros

  Scenario: Premium customers get an extra reward
    Given a customer has a premium subscription
    And a customer has 80 euros of items in their purchase
    When they apply the code "SPRING10"
    Then they earn 80 loyalty points
