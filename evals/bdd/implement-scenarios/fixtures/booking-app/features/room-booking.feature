@booking
Feature: Meeting room booking
  As an employee
  I want to book a meeting room for an hour
  So that my team has somewhere to meet

  Scenario: A free room is booked for the requested hour
    Given the room "Blue" is free at 10:00
    When Ada books the room "Blue" for 10:00
    Then the room "Blue" is reserved for Ada at 10:00

  Scenario: A second booking of the same hour is refused
    Given the room "Blue" is reserved for Ben at 10:00
    When Ada books the room "Blue" for 10:00
    Then Ada is told that the room is already taken
    And the room "Blue" is still reserved for Ben at 10:00

  Scenario: Booking works well
    Given a user books a room
    When they use the system
    Then it works

  Scenario: Ada moves her meeting to another room
    Given the room "Blue" is reserved for Ada at 10:00
    When Ada cancels the booking of the room "Blue"
    And Ada books the room "Green" for 10:00
    Then the room "Blue" is free at 10:00
    And the room "Green" is reserved for Ada at 10:00
