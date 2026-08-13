---
paths:
  - "**/*.cs"
---

# C# XML Documentation

Follow [Microsoft's recommended tags](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/recommended-tags).
Write every documentation comment in complete sentences that end with full stops.

## `<summary>` carries the description

Give every type and method you introduce a `<summary>`, and open every documentation comment with one — a documentation
comment that starts at `<remarks>` is incomplete. Say what the member is for, in one or two sentences.

`<summary>` is the text IntelliSense shows at the call site, so write it to stand on its own there: a reader who sees
only those sentences, with the declaration off screen, should know whether this is the member they want and how to call
it correctly.

Use `<param>`, `<returns>`, `<value>`, `<exception>`, and `<typeparam>` for the parts of the contract they name, and
`<see cref="..."/>` to point at related members. Put `<inheritdoc/>` on an implementation whose interface is already
documented.

## `<remarks>` carries the implementation semantics

Send to `<remarks>` everything that supplements the summary and would bury it: the invariants the member maintains,
legacy-parity rules, ordering and transaction requirements, why a state or outcome is unreachable, performance
characteristics, and the reasoning behind a choice that looks wrong at first glance. Lengthy explanations belong here —
this is the overflow, so let it run as long as the subject needs.

Reach for `<remarks>` whenever explanation starts crowding the summary, and whenever you are tempted to explain a member
at its call sites or in a block comment above its body. Structure a long one with `<para>`, `<list>`, and `<c>`.
