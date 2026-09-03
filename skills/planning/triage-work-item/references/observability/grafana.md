# Observability adapter: Grafana

Mechanics for corroborating a hypothesis against Grafana. Read this file at Step 8, when Grafana is the available platform. Reach for it only once you already hold a specific code-level hypothesis and something concrete to look for. This step corroborates a hypothesis, and it does not explore.

## Loading the tools

The `mcp__grafana__*` tools can be deferred. Load the ones you need with `ToolSearch` when they are not callable. These are the core query tools:

- `query_loki_logs` searches logs, in LogQL.
- `query_prometheus` queries metrics, in PromQL.
- `tempo_traceql-search` searches distributed traces, in TraceQL.

Call `list_datasources` first when you do not already know the relevant datasource UID. Logs, metrics, and traces usually live in separate datasources.

## What to query

Look for the specific error, timeout, or pattern that the issue describes:
- **Logs, in Loki**: the exact error message, or a request path from your hypothesis, scoped to the relevant service label and time range.
- **Metrics, in Prometheus**: an error-rate or latency series for the endpoint you suspect, to confirm that the symptom is real and that it occurs now.
- **Traces, in Tempo**: a slow or failing trace for the specific operation, to confirm where time or errors accumulate along the call path.

## Retention window, which is the Step 8 gate

Hosted Loki and Tempo retention commonly runs 14 to 30 days. Check what applies to your setup when you are unsure. When the reported incident is older than the window, a log or trace lookup comes back empty, so skip it and save the round trip. Prometheus metrics often retain longer, so an aggregate error-rate check can still help after the raw logs age out.
