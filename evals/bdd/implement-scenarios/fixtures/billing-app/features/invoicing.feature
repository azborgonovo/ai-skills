@invoicing
Feature: Customer invoices
  As a finance officer
  I want an invoice to state what a customer owes
  So that I can chase the right amount at the right time

  @SCN-0201
  Scenario: An invoice totals the lines it holds
    Given an invoice with a line "Support" of €200
    And a line "Hosting" of €50
    Then the invoice total is €250

  @SCN-0202
  Scenario: A credit note reduces the invoice total
    Given an invoice with a line "Support" of €200
    When a credit note of €50 is added
    Then the invoice total is €150

  @SCN-0203
  Scenario: An invoice is overdue 30 days after it was issued
    Given an invoice issued on 10 January 2026
    When the finance officer reviews it on 10 February 2026
    Then the invoice is marked as overdue
