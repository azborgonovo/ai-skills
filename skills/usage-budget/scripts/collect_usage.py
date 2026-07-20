#!/usr/bin/env python3
"""Record per-turn token usage from the session transcript.

Claude Code hooks receive no token or cost data, but every hook payload carries
`transcript_path`, and the transcript JSONL records a `usage` block per assistant
message. This script reads that transcript and writes one JSON file per session
describing what each turn actually cost.

Wired to two events (see ../hooks/hooks.json):

  Stop              -> rewrite this session's record now that the turn is complete
  UserPromptSubmit  -> optionally emit a one-line burn-rate notice as context

Everything here is *measurement*, not prediction. It records what was spent so
that the question "does prompt intent predict cost?" can be answered from real
data later, rather than assumed now.
"""

import json
import os
import sys
import time
from pathlib import Path

# Cache reads are billed at roughly a tenth of fresh input, so summing all token
# fields equally would badly overstate cost. This weight is a proxy for relative
# spend, not a billing figure -- treat the output as "weighted tokens", not money.
CACHE_READ_WEIGHT = 0.1

PROMPT_EXCERPT_CHARS = 200

DEFAULTS = {
    # Weighted tokens in the rolling window before a burn-rate line is injected.
    # Set to 0 to disable the notice and collect silently.
    "warn_at_weighted": 2_000_000,
    "window_hours": 5,
}


def data_dir() -> Path:
    return Path(os.environ.get("USAGE_BUDGET_DIR") or (Path.home() / ".claude" / "usage-budget"))


def load_config() -> dict:
    config = dict(DEFAULTS)
    path = data_dir() / "config.json"
    try:
        config.update(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return config


def weighted_tokens(usage: dict) -> float:
    return (
        usage.get("output_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("input_tokens", 0)
        + CACHE_READ_WEIGHT * usage.get("cache_read_input_tokens", 0)
    )


# Harness-injected user-role entries that continue the current turn rather than
# starting a new one. Counting them as prompts would split one turn's cost across
# several phantom ones and attribute it to text the user never typed.
INJECTED_PREFIXES = ("<task-notification>", "<system-reminder>", "<local-command-")


def is_user_prompt(entry: dict) -> bool:
    """True for a real typed prompt, as opposed to a tool result or injected entry."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
            return False
        content = " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if not isinstance(content, str) or not content.strip():
        return False
    return not content.lstrip().startswith(INJECTED_PREFIXES)


def prompt_text(entry: dict) -> str:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return " ".join((content or "").split())[:PROMPT_EXCERPT_CHARS]


def parse_turns(transcript_path: str) -> list:
    """Split a transcript into turns, each carrying its prompt and measured cost.

    A turn runs from one typed prompt to the next; every assistant message in
    between counts toward it, including subagent sidechains, since those are
    real spend attributable to the prompt that triggered them. Usage lines repeat
    per request in the transcript, so `requestId` deduplicates them.
    """
    turns = []
    seen_requests = set()
    current = None

    try:
        handle = open(transcript_path, encoding="utf-8")
    except OSError:
        return turns

    with handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue

            if is_user_prompt(entry):
                if current is not None:
                    turns.append(current)
                current = {
                    "index": len(turns),
                    "prompt_excerpt": prompt_text(entry),
                    "prompt_chars": len(str((entry.get("message") or {}).get("content", ""))),
                    "started_at": entry.get("timestamp"),
                    "weighted": 0.0,
                    "output_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "messages": 0,
                }
                continue

            if current is None:
                continue

            usage = (entry.get("message") or {}).get("usage")
            request_id = entry.get("requestId")
            if not usage or request_id in seen_requests:
                continue
            seen_requests.add(request_id)
            current["weighted"] += weighted_tokens(usage)
            current["output_tokens"] += usage.get("output_tokens", 0)
            current["cache_read_input_tokens"] += usage.get("cache_read_input_tokens", 0)
            current["messages"] += 1
            current["ended_at"] = entry.get("timestamp")

    if current is not None:
        turns.append(current)
    return turns


def record_session(payload: dict) -> None:
    session_id = payload.get("session_id")
    transcript = payload.get("transcript_path")
    if not session_id or not transcript:
        return

    turns = parse_turns(transcript)
    if not turns:
        return

    sessions = data_dir() / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    record = {
        "session_id": session_id,
        "project": Path(payload.get("cwd") or ".").name,
        "cwd": payload.get("cwd"),
        "updated_at": time.time(),
        "turns": turns,
    }
    # Rewritten in full on every Stop, so re-running is idempotent and a
    # resumed or compacted session self-corrects rather than double-counting.
    target = sessions / f"{session_id}.json"
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(target)


def window_totals(window_hours: float) -> tuple:
    cutoff = time.time() - window_hours * 3600
    total = 0.0
    turn_costs = []
    sessions = data_dir() / "sessions"
    if not sessions.is_dir():
        return 0.0, []
    for path in sessions.glob("*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for turn in record.get("turns", []):
            total += turn.get("weighted", 0.0)
            turn_costs.append(turn.get("weighted", 0.0))
    return total, turn_costs


def burn_rate_notice(payload: dict) -> None:
    """Emit a measured burn-rate line, only once past the configured threshold.

    Deliberately silent below the threshold: this hook runs on every prompt, and
    spending context on a usage notice every turn to report usage would be
    self-defeating.
    """
    config = load_config()
    threshold = config.get("warn_at_weighted", 0)
    if not threshold:
        return

    record_session(payload)  # fold in the turn that just finished
    total, _ = window_totals(config.get("window_hours", 5))
    if total < threshold:
        return

    hours = config.get("window_hours", 5)
    message = (
        f"Usage budget: ~{total / 1_000_000:.1f}M weighted tokens in the last {hours}h "
        f"(threshold {threshold / 1_000_000:.1f}M). This is measured consumption, not "
        f"remaining quota -- run /usage for actual limits."
    )
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": message,
            }
        },
        sys.stdout,
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0

    if payload.get("hook_event_name") == "UserPromptSubmit":
        burn_rate_notice(payload)
    else:
        record_session(payload)
    return 0


if __name__ == "__main__":
    # A collector must never break the session it observes: swallow everything.
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
