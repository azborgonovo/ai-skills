Feature: Subscription billing
  As a subscriber
  I want my plan charged on a schedule I can predict
  So that I can budget for it

  Scenario: Monthly plan renews on the billing date
    Given Mira is on the "Standard" monthly plan at 12 euros per month
    When her billing date arrives
    Then she is charged 12 euros
    And her plan renews for another month

  Scenario: A declined card pauses the subscription
    Given Mira is on the "Standard" monthly plan at 12 euros per month
    And her card was declined on her billing date
    When the retry window of 3 days ends
    Then her subscription is paused
    And she is told that her payment failed

  Scenario: A subscriber cancels before the billing date
    Given Mira is on the "Standard" monthly plan at 12 euros per month
    When she cancels 4 days before her billing date
    Then her plan stays active until her billing date
    And she is not charged again
