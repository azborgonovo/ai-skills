---
type: llm
focus: trace
---
Describes the current mechanism from code it read: run_nightly in backend/reconcile_job.py issues `SELECT * FROM orders` every run, and the last_run_at value it writes is never read back as a watermark.
