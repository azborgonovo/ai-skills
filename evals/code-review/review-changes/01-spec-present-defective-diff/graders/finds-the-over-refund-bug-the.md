---
type: llm
focus: last_message
---
Finds the over-refund bug: the guard compares against the order total while ignoring refunds already recorded, so repeated partial refunds can exceed AC-2's limit.
