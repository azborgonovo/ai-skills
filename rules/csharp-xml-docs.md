---
paths:
  - "**/*.cs"
---

# C# XML Documentation

Tag reference: [Microsoft's recommended tags](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags).

- `<summary>` on public and protected members only, and never a documentation comment that opens at `<remarks>`.
  Private and internal helpers get a clear name instead.
- Write the `<summary>` to stand alone in IntelliSense: one or two complete sentences, ending in full stops, telling a
  caller with the declaration off screen whether this is the member they want.
- `<inheritdoc/>` on an implementation whose interface is already documented. Never restate the interface's text.
- `<param>`, `<returns>`, `<exception>`, and `<typeparam>` only where they say something the signature does not — unless
  the build enforces them (CS1573), in which case one clause each.
- `<remarks>` only for a contract detail that would bury the summary: an invariant the caller must uphold, a required
  call order, a documented legacy-parity quirk. Not for design rationale — that goes in the commit message.
