# Platform notes

Running notes on the Lumen video platform. Updated when someone remembers.

## Team

- Two backend engineers, Sofia and Bram. One frontend engineer.
- Neither backend engineer has run Kubernetes or any container platform in production.
- On-call is best effort. There is no paid rota and no formal SLA with anyone internal.
- Standup is at 09:30. Sofia is out from 12 May to 26 May.

## Customer commitments

- The Nordwind contract, signed 2025-02-11, requires all learner video content to be
  stored and processed inside the EU. It names Frankfurt and Amsterdam as acceptable
  regions. Renewal is in March.
- Nordwind is 41 percent of revenue.
- The two smaller customers have no data residency clause.

## How we work

- The founding team decided we self-host everything. Nobody has revisited that since 2021.
- Everything ships from one repository. Deploys are manual and take about 20 minutes.

## Transcoding

- Four bare-metal encode boxes at the Amsterdam colo. Two of them are five years old.
- Box 3 has fallen over four times since January. Box 1 fell over once.
- Cost note: transcoding ran to EUR 4,100 in March 2024. That month we re-encoded the
  whole back catalogue in one go. Nobody has measured a normal month since.
- All encoding goes through one internal interface, `MediaPipeline`, and only
  `media/pipeline.py` knows which backend runs the job. Swapping the backend touches
  that one module.

## Odds and ends

- Log retention is 14 days.
- The billing test suite has one flaky test, `test_proration_rounding`.
- Grafana dashboard for encode queue depth exists but nobody has looked at it in months.
- The coffee machine is broken again.
