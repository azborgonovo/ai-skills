# Work item template

Section headers are bold text, not markdown `##` or `###` headers. That matches how well-formed work items are written in the tools that hold them. Jira, GitHub, Azure DevOps, and Linear all render plain bold correctly. A markdown header often looks oversized in a narrow tracker pane, and sometimes it does not render at all.

## Skeleton

```
**<Framing section: Context | Observed Symptoms + Impact | Steps to reproduce>**

<1 to 3 short paragraphs, or a numbered list, depending on the framing section>

**Root cause** (optional: include it only after real analysis)

<what the analysis found, and never a placeholder>

**Plan** (optional: include it only after real analysis. Use it in place of Root cause for feature or infrastructure work)

<the approach, as a short list of concrete steps>

**Acceptance criteria** (mandatory, except for a conditionally-exempt child item. See SKILL.md)

- <testable, observable outcome>
- <testable, observable outcome>

**Out of Scope** (optional: include it only when real ambiguity is worth ruling out)

- <something that this work item deliberately does not cover>
```

Write each acceptance criterion as a testable and observable outcome, such as "X no longer happens", "Y is logged", or "Z test verifies...". Never write a vague statement such as "works correctly" or "is fixed".

## Worked examples

### Defect, with a Root cause

**Observed Symptoms**

Requests to `/api/orders/{id}` return `502` intermittently under load, on roughly 1% to 2% of requests during peak traffic. The orders service logs no matching error.

**Impact**

Customers see a generic error page when the order lookup fails. Support logged three tickets about this in the past week.

**Root cause**

The connection pool to the orders database caps at 20 connections, and peak concurrent request volume regularly reaches 35 to 40. The load balancer drops a request that cannot acquire a connection within the 2s pool timeout. It returns `502` before the app can return a proper error.

**Acceptance criteria**

- The connection pool size is raised to carry the peak concurrent load, and the configuration of the service documents the new limit.
- A request that exceeds the pool timeout returns a `503` with a `Retry-After` header, instead of an opaque `502`.
- A dashboard panel tracks pool saturation, so the problem is visible before it causes errors again.

### Work item with a Root cause, for tech debt rather than a defect report

**Context**

The nightly reconciliation job now takes more than 45 minutes, up from roughly 10 minutes three months ago. It is at risk of overlapping with the run of the next day.

**Root cause**

The job re-fetches the full customer table on every run, instead of fetching only the records changed since the last successful run. Growth of the customer table drives the slowdown.

**Acceptance criteria**

- The job processes only the records changed since the last successful run.
- Job duration drops back under 15 minutes at the current data volume.
- A regression test verifies that a record excluded from the incremental fetch is still picked up on the next run when it changes again.

### Work item with a Plan, for pure infrastructure work with no root cause

**Context**

We are moving the notification service off the shared message bus and onto its own dedicated queue. A backlog on one consumer then stops blocking every other consumer on the bus.

**Plan**

- Provision a dedicated queue for the notification service.
- Update the publisher to write to both the shared bus and the new queue during the transition.
- Cut the notification service over to consume from the new queue.
- Remove the dual write once the new queue is confirmed stable.

**Acceptance criteria**

- The notification service consumes only from its dedicated queue.
- A backlog induced artificially on an unrelated consumer no longer delays notification delivery.
- The dual-write code is removed, and the publisher writes to the dedicated queue only.

### Child item that needs its own acceptance criteria, because it is independently verifiable

The parent is "Migrate all services off the shared message bus onto dedicated queues", which is a standalone work item that carries the overall Plan. This child item covers one specific service, which deploys and gets verified on its own schedule, independently of the other services in the migration.

**Context**

Cut the billing service over to its dedicated queue, as part of the shared message bus migration.

**Acceptance criteria**

- The billing service consumes only from its dedicated queue in production.
- No billing event is lost during the cutover window, verified against the delivery log of the shared bus.

### Child item correctly left minimal, with no acceptance criteria

The parent is "Add profanity filtering to comment submission", which is a standalone work item that carries the overall acceptance criteria for the whole feature. This child item is one granular checklist entry under that parent. It has no independent "done" state, so it needs neither its own framing nor its own acceptance criteria.

(No content beyond the title. The acceptance criteria of the parent work item already cover this.)
