# SRCH-412 — Workspace search is slow on large workspaces

**Context**

Workspace search takes about 2.4 seconds at the 95th percentile for a workspace
that holds more than 50,000 documents. Product asked for 400 ms at the same
percentile. A small workspace answers in about 300 ms today, so the delay grows
with the document count.

**Root cause**

The service asks the database for every matching row, then re-ranks the whole
result set in the application. The ranking loop runs once per match, so its cost
grows with the size of the workspace. The database index is not the limit here.

**Acceptance criteria**

- Search works correctly.
- Performance is improved.
- No regressions.
