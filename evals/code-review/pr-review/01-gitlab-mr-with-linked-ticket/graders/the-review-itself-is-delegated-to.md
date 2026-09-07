---
type: llm
focus: trace
---
The review itself is delegated to the review-changes skill (invoked via the Skill tool), handed the worktree path, the base SHA as the fixed point, the saved work item file as the spec, and the host's checks status as the test signal — the skill does not re-derive the pyramid layers, severity split, or verdict itself.
