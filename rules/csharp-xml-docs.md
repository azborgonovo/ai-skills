---
paths:
  - "**/*.cs"
---

# C# XML Documentation

Which members get a documentation comment, and how long it runs, is settled before you reach this file. This is only how
to write the one you have already decided on.

Tag reference: [Microsoft's recommended tags](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags).

- Open at `<summary>`, never at `<remarks>`. Write it to stand alone in IntelliSense: one or two complete sentences, ending in full stops, telling a caller with the declaration off screen whether this is the member they want.
- `<inheritdoc/>` on an implementation whose interface is already documented. Never restate the interface's text.
- `<param>`, `<returns>`, `<exception>`, and `<typeparam>` only where they say something the signature does not — unless
  the build enforces them (CS1573), in which case one clause each.
- `<remarks>` only for a contract detail that would bury the summary: an invariant the caller must uphold, a required call order, a documented legacy-parity quirk. One or two lines, like any other comment — it is not an overflow for design rationale, and reaching for `<para>` or `<list>` inside it means the content belongs in the commit message.
