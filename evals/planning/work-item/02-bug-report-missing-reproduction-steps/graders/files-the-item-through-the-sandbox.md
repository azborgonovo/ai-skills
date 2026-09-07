---
type: regex
target:
  source: file
  path: tracker-calls.log
pattern: 'issue create'
match: contains
arm: with-only
---
