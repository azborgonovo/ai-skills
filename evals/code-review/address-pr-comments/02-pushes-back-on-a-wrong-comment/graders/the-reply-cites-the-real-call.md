---
type: llm
focus:
  source: file
  path: writes.log
---
The reply it posted cites the real call site as evidence: src/api.py hands payload.get("percent", 0) to apply_discount with no validation of its own, so the branch is reachable.
