#!/usr/bin/env python3
"""Run Claude Code in a loop against a prompt file (a "Ralph Wiggum" loop).

Each iteration feeds the prompt file to the `claude` CLI in headless mode and
streams its thinking, tool calls, and tool results back to your terminal in
real time. The loop stops as soon as one of these happens:

  - Claude's final response for an iteration contains a line that is
    exactly --sentinel (the prompt should instruct it to print this once
    there is no work left; a lead-in sentence before the sentinel line is
    tolerated, since models don't reliably omit one)
  - --max-iters iterations have run without a match (safety cap)
  - the `claude` process exits non-zero

This is a Python port of a zsh + jq script (see the repo history / gist this
was based on) kept for portability: no zsh or jq dependency, just Python 3
and the `claude` CLI on PATH.

Usage:
    python tools/ralph-loop/ralph_loop.py [prompt_file] [sentinel] [max_iters]

Defaults: prompt_file=ralph-prompt.md, sentinel=FINISHED, max_iters=10.

See tools/ralph-loop/README.md and jira-tasks-example.md for how to write a
prompt that drives this loop.
"""

import argparse
import json
import os
import re
import subprocess
import sys

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

RESET = "\x1b[0m"
DIM = "\x1b[90m"
BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"


def format_todo(todo: dict) -> str:
    status = todo.get("status")
    if status == "completed":
        marker = f"{GREEN}✔ "
    elif status == "in_progress":
        marker = f"{YELLOW}◐ "
    else:
        marker = f"{DIM}○ "
    return "   " + marker + (todo.get("content") or "") + RESET


def format_tool_use(block: dict) -> str:
    name = block.get("name", "")
    if name == "TodoWrite":
        todos = (block.get("input") or {}).get("todos") or []
        body = "\n".join(format_todo(t) for t in todos)
        return f"\n{CYAN}{BOLD}● Todos{RESET}\n{body}\n"

    tool_input = block.get("input") or {}
    preview = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("command")
        or tool_input.get("pattern")
        or tool_input.get("url")
        or json.dumps(tool_input)
    )
    preview = str(preview).replace("\n", " ")[:100]
    return f"\n{CYAN}{BOLD}● {name}{RESET}{CYAN} {preview}{RESET}\n"


def format_stream_event(event: dict) -> str:
    inner = event.get("event") or {}
    inner_type = inner.get("type")

    if inner_type == "content_block_delta":
        delta = inner.get("delta") or {}
        if delta.get("type") == "text_delta":
            return delta.get("text", "")
        if delta.get("type") == "thinking_delta":
            return f"{DIM}{delta.get('thinking', '')}{RESET}"
        return ""

    if inner_type == "content_block_start":
        block_type = (inner.get("content_block") or {}).get("type", "")
        if block_type == "thinking":
            return f"\n{DIM}{ITALIC}· thinking ·{RESET}\n"
        if block_type == "text":
            return "\n"
        return ""

    return ""


def format_assistant(event: dict) -> str:
    blocks = (event.get("message") or {}).get("content") or []
    return "".join(format_tool_use(b) for b in blocks if b.get("type") == "tool_use")


def format_tool_result_content(content) -> str:
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    if isinstance(content, str):
        return content
    return ""


def format_user(event: dict) -> str:
    out = []
    for block in (event.get("message") or {}).get("content") or []:
        if block.get("type") != "tool_result":
            continue
        text = format_tool_result_content(block.get("content")).replace("\n", " ")
        ellipsis = "…" if len(text) > 90 else ""
        out.append(f"{DIM}   ⎿ {text[:90]}{ellipsis}{RESET}\n")
    return "".join(out)


def format_result(event: dict) -> str:
    turns = event.get("num_turns") or 0
    cost = event.get("total_cost_usd") or 0
    duration_s = (event.get("duration_ms") or 0) / 1000
    return (
        f"\n{GREEN}{BOLD}✔ {event.get('subtype') or 'done'}{RESET} {DIM}· "
        f"{turns} turns · ${cost} · {duration_s}s{RESET}\n"
    )


def format_event(event: dict) -> str:
    event_type = event.get("type")
    if event_type == "stream_event":
        return format_stream_event(event)
    if event_type == "assistant":
        return format_assistant(event)
    if event_type == "user":
        return format_user(event)
    if event_type == "result":
        return format_result(event)
    return ""


def run_iteration(claude_bin: str, prompt_path: str, emit) -> tuple[int, str | None]:
    """Run one `claude` pass over the prompt file, streaming formatted output via emit.

    Returns (exit_code, last_result_text).
    """
    with open(prompt_path, "rb") as prompt_stream:
        proc = subprocess.Popen(
            [
                claude_bin,
                "-p",
                "--permission-mode=auto",
                "--output-format",
                "stream-json",
                "--verbose",
                "--include-partial-messages",
            ],
            stdin=prompt_stream,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        last_result = None
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            emit(format_event(event))
            if event.get("type") == "result":
                last_result = event.get("result")

        proc.wait()

    return proc.returncode, last_result


def has_sentinel_line(text: str, sentinel: str) -> bool:
    """True if any line of text, once stripped, is exactly the sentinel.

    A whole-message equality check is too strict: models don't reliably
    omit a lead-in sentence before the sentinel, so exact-message matches
    were missing valid stop signals and running extra, redundant iterations.
    Matching per-line (not substring) keeps false positives like "not
    FINISHED yet" from tripping it.
    """
    return any(line.strip() == sentinel for line in (text or "").splitlines())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prompt_file", nargs="?", default="ralph-prompt.md")
    parser.add_argument("sentinel", nargs="?", default="FINISHED")
    parser.add_argument("max_iters", nargs="?", type=int, default=10)
    parser.add_argument(
        "--claude-bin",
        default=os.environ.get("RALPH_CLAUDE_BIN", "claude"),
        help="Path to the claude CLI (default: $RALPH_CLAUDE_BIN or 'claude' on PATH).",
    )
    args = parser.parse_args()

    if not os.access(args.prompt_file, os.R_OK):
        print(f"Prompt file not found or not readable: {args.prompt_file}", file=sys.stderr)
        return 1

    color_enabled = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

    def emit(text: str) -> None:
        if not text:
            return
        sys.stdout.write(text if color_enabled else ANSI_RE.sub("", text))
        sys.stdout.flush()

    print(f'prompt: {args.prompt_file} | sentinel: "{args.sentinel}" | max iters: {args.max_iters}')

    iteration = 0
    while iteration < args.max_iters:
        iteration += 1
        emit(f"\n{MAGENTA}{BOLD}===== Iteration {iteration} ====={RESET}\n")

        try:
            exit_code, last_result = run_iteration(args.claude_bin, args.prompt_file, emit)
        except FileNotFoundError:
            print(f"claude binary not found: {args.claude_bin}", file=sys.stderr)
            return 1

        print()

        if exit_code != 0:
            print(f"claude exited non-zero ({exit_code}); stopping.", file=sys.stderr)
            break

        if has_sentinel_line(last_result, args.sentinel):
            print(f'Got sentinel ("{args.sentinel}") — stopping loop.')
            break
    else:
        print(f'Hit max_iters ({args.max_iters}) without "{args.sentinel}".', file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
