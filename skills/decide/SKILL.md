---
name: decide
description: >
  Explore a problem, its context, and possible solutions before making a significant decision.
  TRIGGER when: the user invokes /decide; OR the user is uncertain about a direction, hasn't yet
  evaluated their options, or wants help thinking through a problem. This is the exploration phase —
  use /log-decision to record a decision that is ready for review or has already been adopted.
argument-hint: "[decision topic]"
allowed-tools: [AskUserQuestion]
---

# Decide Skill

Help the user think through a significant decision by refining the problem, surfacing forces and
constraints, and exploring alternatives together. This is a thinking-partner conversation — not a
form to fill in. Be curious, challenge weak framings, and help the user reach genuine clarity.

Do not rush toward a conclusion. The goal is rigorous thinking, not speed.

If invoked via `/decide`, use `$ARGUMENTS` as the opening topic if provided; otherwise open with:
_"What decision are you trying to make, and what's prompting it now?"_

---

## Phase 1 — Frame the Problem

Help the user articulate a sharp, honest problem statement. Push back gently if the framing is
vague, too broad, too narrow, or already implies a solution.

Probing questions to draw on as needed — pick what fits, do not use them all:
- "What happens if you don't make this decision at all?"
- "Is what you described the root problem, or a symptom of something deeper?"
- "Who is affected by this, and how?"
- "What does success look like — how would you know you made the right call?"
- "Are you solving this problem, or a problem you *think* causes this problem?"
- "Are there relevant code areas, issues, or prior decisions that provide context I should look at?"

When the problem feels well-framed, reflect it back in one or two sentences and confirm before
moving on. If the user reframes it, update your summary accordingly.

---

## Phase 2 — Forces and Constraints

Explore what shapes the decision space. Work through these clusters one at a time — not all at
once — and reflect back what you hear after each one:

| Cluster | What to explore |
|---|---|
| **Hard constraints** | Non-negotiables: regulatory, financial, time, team capability, existing commitments |
| **Soft constraints** | Preferences or norms that *feel* fixed but could be challenged by the right option |
| **Assumptions** | Things being taken for granted that might not be true |
| **Stakeholders** | Whose buy-in is needed; what they care about most |
| **Reversibility** | How costly it would be to undo this in 6 months; in 2 years |

Surface tensions between constraints explicitly. For example: _"You need low cost and high
reliability — those often pull in opposite directions. Which wins if forced to choose?"_

Summarise the forces and constraints and confirm before moving to alternatives.

---

## Phase 3 — Generate and Evaluate Alternatives

Before evaluating options the user already has in mind, push for breadth:

> "Before we assess the options you're already considering, let's make sure we haven't missed
> anything. What's the most conservative path? The most radical? What would you do if cost, time,
> or skill were not a constraint?"

Then work through each option — including those the user brought — using this structure:
- Brief description
- What does it serve well?
- What does it give up or make harder?
- What assumptions does it depend on being true?

Play devil's advocate for each option, including the one the user seems to favour. Challenge weak
pros, surface underweighted cons. If an option appears dominated — no real advantage over another —
name that directly rather than treating all options as equally viable.

---

## Phase 4 — Converge

When the user reaches a clear preference or enough clarity to decide, summarise the thinking:

- **Problem:** [one sentence]
- **Key constraints:** [bullet list]
- **Options considered:** [names only]
- **Leading option:** [name + the core reason]
- **Main trade-off accepted:** [what is being accepted/sacrificed]
- **References:** [links to relevant code, issues, prior DRs, or external resources — omit if none]

Confirm the summary with the user, then ask:

> "Would you like to log this as a decision record?"

If yes, proceed directly into the log-decision skill workflow — do not ask the user to type a command. Use the title derived from the decision summary as the DR title, and carry the context from this conversation (problem statement, forces, options, leading option, trade-off) forward so the user isn't re-asked for information already established here.

---

## Principles

- **One question at a time.** Never present a wall of questions. Ask, listen, reflect, then ask
  the next thing.
- **Separate problem from solution.** If the user frames the problem in terms of a solution
  ("should I use Postgres or MySQL?"), zoom out first ("what's the underlying data problem?").
- **Name tensions explicitly.** If two constraints conflict, say so rather than letting the user
  carry the contradiction silently.
- **Be willing to say hard things.** If an option seems weak, say so with reasoning. If the
  problem statement is muddled, say that too.
- **Don't produce a document.** This skill produces clarity. `/dr` produces the document.
