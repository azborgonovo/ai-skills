# Bug analysis comment template

Use this template when Step 3 classifies the item as a bug. For a change request, use `references/change-request-template.md` instead. Step 3 carries the test that separates the two.

This is a reasonable generic shape, not a fixed format. Sometimes the investigation genuinely does not fit one of these sections, for example when no meaningful "why this specific case" angle exists. Drop the section instead of padding it. Write the comment in the tracker's markup dialect, from Step 4.

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

- Step 3 explains the attribution-line convention, which covers filling in `<model>` and `<effort>`, and using the literal 🤖 rather than a shortcode. Apply it here too.
- **Proposed fixes** takes a second option only where a second one is reasonable. When only one sane fix exists, say so instead of padding the section with a strawman alternative.
- Keep a code snippet short and targeted. Quote the specific lines that demonstrate the bug, and not the whole method, unless the surrounding context is what makes the bug apparent.
- See "Keep it tight" in Step 10 of SKILL.md for the drafting habits that apply here. Cite the strongest evidence once, rather than every corroborating source you found. When the same gap shows up in more than one file, quote one and cite the rest by `file:line`.
- When the investigation genuinely reached no confident root cause, say so plainly instead of forcing the template. For example: "investigation so far narrows it to X or Y, and I cannot confirm which one without <missing piece of evidence>." An honest partial finding beats a confident-sounding guess.
