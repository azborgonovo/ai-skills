# exports-app

Two deployables behind the order export feature:

- `frontend/` — the orders screen. Plain ES modules, no build step.
- `backend/` — the export endpoint and the nightly reconciliation job. Python.

`GET /api/exports` renders the order list of one tenant. The nightly
reconciliation job runs at 02:00 UTC.
