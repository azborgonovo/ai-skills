# work-item eval suite

Why these cases exist. Recovered from the `notes` field of the `evals.json` that
`claude plugin eval` replaced, so the design intent stays with the cases.

No case may create a real ticket. Cases 1, 3 and 4 stay in the drafting path, because the prompt
asks for a draft and nothing more. Case 2 asks for a create, and it runs against the sandbox gh
at evals/fixtures/bin/gh, which records the call in tracker-calls.log and reaches no network.
The skill picks its create tool at runtime, so the sandbox stub answers the gh commands that a
headless run can reach: auth status, repo view, label list, issue list and issue create. Every
other command exits 1 with a message that names the supported set.
