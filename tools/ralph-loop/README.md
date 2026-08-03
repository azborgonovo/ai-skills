# ralph-loop

**Status: Trial** — usable, still being validated. See [tools/README.md](../README.md) for what that means.

Re-runs a prompt file through the [Claude Code](https://code.claude.com) CLI, in
headless mode, over and over, until the agent signals it's done. Named after
the ["Ralph Wiggum" technique](https://ghuntley.com/ralph/): a dumb `while`
loop around an agent is often enough to grind through a queue of well-defined
work — one subtask per iteration — without a human driving each step.

## Requirements

- Python 3.10+
- The `claude` CLI on `PATH`, already authenticated

## Usage

```bash
python tools/ralph-loop/ralph_loop.py [prompt_file] [sentinel] [max_iters]
```

| Argument      | Default            | Meaning                                                          |
|---------------|---------------------|-------------------------------------------------------------------|
| `prompt_file` | `prompt.md`         | Path to the prompt fed to `claude -p` on every iteration.        |
| `sentinel`    | `FINISHED`          | Exact final response that stops the loop (see below).            |
| `max_iters`   | `10`                | Safety cap so a stuck loop can't run forever.                    |

Example:

```bash
python tools/ralph-loop/ralph_loop.py my-prompt.md FINISHED 20
```

Output streams live: thinking, tool calls, tool results, and a per-iteration cost/turn summary — colorized when stdout is a TTY, plain otherwise (or when `NO_COLOR` is set).

The loop stops when any of these happens:

- Claude's final response for an iteration contains a line that is *exactly* the sentinel string (a lead-in sentence before that line is fine — models don't reliably print the sentinel with nothing else, so the check matches per line rather than requiring the whole response to be just the sentinel)
- `max_iters` iterations ran without that happening
- the `claude` process exits non-zero

## Writing a prompt for the loop

Each iteration re-sends the same prompt file from scratch — Claude has no memory of prior iterations beyond what it left behind in the world (commits, tracker state, files). So the prompt must:

1. Find the next unit of work itself (e.g. query a tracker for the next `"To Do"` item) rather than assume it's continuing a specific task.
2. Print the sentinel string *exactly*, and stop, once there is no more work — that's the loop's only way to know it's done.

See [`jira-tasks-example.md`](jira-tasks-example.md) for a full example that pulls Jira subtasks one at a time, implements each on its own branch, opens a draft MR, and prints `FINISHED` once the tracker has nothing left in `"To Do"`.

### Best Practices for token-efficiency

Because each iteration is a fresh `claude -p` process with no memory of the last one, anything the prompt doesn't hand it directly gets rediscovered from scratch, every time. A few habits keep that rediscovery cheap:

- **Only name a skill/tool you have confirmed exists.** A prompt step that says "use the `foo-cli` skill" costs nothing when `foo-cli` is configured, but if it isn't, every single iteration wastes a call discovering that and falling back to something else.
- **Inline static facts instead of rediscovering them.** Tracker site IDs, your tracker username, repo-host org names, and similar constants don't change between iterations — put them directly in the prompt instead of making the agent look them up each time.
