# Default analysis comment template

Use this only when no reference comment was given to mirror (Step 3 of SKILL.md). It's a reasonable
generic shape, not a fixed format — if the investigation genuinely doesn't fit one of these
sections (e.g. there's no meaningful "why this specific case" angle), drop it rather than padding.

```markdown
:robot: analysis:

**What's happening**
<Plain description of the mechanism, tied directly to the symptom the reporter described. Name the
concrete request/action/flow, not an abstract restatement of the ticket title.>

**Root cause**
<The specific, verified code path. Name files, and include an actual snippet where it clarifies the
issue better than prose would.>

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

- The `:robot: analysis:` opener is a convention some engineers use to make it visually clear a
  comment was AI-assisted — keep it (or whatever the reference example used) so readers can
  calibrate their trust and scrutiny accordingly. Don't drop it to make the comment look more
  "human."
- Keep code snippets short and targeted — the specific lines that demonstrate the bug, not the
  whole method, unless the surrounding context is what makes the bug apparent.
- If you genuinely couldn't reach a confident root cause after investigation, say so plainly instead
  of forcing a template — e.g. "investigation so far narrows it to X or Y, but I couldn't confirm
  which without <missing piece of evidence>." An honest partial finding is more useful than a
  confident-sounding guess.
