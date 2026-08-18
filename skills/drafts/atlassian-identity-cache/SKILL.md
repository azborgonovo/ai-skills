---
name: atlassian-identity-cache
description: >
  Resolves and self-heals a local on-disk cache mapping Jira project-key prefixes to Atlassian
  cloud IDs, and cloud IDs to tracker account IDs, so calls into the Atlassian MCP tools
  (`getJiraIssue`, `searchJiraIssuesUsingJql`, `transitionJiraIssue`, etc.) skip re-resolving
  `cloudId`/`accountId` via `getAccessibleAtlassianResources`/`lookupJiraAccountId` on every
  run. Applies only when the Atlassian MCP tools are the backend — especially valuable for a
  prompt that starts from scratch on every invocation (e.g. a headless loop like ralph-loop) or
  one that may span more than one connected Atlassian site. Do NOT use when Atlassian's `twg`
  CLI is available: it carries the site and identity in `~/.config/twg/auth.conf`, so there is
  nothing left to resolve or cache.
---

# Atlassian identity cache

Two Atlassian facts get looked up over and over by anything that calls the Atlassian MCP tools: the `cloudId` for a Jira site, and the `accountId` for a tracker user on that site. Both are constants for a given site, so rediscovering them on every call — or every iteration, for something like a headless loop — is pure waste. This skill resolves them through a small on-disk cache that heals itself if it's ever wrong, instead of a flat single value that would silently break the moment more than one Atlassian site is in play.

## Precondition: is there anything to cache?

Check for Atlassian's Teamwork Graph CLI first: `command -v twg`, then `$HOME/.local/bin/twg` if the shell reports `command not found`.

If the binary is there, stop — this skill has nothing to add. `twg` stores the site, `cloud-id`, and `user-id` in `~/.config/twg/auth.conf` at login and refreshes the token on its own schedule, so every command already knows who and where it is. Drive the tracker through `twg` and skip the rest of this file.

Everything below applies to the Atlassian MCP path only.

## Cache files

- `$HOME/.claude/atlassian-cloud-ids.json` — `{ "<PROJECT-PREFIX>": "<cloudId>" }`
- `$HOME/.claude/atlassian-account-ids.json` — `{ "<cloudId>": "<accountId>" }`

Both are plain JSON maps. Treat a missing file as an empty map (`{}`), not an error — create it the first time you write to it.

Two older, singular files exist alongside these: `$HOME/.claude/atlassian-cloud-id` and `$HOME/.claude/atlassian-account-id`, each a single bare line holding one value. That is the legacy single-site form, and the `pr-review` skill still reads the cloud-id one directly. It cannot represent more than one site, which is the whole reason for the JSON maps here — so write the maps, and treat a singular file as a seed value for the map rather than a destination to keep in sync.

## Resolving a cloud ID for a task key

Given a task key like `PROJ-101`, the project-key prefix (`PROJ`) is everything before the `-`.

1. Look up the prefix in the cloud-ids map.
2. If it's there, use that `cloudId` directly for the tracker call you actually need to make — the call itself is the validation, so there's no separate check to pay for.
   - If the call succeeds, you're done.
   - If it fails as "issue not found" / "no permission" for that specific key, the cached value is stale: run **Resolve** below, overwrite the map entry with the result, then retry the original call once.
3. If the prefix isn't in the map at all, run **Resolve** directly.

**Resolve**: call `getAccessibleAtlassianResources` for the list of accessible sites.
- Exactly one site → that's the cloudId.
- More than one → retry the same tracker call against each candidate cloudId in turn; the first one that doesn't fail with "not found"/"no permission" is the answer.
- None succeed → none of the accessible sites hosts this task; stop and report that rather than guessing further.

Write the resolved `{prefix: cloudId}` pair into the cache — adding a new entry or overwriting the stale one — before moving on.

## Resolving an account ID for a cloud ID

1. Look up the cloudId in the account-ids map.
2. If it's there, use it.
3. If not, call `lookupJiraAccountId` with the tracker username and that cloudId, then write the `{cloudId: accountId}` pair into the cache.

There's no staleness case here analogous to the cloud-id one — a wrong account ID doesn't fail a call the way a wrong cloudId does, it just misattributes an action. Re-resolve this value deliberately if you have reason to think the identity behind it changed (e.g. a different user reconfigured the environment), rather than assuming a failed call means this one needs healing too.
