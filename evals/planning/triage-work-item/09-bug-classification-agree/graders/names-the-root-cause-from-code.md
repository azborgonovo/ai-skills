---
type: llm
focus: trace
---
Names the root cause from code it re-read itself: backend/export_service.py runs an unbounded `SELECT * FROM orders WHERE tenant_id = %s` under the 30-second QUERY_TIMEOUT_SECONDS bound, and materializes every row with list(rows).
