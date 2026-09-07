# standard-first eval suite

Why these cases exist. Recovered from the `notes` field of the `evals.json` that
`claude plugin eval` replaced, so the design intent stays with the cases.

The run is headless and has no network, so no case can require a live documentation fetch or a
registry lookup. Where an expectation covers documentation, it asks the run to name the standard
API and to say that the API must be confirmed against current official docs. Cases 1 to 3 push
against a hand-rolled primitive, a legacy API the user names, and a non-standard local helper.
Case 4 is the near-miss, where custom code is the correct answer and the skill must not force a
package onto the problem.
