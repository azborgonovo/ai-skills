@auth @smoke
Feature: Account sign-in
  As a registered user
  I want to sign in to my account
  So that I can reach my personalised content

  Background:
    Given Ada is a registered user with the "Editor" role

  Scenario: Registered user reaches their dashboard after signing in
    When Ada signs in with valid credentials
    Then she sees her personal dashboard

  Scenario: Wrong password keeps the user signed out
    Given the user is logged in is not yet true for Ada
    When Ada authenticates with an incorrect password
    Then she stays on the sign-in page
    And she sees the message "Those credentials don't match"
