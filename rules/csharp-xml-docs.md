---
paths:
  - "**/*.cs"
---

# C# XML Documentation

Which members get a documentation comment, and how long it runs, is settled before you reach this file. This file covers only how to write the one you already decided on.

Tag reference: [Microsoft's recommended tags](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags).

- Open at `<summary>`, never at `<remarks>`. Write it to stand alone in IntelliSense: one or two complete sentences, each ending in a full stop. It must tell a caller with the declaration off screen whether this is the member they want.
- Put `<inheritdoc/>` on an implementation whose interface is already documented. Never restate what the interface already says.
- Use `<param>`, `<returns>`, `<exception>`, and `<typeparam>` only where they say something that the signature does not. The exception is a build that enforces them through CS1573, where each one takes one clause.
- Use `<remarks>` only for a contract detail that buries the summary. That detail is an invariant the caller must uphold, a required call order, or a documented legacy-parity quirk. Keep it to one or two lines, like any other comment. It is not an overflow for design rationale, and content that needs `<para>` or `<list>` inside it belongs in the commit message.
