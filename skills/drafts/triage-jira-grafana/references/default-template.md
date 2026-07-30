# Default analysis comment template

Use this only when no reference comment was given to mirror (Step 3 of SKILL.md). It's a reasonable
generic shape, not a fixed format — if the investigation genuinely doesn't fit one of these
sections (e.g. there's no meaningful "why this specific case" angle), drop it rather than padding.

```markdown
Triaged with 🤖 using <model> (<effort> effort):

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

- The `Triaged with 🤖 using <model> (<effort> effort)` opener is a convention some engineers use
  (mirrored from the equivalent `Co-reviewed with :robot: using <model>` footer in the
  `gitlab-jira-mr-review` skill) to make it visually clear a comment was AI-assisted, and by which
  model, so readers can calibrate their trust and scrutiny accordingly. Keep some form of it — or
  whatever the mirrored reference comment used, see Step 3 — rather than dropping it to make the
  comment look more "human."
  - Always fill in `<model>` — you always know your own model name from your environment context
    (e.g. `Sonnet 5`).
  - Only fill in `(<effort> effort)` when you have a concrete, known effort/thinking-level setting
    for this session to report — never guess one just to fill the field. When you don't have one,
    drop the whole parenthetical rather than writing a placeholder: `Triaged with 🤖 using Sonnet 5:`.
- Use the literal Unicode emoji character (🤖), not a `:robot:`-style shortcode. Jira's
  markdown-to-ADF conversion (via `addCommentToJiraIssue` with `contentFormat: "markdown"`) does not
  expand emoji shortcodes the way Slack or GitHub-flavored markdown (and therefore GitLab, which is
  why `gitlab-jira-mr-review` can use `:robot:` in its footer) do — posting `:robot:` in a Jira
  comment renders as the literal text ":robot:", not an emoji. This applies to any other emoji you
  might want to use in a Jira comment, not just this opener.
- Keep code snippets short and targeted — the specific lines that demonstrate the bug, not the
  whole method, unless the surrounding context is what makes the bug apparent.
- If you genuinely couldn't reach a confident root cause after investigation, say so plainly instead
  of forcing a template — e.g. "investigation so far narrows it to X or Y, but I couldn't confirm
  which without <missing piece of evidence>." An honest partial finding is more useful than a
  confident-sounding guess.
