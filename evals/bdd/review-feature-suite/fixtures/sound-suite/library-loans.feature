@loans
Feature: Library loans
  As a library member
  I want to borrow and return books
  So that I can read without buying every title

  Background:
    Given Ada is a library member with no books on loan

  Scenario: A member borrows an available book
    Given the library holds one copy of "Dune"
    When Ada borrows "Dune"
    Then "Dune" is on loan to Ada
    And the library holds no available copy of "Dune"

  Scenario: A member cannot borrow a book that is already on loan
    Given the library holds one copy of "Dune"
    And "Dune" is on loan to Ben
    When Ada borrows "Dune"
    Then Ada is told "Dune" is on loan until 14 March 2026
    And "Dune" is on loan to Ben

  Scenario: Returning a book makes it available again
    Given "Dune" is on loan to Ada
    When Ada returns "Dune"
    Then the library holds one available copy of "Dune"
    And Ada has no books on loan

  Scenario: A member reaches the borrowing limit
    Given Ada has 5 books on loan
    And the library holds one copy of "Dune"
    When Ada borrows "Dune"
    Then Ada is told a member may hold 5 books at once
    And "Dune" stays available
