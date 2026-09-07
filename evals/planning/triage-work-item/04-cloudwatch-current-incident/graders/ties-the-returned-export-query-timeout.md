---
type: llm
focus: trace
---
Ties the returned 'export.query timeout after 30s tenant=acme-42' lines to code it re-read itself: the unbounded `SELECT * FROM orders WHERE tenant_id = %s` and the QUERY_TIMEOUT_SECONDS = 30 bound in backend/export_service.py.
