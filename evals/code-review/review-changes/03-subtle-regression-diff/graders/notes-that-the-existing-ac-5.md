---
type: llm
focus: trace
---
Notes that the existing AC-5 test passes only because it calls refund_order directly and never exercises the changed api.post_refund path.
