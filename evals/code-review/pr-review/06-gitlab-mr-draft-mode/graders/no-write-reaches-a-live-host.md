---
type: llm
focus: last_message
arm: with-only
---
No write reaches a live host: the run puts evals/fixtures/bin first on PATH, every glab call resolves to the stub there, and each draft call is recorded in posted-calls.log instead of sent.
