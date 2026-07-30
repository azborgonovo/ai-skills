# Bug analysis comment template

Use this template when Step 3 classifies the item as a bug — actual behavior deviates from what the system is intended or documented to do. For a change request (new/changed behavior, or non-behavioral work), use `references/change-request-template.md` instead.

This is a reasonable generic shape, not a fixed format — if the investigation genuinely doesn't fit one of these sections (e.g. there's no meaningful "why this specific case" angle), drop it rather than padding. Write it in the tracker's markup dialect (Step 4).

```markdown
Triaged with 🤖 using <model> (<effort> effort):

**What's happening**
<Plain description of the mechanism, tied directly to the symptom the reporter described. Name the concrete request/action/flow, not an abstract restatement of the issue title.>

**Root cause**
<The specific, verified code path. Name files, and include an actual snippet where it clarifies the issue better than prose would.>

```<language>
<verified code snippet>
```

<Explanation of why this code produces the reported symptom.>

**Why it's specific to this case** (omit if not applicable)
<Why this customer/input/timing/scale triggers it when others apparently don't.>

**Proposed fixes**
- Option A — <description>. Tradeoff: <...>
- Option B — <description>. Tradeoff: <...>

<A recommendation, if you have one, and why.>
```

## Notes

- The attribution-line convention (filling in `<model>`/`<effort>`, and using the literal 🤖 rather than a shortcode) is explained in Step 3 — apply it here too.
- Keep code snippets short and targeted — the specific lines that demonstrate the bug, not the whole method, unless the surrounding context is what makes the bug apparent.
- See "Keep it tight" in SKILL.md Step 10 for the same drafting habits applied here — cite the strongest evidence once rather than every corroborating source you found, and if the same gap shows up in more than one file, quote one and cite the rest by file:line.
- If you genuinely couldn't reach a confident root cause after investigation, say so plainly instead of forcing a template — e.g. "investigation so far narrows it to X or Y, but I couldn't confirm which without <missing piece of evidence>." An honest partial finding is more useful than a confident-sounding guess.
