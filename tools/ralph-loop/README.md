# ralph-loop

**Status: Trial** — usable, still under validation. See [README.md](../../README.md) for what that means.

Sends a prompt file to the [Claude Code](https://code.claude.com) CLI in headless mode, again and again, until the
agent signals that the work is done. The name comes from the ["Ralph Wiggum" technique](https://ghuntley.com/ralph/).
A plain `while` loop around an agent is often enough to work through a queue of well-defined work, one subtask per
iteration. No person drives each step.

## Requirements

- Python 3.10+
- The `claude` CLI on `PATH`, already authenticated

## Usage

```bash
python tools/ralph-loop/ralph_loop.py [prompt_file] [sentinel] [max_iters]
```

| Argument      | Default            | Meaning                                                          |
|---------------|---------------------|-------------------------------------------------------------------|
| `prompt_file` | `prompt.md`         | Path to the prompt that goes to `claude -p` on every iteration.  |
| `sentinel`    | `FINISHED`          | Exact final response that stops the loop (see below).            |
| `max_iters`   | `10`                | Safety cap, so a stuck loop cannot run forever.                  |

Example:

```bash
python tools/ralph-loop/ralph_loop.py my-prompt.md FINISHED 20
```

The output streams live: the thinking, the tool calls, the tool results, and a summary of cost and turns for each
iteration. The output has color when stdout is a TTY, and no color otherwise, or when `NO_COLOR` is set.

The loop stops on any of these events:

- The final response of an iteration holds a line that is *exactly* the sentinel string. A lead-in sentence before
  that line is acceptable, because a model does not reliably print the sentinel alone. For that reason the check reads
  each line on its own, instead of the whole response.
- The loop ran `max_iters` iterations and no sentinel arrived.
- The `claude` process exits with a non-zero code.

## Writing a prompt for the loop

Each iteration sends the same prompt file again, from the start. Claude remembers nothing from an earlier iteration,
except what it left behind in the world, such as commits, tracker state, and files. The prompt must therefore do two
things:

1. Find the next unit of work itself. For example, query the tracker for the next `"To Do"` item. The prompt must not
   assume that it continues one specific task.
2. Print the sentinel string *exactly*, and stop, when no work is left. The sentinel is the only signal that tells the
   loop that the work is done.

For a full example, see [`jira-tasks-example.md`](jira-tasks-example.md). It pulls Jira subtasks one at a time. It
implements each one on its own branch, and opens a draft merge request for it. It prints `FINISHED` when the tracker
holds nothing more in `"To Do"`.

### Best practices for token efficiency

Each iteration is a fresh `claude -p` process with no memory of the last one. Anything that the prompt does not hand
to the agent directly, the agent finds again from scratch, every time. Two habits keep that cost low:

- **Name a skill or a tool only after you confirm that it exists.** A prompt step that says "use the `foo-cli` skill"
  costs nothing when `foo-cli` is configured. When it is absent, every iteration wastes a call to discover that, and
  then falls back to something else.
- **Put static facts in the prompt.** Tracker site IDs, your tracker username, the org name of the repository host,
  and similar constants do not change between iterations. Write them into the prompt, instead of a lookup on every
  iteration.
