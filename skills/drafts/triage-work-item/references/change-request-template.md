# Change-request analysis comment template

Use this template when Step 3 classifies the item as a change request — the system does what it was built to do, but the desired behavior is changing, or the work is non-behavioral (refactor, chore, tech debt, spike) where neither "root cause" nor "problem" fits. For an item reporting that existing behavior is broken, use `references/bug-template.md` instead.

This is a reasonable generic shape, not a fixed format — if a section genuinely doesn't apply (there is rarely a meaningful "risks" angle for a small, contained change), drop it rather than padding. Write it in the tracker's markup dialect (Step 4).

```markdown
Triaged with 🤖 using <model> (<effort> effort):

**How it works today**
<The current mechanism/behavior, tied to the specific code path — or, for non-behavioral work, the current state driving the request (e.g. current structure, current test coverage, current performance).>

**What should change**
<The concrete new/changed behavior being requested, stated precisely enough that "done" is unambiguous. For non-behavioral work, the concrete end state (e.g. "the module splits into X and Y", "the job runs incrementally instead of full-table").>

**Proposed approach**
- Option A — <description>. Tradeoff: <...>
- Option B — <description>. Tradeoff: <...>

<A recommendation, if you have one, and why.>

**Risks / open questions** (omit if not applicable)
<Anything that complicates the approach — data migration, backward compatibility, affected callers, a decision that needs a stakeholder before work starts.>

**Rough effort**
<small | medium | large>, <one-line reason tied to what the approach actually touches>.
```

## Notes

- The `Triaged with 🤖 using <model> (<effort> effort)` opener signals AI assistance and by which model, so readers calibrate trust and scrutiny accordingly — keep it rather than dropping it to make the comment look more "human."
  - Always fill in `<model>`. Only fill in `(<effort> effort)` when you have a concrete, known effort/thinking-level setting for this session — never guess one, and drop the whole parenthetical rather than write a placeholder.
- Use the literal Unicode emoji character (🤖), not a `:robot:`-style shortcode, unless you've confirmed the tracker's renderer expands shortcodes — Jira's does not (see `references/trackers/jira.md`).
- **Rough effort** is a relative sizing signal for planning, not a commitment — small/medium/large, calibrated to obvious signals (touches one file vs. spans multiple services/teams, needs a data migration, needs design/product input before work starts) rather than a precise estimate.
- For a non-behavioral task with no user-visible behavior change, **What should change** describes the concrete engineering outcome (structure, test coverage, performance) rather than a behavior — don't force a behavioral framing where none exists.
- If you genuinely couldn't reach a confident approach after investigation, say so plainly instead of forcing the template — e.g. "the current mechanism is clear, but the approach depends on whether <X> is in scope, which needs a product decision." An honest partial finding is more useful than a confident-sounding guess.
