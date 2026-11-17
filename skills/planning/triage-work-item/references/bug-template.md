# Bug analysis comment template

Use this template when Step 3 classifies the item as a bug. It is a generic shape, not a fixed format. When a section genuinely does not apply, drop it instead of padding it.

```markdown
Triaged with 🤖 using <model> (<effort> effort):

**What's happening**
<Plain description of the mechanism, tied directly to the symptom that the reporter described. Name the concrete request, action, or flow. Do not restate the issue title in the abstract.>

**Root cause**
<The specific, verified code path, configuration value, or data condition. Name the files, and include an actual snippet where the snippet clarifies the issue better than prose does.>

```<language>
<verified code snippet>
```

<Explanation of why this code produces the reported symptom.>

**Why it's specific to this case** (omit when it does not apply)
<Why this customer, input, timing, or scale triggers the problem when others apparently do not.>

**Proposed fixes**
- Option A — <description>. Trade-off: <...>
- Option B — <description>. Trade-off: <...>

<A recommendation, when you have one, and why.>
```

## Notes

- **Proposed fixes** takes a second option only where a second one is reasonable. When only one sane fix exists, say so instead of adding a strawman.
- Quote the specific lines that demonstrate the bug, and not the whole method, unless the surrounding context is what makes the bug apparent.
- When the investigation reached no confident root cause, say so plainly instead of forcing the template. For example: "investigation so far narrows it to X or Y, and I cannot confirm which one without <missing piece of evidence>."
