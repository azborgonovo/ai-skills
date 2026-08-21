# Code Comments

The default is no comment. Write one only when the code cannot carry the meaning and a reader would otherwise get it
wrong.

- Comment the non-obvious *why*, never the *what*. If the line already says it, say nothing.
- A better name or a test beats a comment whenever either will do.
- Put the comment on the line that is easy to get wrong, not at the top of the function. Its job is to stop a plausible
  refactor from breaking something.
- Documentation comments go on public API only, in the language's own format, so a caller can skip the implementation.
  Follow the file you are editing: in a type whose members carry none, add the member bare.
- Rationale for a change — the approach chosen, the alternatives rejected, the constraint that forced it — goes in the
  commit message and the MR description, never in the code.
- Write for someone reading in ten months. Describe the constraint, not today's task: no "new", "for now", "temporary",
  "recently changed", no sprint or migration status, no dates.
- Do not name tickets or MRs by default — only when the ticket holds context that will not fit in one line and will
  still matter later. Do not open a ticket just because a comment names one; only if the current task needs it.
- Plain English, one or two lines. If it needs a paragraph, the code or the test is the wrong shape.
- While editing code, delete or fix any nearby comment you cannot verify.
