# Mining evidence attached to a work item

How to get a file attached to an issue and pull the answer out of it, without loading megabytes into your context. Read this at Step 8 when Step 2 listed an attachment worth opening.

Attached files are the highest-value evidence in a triage and the easiest to overlook: nobody links them from the comment that needed them, and a thread often keeps asking for a capture that has been sitting on the issue for weeks. They are also the only runtime evidence that survives past a log backend's retention window.

## Downloading

The tracker adapter has the authenticated call — use it rather than assembling your own request. In particular, don't read the CLI's credential file to build a `curl`: a tool that already holds the session almost always exposes a raw authenticated passthrough (for Jira's `twg`, that is `twg api`), which keeps the secret out of your context and out of your shell history.

Write the file to the scratchpad directory, not the user's project.

## Size discipline

Check the size from Step 2's metadata before you touch the file. Anything past a few hundred KB should never be read whole — a browser HAR from a single page load is routinely 5–20 MB, and reading one will evict everything else you have established. Two safe patterns:

- Project the few fields that matter with `jq`, `grep`, or `python`, and read only the projection.
- Hand the file path to a subagent with a specific question, and have it return the extracted lines rather than the file.

Prefer `jq` over `grep` on structured formats. `grep` on minified JSON matches one enormous line and re-expands the payload you were trying to avoid.

## HAR files

A HAR is a JSON envelope with `log.entries[]` (one object per request) and `log.pages[]` (one per top-level navigation). Start with a projection of the requests whose URL matches the flow under investigation:

```
jq -r '.log.entries[]
  | select(.request.url | test("<path-of-interest>"))
  | "\(.startedDateTime) \(.request.method) st=\(.response.status) t=\(.time|floor)ms init=\(._initiator.type) \(.request.url[0:140])"' capture.har
```

Five fields decide most cases:

- **`response.status`** — a status of `0` means the request never completed. That is a cancelled or failed navigation, not a server error, and it is invisible in server-side logs.
- **`timings`** — where the time actually went. Time concentrated in `blocked` with `send`/`wait`/`receive` at zero and no `serverIPAddress` means the request was never dispatched to the network at all, so no server-side log exists for it. Compare against a working request in the same capture to establish what normal looks like.
- **`_initiator.type`** — `script` vs `parser` vs a user action distinguishes "the page re-navigated itself" from "the browser fetched a subresource".
- **`log.pages[]`** — the top-level URLs and their timestamps reconstruct what the person was actually doing (opened X, went back, reopened X), which is what you compare against the reported reproduction steps.
- **`request.queryString`** — project a specific parameter across entries to spot a credential or one-time token being replayed:

```
jq -r '.log.entries[] | select(.request.url | test("<endpoint>"))
  | "\(.startedDateTime) st=\(.response.status) tok=\(.request.queryString[]? | select(.name=="<param>") | .value)"' capture.har
```

Two requests carrying the same single-use value, or a redirect target that never dispatched, show up in exactly these fields.

`response.content.text` holds response bodies when the capture included them — useful for reading the exact error payload the user received, and worth checking before you infer that payload from code.

## Other formats

- **Log or CSV exports** — count matches before reading any (`grep -c`), then read with bounded context around the interesting lines.
- **Screenshots and images** — `Read` renders them directly; this is the cheapest way to confirm what the user actually saw.
- **Screen recordings** (`.mov`, `.mp4`) — you cannot watch these. Say so plainly rather than writing around it, and get what you need from a HAR, a log, or by asking the reporter what happens at a given point. An unwatched recording is not evidence you can cite.
- **Archives and packages** (`.zip`, a SCORM export) — list the contents first and extract only the entry you need, rather than unpacking everything.

## Quoting it in the comment

Quote the smallest set of entries that carries the conclusion, and strip the rows that don't participate — analytics beacons, fonts, images, unrelated third-party calls. A trimmed six-line request timeline showing a duplicate call and a dead redirect is an argument; the raw capture pasted in is a data dump the reader has to re-derive the argument from.

Reconstructing a timeline is usually worth more than any single field: request, status, and elapsed time in order, annotated with what each step means, lets a reader follow the failure without opening the file.
