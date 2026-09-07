# decide eval suite

Why these cases exist. Recovered from the `notes` field of the `evals.json` that
`claude plugin eval` replaced, so the design intent stays with the cases.

This skill produces thinking, not a document, so almost every expectation is judgment. Case 1
tests reframing a solution back into a problem. Case 2 tests whether a hard constraint that the
user never stated is pulled out of the repository and allowed to change the answer. Case 3 is
the near-miss: a decision small enough that the right answer is short, so its expectations test
the moves the method still makes at that size, which are the reframe, the wider option set, the
named owner, and the trade-off of the option it picks. Case 4 is the central task, where the
options are real and the trade-off has to be named. Only three contract expectations exist
across the suite, and each one matches a rule the skill states outright.
