# Code Comments

Every piece of explanation has exactly one home. Pick it by what kind of explanation it is.

## Route the explanation

- **Why this change was made** — the approach chosen, the alternatives rejected, the performance win, the constraint
  that forced it: write it in the commit message body and the MR description.
- **What a member does, and how it behaves** — write it as documentation on the declaration, in the language's own
  documentation-comment format.
- **A fact the reader needs at this exact line and cannot get from the code** — a magic value's origin, a workaround for
  an external bug: write a one- or two-line comment right there.
- **Everything else** — express it in the code: name the constant, extract the local, extract the method, tighten the
  type. Reach for a name before reaching for a comment.

Explain a member once, at its declaration. Leave call sites to read as plain code, and trust the reader to follow the
name or hover the declaration when they want the detail.

## Match the file you are editing

Read the file's existing comments before writing one, and land within the same density and depth. A file that explains
itself in five lines across three hundred gets the same treatment for the code you add.

Document a new member when its siblings are documented. In a type whose members carry no documentation, add the member
bare and put what you would have documented into the MR description instead.

## Size

Keep an inline comment to three lines or fewer. When the explanation needs more room, move it onto the nearest
declaration's documentation comment, or introduce named code that carries the meaning.

When you have designed something and want to show your reasoning, put it in your reply to the user and in the commit
message. Let the code carry only what a reader needs a year from now with no access to the diff.
