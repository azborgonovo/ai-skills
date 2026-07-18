# Work item template

Section headers are bold text, not markdown `##`/`###` — this matches how well-formed tickets are
actually written in the tools they end up in (Jira, GitHub, Azure DevOps, Linear all render plain
bold fine; markdown headers often look oversized or don't render at all in narrow ticket panes).

## Skeleton

```
**<Framing section: Context | Observed Symptoms + Impact | Steps to reproduce>**

<1-3 short paragraphs or a numbered list, depending on the framing section>

**Root cause** (optional — only if real analysis was done)

<what was actually found, not a placeholder>

**Plan** (optional — only if real analysis was done; use instead of Root cause for feature/infra work)

<the approach, as a short list of concrete steps>

**Acceptance criteria** (mandatory, except conditionally-exempt child items — see SKILL.md)

- <testable, observable outcome>
- <testable, observable outcome>

**Out of Scope** (optional — only when there's real ambiguity worth ruling out)

- <thing deliberately not covered by this ticket>
```

Write Acceptance criteria bullets as testable, observable outcomes: "X no longer happens", "Y is logged", "Z test verifies..." — not vague statements like "works correctly" or "is fixed."

## Worked examples

### Defect, with Root cause

**Observed Symptoms**

Requests to `/api/orders/{id}` intermittently return `502` under load, roughly 1-2% of requests
during peak traffic. No corresponding error is logged on the orders service itself.

**Impact**

Customers see a generic error page when the order lookup fails; support has logged three tickets
referencing this in the past week.

**Root cause**

The connection pool to the orders database is capped at 20 connections, but peak concurrent
request volume regularly hits 35-40. Requests that can't acquire a connection within the 2s pool
timeout are dropped by the load balancer as `502` before the app can return a proper error.

**Acceptance criteria**

- Connection pool size is raised to accommodate peak concurrent load, and the new limit is
  documented in the service's config
- Requests that do exceed the pool timeout return a `503` with a `Retry-After` header instead of
  surfacing as an opaque `502`
- A dashboard panel tracks pool saturation so this is visible before it causes errors again

### Work item with Root cause (tech-debt, not a defect report)

**Context**

The nightly reconciliation job has been taking 45+ minutes, up from ~10 minutes three months ago,
and is now at risk of overlapping with the next day's run.

**Root cause**

The job re-fetches the full customer table on every run instead of only fetching records changed
since the last successful run. Customer table growth is what's driving the slowdown.

**Acceptance criteria**

- The job only processes records changed since the last successful run
- Job duration drops back to under 15 minutes on the current data volume
- A regression test verifies that a record excluded from the incremental fetch is still picked up
  on the next run if it changes again

### Work item with Plan (pure infra work, no root cause)

**Context**

We're moving the notification service off the shared message bus and onto its own dedicated queue,
so a backlog on one consumer stops blocking every other consumer on the bus.

**Plan**

- Provision a dedicated queue for the notification service
- Update the publisher to write to both the shared bus and the new queue during the transition
- Cut the notification service over to consume from the new queue
- Remove the dual-write once the new queue is confirmed stable

**Acceptance criteria**

- The notification service consumes exclusively from its dedicated queue
- A backlog artificially induced on an unrelated consumer no longer delays notification delivery
- Dual-write code is removed and the publisher writes to the dedicated queue only

### Child item needing its own Acceptance criteria (independently verifiable)

Parent: "Migrate all services off the shared message bus onto dedicated queues" (a standalone work
item, carries the overall Plan). This child item covers one specific service, which is deployed
and verified on its own schedule independent of the other services in the migration.

**Context**

Cut the billing service over to its dedicated queue as part of the shared message bus migration.

**Acceptance criteria**

- The billing service consumes exclusively from its dedicated queue in production
- No billing events are lost during the cutover window (verified against the shared bus's
  delivery log)

### Child item correctly left minimal (no Acceptance criteria needed)

Parent: "Add profanity filtering to comment submission" (a standalone work item, carries the
overall Acceptance criteria covering the whole feature). This child item is one granular checklist
item under that parent — it has no independent "done" state of its own, so it doesn't need its own
framing or acceptance criteria.

(No content beyond the title — the parent ticket's acceptance criteria already covers this.)