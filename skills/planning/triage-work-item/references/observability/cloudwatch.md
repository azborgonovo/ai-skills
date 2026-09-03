# Observability adapter: AWS CloudWatch

Mechanics for corroborating a hypothesis against AWS CloudWatch. Read this file at Step 8, when CloudWatch is the available platform. Reach for it only once you already hold a specific code-level hypothesis and something concrete to look for. This step corroborates a hypothesis, and it does not explore.

**Status**: verified against the installed `aws` CLI, version 2.36.8. The client-side validation of the CLI confirms all four commands and their required parameters, such as `--query-id`, and the trio `--metric-data-queries`, `--start-time`, and `--end-time`. They match the official reference. That includes the per-command time-unit difference: `logs start-query` and `xray get-trace-summaries` take epoch seconds, and `cloudwatch get-metric-data` takes ISO 8601 timestamps. The live API round-trip is untested, because this machine has no AWS credentials configured. Run `aws sts get-caller-identity` first, then one real query, before you trust the output.

## Tooling

Use the `aws` CLI over Bash. When an AWS MCP connector is available instead, discover it with `ToolSearch`, for example with the keyword `cloudwatch`, and prefer it. Set the region explicitly with `--region <r>`, or through `AWS_REGION`. CloudWatch data is per-region, and a query against the wrong region returns empty results that look like "no data" rather than an error.

## Logs, through CloudWatch Logs Insights

A log query is asynchronous. Start the query, then poll for its results.

```
aws logs start-query \
  --log-group-name <group> \
  --start-time <epoch-seconds> --end-time <epoch-seconds> \
  --query-string 'fields @timestamp, @message | filter @message like /<error-or-pattern>/ | sort @timestamp desc | limit 50'

aws logs get-query-results --query-id <id-from-start-query>
```

Scope the query to the log group of the suspected service. Logs Insights uses its own query syntax, which is not LogQL. The keywords are `filter`, `parse`, `stats`, and `fields`.

## Metrics

```
aws cloudwatch get-metric-data \
  --start-time <iso8601> --end-time <iso8601> \
  --metric-data-queries '<json: namespace, metric name, dimensions, stat, period>'
```

Use this command for an error-rate or latency series on the suspected resource, to confirm that the symptom is real and that it occurs now. `get-metric-statistics` is the simpler alternative for a single metric.

## Traces, through AWS X-Ray

Distributed traces live in X-Ray, and not in CloudWatch Logs:

```
aws xray get-trace-summaries --start-time <epoch> --end-time <epoch> --filter-expression '<expr>'
```

Use it to find a slow or failing trace for the specific operation, and to see where time or errors accumulate along the call path.

## Retention window, which is the Step 8 gate

CloudWatch retention differs from hosted Loki and Tempo in a way that matters for the age gate:
- **Logs**: retention is set per log group, and it defaults to "never expire". Many groups are configured to a fixed window of 30 or 90 days. Check the retention of the log group before you assume that the logs of an old incident are gone, because they can still be there.
- **Metrics**: retained on a rolling 15-month schedule, at a coarser resolution as the data ages. An aggregate error-rate or latency check stays useful long after raw logs age out on another platform.
- **X-Ray traces**: retained for roughly 30 days. Apply the same skip-if-older gate as for a trace lookup on another platform.
