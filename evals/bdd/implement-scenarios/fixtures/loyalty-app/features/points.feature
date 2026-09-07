@loyalty
Feature: Loyalty points on a purchase
  As a loyalty member
  I want points for what I spend
  So that I can turn them into rewards

  @SCN-0011
  Scenario: A member earns one point for each euro spent
    Given Ada is a loyalty member
    And Ada has a purchase of 40 euros
    When the purchase is completed
    Then Ada has 40 loyalty points

  Scenario: A redeemed reward takes its price off the balance
    Given Ada is a loyalty member
    And Ada has earned 500 loyalty points
    When Ada redeems the reward "Free Coffee"
    Then Ada has 350 loyalty points
    And the reward "Free Coffee" is issued to Ada
