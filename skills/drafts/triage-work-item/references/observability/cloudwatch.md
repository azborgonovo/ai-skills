# Observability adapter: AWS CloudWatch

Mechanics for corroborating a hypothesis against AWS CloudWatch. Read this at Step 8 when CloudWatch is the available platform. Reach for it only once you already have a specific code-level hypothesis and something concrete to look for — this is corroboration, not exploration.

**Status**: verified against the installed `aws` CLI (v2.36.8) — all four commands and their required parameters (`--query-id`; `--metric-data-queries/--start-time/--end-time`; etc.) are confirmed by the CLI's own client-side validation and match the official reference, including the per-command time-unit difference: `logs start-query` and `xray get-trace-summaries` take epoch seconds, while `cloudwatch get-metric-data` takes ISO 8601 timestamps. The live API round-trip is still untested — no AWS credentials are configured on this machine — so run `aws sts get-caller-identity` first, then one real query, before trusting output.

## Tooling

Use the `aws` CLI over Bash. If an AWS MCP connector is available instead, discover it with `ToolSearch` (e.g. `cloudwatch`) and prefer it. Set the region explicitly (`--region <r>`) or via `AWS_REGION` — CloudWatch data is per-region, and querying the wrong region returns empty results that look like "no data" rather than an error.

## Logs (CloudWatch Logs Insights)

Log queries are asynchronous: start a query, then poll for results.

```
aws logs start-query \
  --log-group-name <group> \
  --start-time <epoch-seconds> --end-time <epoch-seconds> \
  --query-string 'fields @timestamp, @message | filter @message like /<error-or-pattern>/ | sort @timestamp desc | limit 50'

aws logs get-query-results --query-id <id-from-start-query>
```

Scope to the log group for the suspected service. Logs Insights uses its own query syntax (not LogQL) — `filter`, `parse`, `stats`, `fields`.

## Metrics

```
aws cloudwatch get-metric-data \
  --start-time <iso8601> --end-time <iso8601> \
  --metric-data-queries '<json: namespace, metric name, dimensions, stat, period>'
```

Use this for an error-rate or latency series on the suspected resource to confirm the symptom is real and currently occurring. `get-metric-statistics` is the simpler single-metric alternative.

## Traces (AWS X-Ray)

Distributed traces live in X-Ray, not CloudWatch Logs:

```
aws xray get-trace-summaries --start-time <epoch> --end-time <epoch> --filter-expression '<expr>'
```

Use it to find a slow or failing trace for the specific operation and see where time or errors accumulate along the call path.

## Retention window (Step 8 gate)

CloudWatch retention differs from hosted Loki/Tempo in a way that matters for the age gate:
- **Logs**: retention is set per log group and defaults to "never expire," but many groups are configured to a fixed window (30/90 days). Check the log group's retention before assuming an old incident's logs are gone — they may still be there.
- **Metrics**: retained on a rolling 15-month schedule (with coarser resolution as data ages), so aggregate error-rate/latency checks stay useful long after raw logs would have aged out on other platforms.
- **X-Ray traces**: retained ~30 days — apply the same skip-if-older gate as trace lookups on other platforms.
