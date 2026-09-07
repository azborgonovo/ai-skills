---
type: llm
focus:
  source: file
  path: posted-calls.log
arm: with-only
---
Each comment it posted is review-changes' report entry verbatim, with only the list number stripped, and is never re-drafted, expanded, or re-explained for the MR.
