# triage-work-item eval suite

Why these cases exist. Recovered from the `notes` field of the `evals.json` that
`claude plugin eval` replaced, so the design intent stays with the cases.

Every case runs offline against fixtures. No case touches a live tracker or a live observability
platform. evals/fixtures/bin holds stub `twg`, `gh` and `aws` executables, and each prompt puts
that directory first on PATH. The stubs serve canned JSON from evals/fixtures/tracker and
evals/fixtures/observability, and every write call, such as posting a comment, appends the body
to $PWD/posted-calls.log and exits 0 without a network call. The Jira keys and the GitHub
repository in the prompts do not exist on any real host, so a call that escapes the stub cannot
write to a real work item either. evals/fixtures/exports-app is the codebase fixture, and it
carries three planted defects: a swallowed catch around window.showSaveFilePicker in
frontend/export-button.js, an unbounded export query under a 30-second timeout in
backend/export_service.py, and a full-table read with an unused last_run_at watermark in
backend/reconcile_job.py. Run `bash evals/fixtures/build.sh` once before the suite. It builds
the git checkouts that cases 1 and 8 use, because git metadata does not survive a commit into
this repository, and those two cases report a missing fixture until it has run. Only cases 6 and
7 sit on the triggering axis alone and end before any real work, so case 7 needs no fixture and
case 6 needs the tracker stub only. Cases 2, 10 and 11 carry one triggering expectation each,
and they still run the whole workflow against the fixture. Grafana has no case, because the
skill reaches Grafana only through mcp__grafana__* tools, and run_evals.py passes --strict-mcp-
config and loads no MCP server, so no stub can stand in for it. The Jira MCP backend of the
adapter is unreachable for the same reason, which leaves the twg CLI backend as the Jira path
that these cases exercise.
