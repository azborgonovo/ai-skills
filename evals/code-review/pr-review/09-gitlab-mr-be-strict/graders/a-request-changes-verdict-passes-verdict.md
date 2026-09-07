---
type: llm
focus:
  source: file
  path: posted-calls.log
arm: with-only
---
A Request changes verdict passes --verdict request-changes with a --summary-file holding two or three sentences in the "I did not approve this merge request yet because <blocking finding>" shape — naming why it blocks and where the detail is, not restating the review's suggestions, checked-and-clean list, or path to merge.
