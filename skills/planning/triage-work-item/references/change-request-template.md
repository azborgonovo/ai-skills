# Change-request analysis comment template

Use this template when Step 3 classifies the item as a change request, which covers non-behavioral work too. For an item that reports broken existing behavior, use `references/bug-template.md` instead. Step 3 carries the test that separates the two.

This is a reasonable generic shape, not a fixed format. When a section genuinely does not apply, drop it instead of padding it. A small, contained change rarely has a meaningful "risks" angle. Write the comment in the tracker's markup dialect, from Step 4.

```markdown
Triaged with 🤖 using <model> (<effort> effort):

**How it works today**
<The current mechanism or behavior, tied to the specific code path. For non-behavioral work, give the current state that drives the request, such as the current structure, the current test coverage, or the current performance.>

**What must change**
<The concrete new or changed behavior that the item requests, stated precisely enough that "done" is unambiguous. For non-behavioral work, give the concrete end state, such as "the module splits into X and Y" or "the job runs incrementally instead of full-table".>

**Proposed approach**
- Option A — <description>. Trade-off: <...>
- Option B — <description>. Trade-off: <...>

<A recommendation, when you have one, and why.>

**Risks / open questions** (omit when they do not apply)
<Anything that complicates the approach: a data migration, backward compatibility, affected callers, or a decision that needs a stakeholder before work starts.>

**Rough effort**
<small | medium | large>, <one-line reason tied to what the approach actually touches>.
```

## Notes

- Step 3 explains the attribution-line convention, which covers filling in `<model>` and `<effort>`, and using the literal 🤖 rather than a shortcode. Apply it here too.
- **Proposed approach** takes a second option only where a genuine choice exists. Name the code that has to change, plus any complicating factor, such as a data migration, backward compatibility, or affected callers.
- **Rough effort** is a relative sizing signal for planning, and not a commitment. Calibrate small, medium, and large to obvious signals. Those signals are one file against several services or teams, a needed data migration, and a design or product input needed before work starts. Do not give a precise estimate.
- For a non-behavioral task with no user-visible behavior change, **What must change** describes the concrete engineering outcome. That outcome is the structure, the test coverage, or the performance. Do not force a behavioral framing where none exists.
- See "Keep it tight" in Step 10 of SKILL.md for the drafting habits that apply here. When one option in **Proposed approach** is clearly the pick, give it the fuller explanation. Dispatch the weaker one in a clause, rather than mirroring its depth for symmetry.
- When the investigation genuinely reached no confident approach, say so plainly instead of forcing the template. For example: "the current mechanism is clear, and the approach depends on whether <X> is in scope, which needs a product decision." An honest partial finding beats a confident-sounding guess.
