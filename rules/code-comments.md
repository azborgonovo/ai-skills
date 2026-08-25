# Code Comments

The default is no comment. Write one only when the code cannot carry the meaning and a reader would otherwise get it
wrong.

- Comment the non-obvious *why*, never the *what*. If the line already says it, say nothing.
- A better name or a test beats a comment whenever either will do.
- Put the comment on the line that is easy to get wrong, not at the top of the function.
- Write the constraint the code has to satisfy, not the reasoning that reached it. Test each sentence: if it would read naturally in the commit message, that is where it goes.
- Documentation comments go on public API only, in the language's own format, so a caller can skip the implementation.
- Tests carry none. A test's name and its arrange/act/assert body are its documentation, and that holds for the
  fixtures, stubs, and utilities a suite shares — every caller is in the same suite and can read them.
- Write for someone reading in ten months. Describe the constraint, not today's task: no "new", "for now", "temporary",
  "recently changed", no sprint or migration status, no dates.
- Do not name tickets or MRs by default — only when the ticket holds context that will not fit in one line and will
  still matter later. Do not open a ticket just because a comment names one; only if the current task needs it.
- Plain English, one or two lines. If it needs a paragraph, the code or the test is the wrong shape.
- Land at or below the comment density of the code around you; in a new file, match its neighbors in the same assembly or package. Every comment can be defensible on its own and the file still end up reading as prose.
- While editing code, delete or fix any nearby comment you cannot verify.
