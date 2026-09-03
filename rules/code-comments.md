# Code Comments

The default is no comment. Write one only when the code cannot carry the meaning, and a reader gets it wrong without the comment.

- Comment the non-obvious *why*, never the *what*. When the line already says it, say nothing.
- A better name or a test beats a comment whenever either one will do.
- Put the comment on the line that is easy to get wrong, and not at the top of the function.
- Write the constraint that the code has to satisfy, and not the reasoning that reached it. Test each sentence. When it reads naturally in the commit message, that is where it goes.
- Documentation comments go on public API only, in the language's own format, so that a caller can skip the implementation.
- Tests carry none. The name of a test and its arrange, act, and assert body are its documentation. That holds for the fixtures, stubs, and utilities that a suite shares, because every caller sits in the same suite and can read them.
- Write for someone reading in ten months. Describe the constraint, and not today's task. Use no "new", "for now", "temporary", or "recently changed". Give no sprint status, no migration status, and no dates.
- Do not name tickets or merge requests by default. Name one only when the ticket holds context that does not fit in one line and still matters later. Do not open a ticket because a comment names one. Open it only when the current task needs it.
- Plain English, one or two lines. When it needs a paragraph, the code or the test is the wrong shape.
- Land at or below the comment density of the code around you. In a new file, match its neighbors in the same assembly or package. Every comment can be defensible on its own, and the file can still end up reading as prose.
- While you edit code, delete or fix any nearby comment that you cannot verify.
