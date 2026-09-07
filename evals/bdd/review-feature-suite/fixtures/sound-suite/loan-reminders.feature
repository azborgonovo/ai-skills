@loans @reminders
Feature: Loan reminders
  As a library member
  I want a reminder before a book is due
  So that I can return it without paying a late fee

  Background:
    Given Ada is a library member with no books on loan

  Scenario: A member is reminded two days before a book is due
    Given "Dune" is on loan to Ada until 14 March 2026
    When the reminder run happens on 12 March 2026
    Then Ada receives a reminder that "Dune" is due on 14 March 2026

  Scenario: A member is not reminded twice for the same loan
    Given "Dune" is on loan to Ada until 14 March 2026
    And Ada has received a reminder for "Dune"
    When the reminder run happens on 13 March 2026
    Then Ada receives no further reminder for "Dune"

  Scenario: A returned book triggers no reminder
    Given "Dune" was on loan to Ada until 14 March 2026
    And Ada returned "Dune" on 11 March 2026
    When the reminder run happens on 12 March 2026
    Then Ada receives no reminder for "Dune"
