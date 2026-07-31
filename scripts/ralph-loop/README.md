# ralph-loop

Re-runs a prompt file through the [Claude Code](https://code.claude.com) CLI, in
headless mode, over and over, until the agent signals it's done. Named after
the ["Ralph Wiggum" technique](https://ghuntley.com/ralph/): a dumb `while`
loop around an agent is often enough to grind through a queue of well-defined
work — one subtask per iteration — without a human driving each step.

## Requirements

- Python 3.10+
- The `claude` CLI on `PATH`, already authenticated
- Any skills your prompt references (e.g. a tracker CLI) installed and configured

## Usage

```bash
python scripts/ralph-loop/ralph_loop.py [prompt_file] [sentinel] [max_iters]
```

| Argument      | Default            | Meaning                                                          |
|---------------|---------------------|-------------------------------------------------------------------|
| `prompt_file` | `ralph-prompt.md`  | Path to the prompt fed to `claude -p` on every iteration.        |
| `sentinel`    | `FINISHED`          | Exact final response that stops the loop (see below).            |
| `max_iters`   | `10`                | Safety cap so a stuck loop can't run forever.                    |

Example:

```bash
python scripts/ralph-loop/ralph_loop.py my-prompt.md FINISHED 20
```

Output streams live: thinking, tool calls, tool results, and a per-iteration
cost/turn summary — colorized when stdout is a TTY, plain otherwise (or when
`NO_COLOR` is set).

The loop stops when any of these happens:

- Claude's final response for an iteration is *exactly* the sentinel string
- `max_iters` iterations ran without that happening
- the `claude` process exits non-zero

## Writing a prompt for the loop

Each iteration re-sends the same prompt file from scratch — Claude has no
memory of prior iterations beyond what it left behind in the world (commits,
tracker state, files). So the prompt must:

1. Find the next unit of work itself (e.g. query a tracker for the next `"To
   Do"` item) rather than assume it's continuing a specific task.
2. Print the sentinel string *exactly*, and stop, once there is no more work
   — that's the loop's only way to know it's done.

See [`prompt-example.md`](prompt-example.md) for a full example that pulls
Jira subtasks one at a time, implements each on its own branch, opens a
draft MR, and prints `FINISHED` once the tracker has nothing left in `"To
Do"`. It references skills (`jira-cli`, `glab-cli`) that aren't part of this
repository — swap in whatever tools fit your workflow.

## Why Python instead of the original zsh + jq

This started as a zsh script that shelled out to `claude` and reformatted its
`stream-json` output with a `jq` filter. This port keeps the same behavior
and terminal output but drops the zsh/jq dependency so it runs anywhere
Python does.
