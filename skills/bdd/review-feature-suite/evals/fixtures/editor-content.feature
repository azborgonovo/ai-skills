@content @smoke
Feature: Content editing
  As a Content Editor
  I want to publish articles
  So that readers see up-to-date content

  Scenario: Editor publishes a draft article
    Given a Content Editor is signed in
    And they have a draft article titled "Spring releases"
    When they publish the draft
    Then the article is visible to readers
    And the article shows a published date of "2026-06-29"

  Scenario: Reviewer cannot publish without approval
    Given a Reviewer is signed in
    When they try to publish a draft article
    Then publishing is blocked
    And they see the message "Publishing needs an Editor's approval"
