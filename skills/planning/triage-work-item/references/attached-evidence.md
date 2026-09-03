# Mining evidence attached to a work item

How to get a file attached to an issue, and how to pull the answer out of it, without loading megabytes into your context. Read this file at Step 8, when Step 2 listed an attachment worth opening.

An attached file is the highest-value evidence in a triage, and the easiest to overlook. Nobody links it from the comment that needed it. A thread often keeps asking for a capture that has sat on the issue for weeks. An attachment is also the only runtime evidence that survives past the retention window of a log backend.

## Downloading

The tracker adapter holds the authenticated call, so use it instead of assembling your own request. Do not read the credential file of a CLI to build a `curl` command. A tool that already holds the session almost always exposes a raw authenticated passthrough, which for the `twg` CLI of Jira is `twg api`. The passthrough keeps the secret out of your context and out of your shell history.

Write the file to the scratchpad directory, and not into the user's project.

## Size discipline

Check the size from the Step 2 metadata before you touch the file. Never read a file past a few hundred KB whole. A browser HAR from a single page load routinely runs 5 MB to 20 MB, and reading one evicts everything else that you established. Two patterns are safe:

- Project the few fields that matter with `jq`, `grep`, or `python`, and read only the projection.
- Hand the file path to a subagent with a specific question, and have it return the extracted lines rather than the file.

Prefer `jq` over `grep` on a structured format. `grep` on minified JSON matches one enormous line, and it re-expands the payload that you were trying to avoid.

## HAR files

A HAR file is a JSON envelope with `log.entries[]`, which holds one object per request, and `log.pages[]`, which holds one object per top-level navigation. Start with a projection of the requests whose URL matches the flow under investigation:

```
jq -r '.log.entries[]
  | select(.request.url | test("<path-of-interest>"))
  | "\(.startedDateTime) \(.request.method) st=\(.response.status) t=\(.time|floor)ms init=\(._initiator.type) \(.request.url[0:140])"' capture.har
```

Five fields decide most cases:

- **`response.status`**: a status of `0` means that the request never completed. That is a cancelled or failed navigation, and not a server error, so it is invisible in the server-side logs.
- **`timings`**: where the time actually went. Time concentrated in `blocked`, with `send`, `wait`, and `receive` at zero and no `serverIPAddress`, means that the browser never dispatched the request to the network. So no server-side log exists for it. Compare against a working request in the same capture, to establish what normal looks like.
- **`_initiator.type`**: the values `script`, `parser`, and a user action distinguish "the page re-navigated itself" from "the browser fetched a subresource".
- **`log.pages[]`**: the top-level URLs and their timestamps reconstruct what the person was doing, such as opened X, went back, reopened X. That is what you compare against the reported reproduction steps.
- **`request.queryString`**: project a specific parameter across entries, to spot a credential or a one-time token replayed:

```
jq -r '.log.entries[] | select(.request.url | test("<endpoint>"))
  | "\(.startedDateTime) st=\(.response.status) tok=\(.request.queryString[]? | select(.name=="<param>") | .value)"' capture.har
```

Two requests that carry the same single-use value, and a redirect target that never dispatched, show up in exactly these fields.

`response.content.text` holds the response bodies when the capture included them. Use it to read the exact error payload that the user received, and check it before you infer that payload from the code.

## Other formats

- **A log or CSV export**: count the matches before you read any of them, with `grep -c`, then read with bounded context around the interesting lines.
- **A screenshot or image**: `Read` renders it directly, and this is the cheapest way to confirm what the user saw.
- **A screen recording**, such as a `.mov` or `.mp4` file: you cannot watch it. Say so plainly instead of writing around it. Get what you need from a HAR, from a log, or by asking the reporter what happens at a given point. A recording that nobody watched is not evidence that you can cite.
- **An archive or package**, such as a `.zip` file or a SCORM export: list the contents first, and extract only the entry that you need, rather than unpacking everything.

## Quoting it in the comment

Quote the smallest set of entries that carries the conclusion. Strip the rows that take no part, such as analytics beacons, fonts, images, and unrelated third-party calls. A trimmed six-line request timeline that shows a duplicate call and a dead redirect is an argument. The raw capture pasted in is a data dump, and the reader has to re-derive the argument from it.

Reconstructing a timeline is usually worth more than any single field. Give the request, the status, and the elapsed time in order, annotated with what each step means. Then a reader can follow the failure without opening the file.
