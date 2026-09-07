"""Shared lookup and call-recording helpers for the stub host CLIs.

The stubs serve canned JSON from the `<case>/api/` tree a scaffold copies in. They open no socket, so a
run cannot reach a real host. Every write call is appended to `posted-calls.log` beside the
bin/ directory that holds these stubs, and answered with a canned success.
"""

import json
import os
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
FIXTURE_ROOT = BIN.parent


def case_dirs():
    """Every case fixture directory that carries an api/ tree."""
    return [p for p in sorted(FIXTURE_ROOT.iterdir())
            if p.is_dir() and p.name != "bin" and (p / "api").is_dir()]


def sanitize(path):
    """Turn an API path into the file name that build_fixture.py wrote."""
    key = path.split("?")[0].strip("/")
    key = key.replace("%2F", "/").replace("%2f", "/")
    return key.replace("/", "_")


def find(name, suffix=".json"):
    """Return the first canned response file called <name><suffix>."""
    for case in case_dirs():
        candidate = case / "api" / f"{name}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def find_glob(pattern):
    """Return the only canned response matching a glob, when exactly one matches."""
    hits = []
    for case in case_dirs():
        hits.extend(sorted((case / "api").glob(pattern)))
    return hits[0] if len(hits) == 1 else None


def log_path():
    # Anchored to the stub, not to the caller. A run reviews from inside the
    # clone or a worktree, so a cwd-relative log would scatter across
    # directories and the graders that read it would find an empty file.
    return Path(os.environ.get("PR_REVIEW_CALL_LOG") or BIN.parent / "posted-calls.log")


def serve(path, tool):
    """Print a canned read response, or fail loudly when none exists."""
    if path is None:
        return None
    sys.stdout.write(path.read_text())
    print(f"[stub {tool}] served {path}", file=sys.stderr)
    return 0


def missing(tool, what, looked_for):
    print(f"[stub {tool}] no fixture for {what} (looked for {looked_for})",
          file=sys.stderr)
    return 1


def record(tool, action, target, body=None):
    """Append a write call to the log and answer it with a canned success."""
    log = log_path()
    previous = 0
    if log.exists():
        previous = len([line for line in log.read_text().splitlines() if line.strip()])
    entry = {
        "tool": tool,
        "action": action,
        "target": target,
        "argv": sys.argv[1:],
        "body": body,
        "sent_to_network": False,
    }
    with log.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    print(f"[stub {tool}] recorded {action} {target} in {log}. Nothing was sent.",
          file=sys.stderr)
    return previous + 1


def canned_write_response(new_id, target=""):
    return {
        "id": new_id,
        "iid": new_id,
        "line_code": "fixture_line_code",
        "state": "PENDING",
        "html_url": f"https://fixture.invalid/{target.strip('/')}#note_{new_id}",
        "web_url": f"https://fixture.invalid/{target.strip('/')}#note_{new_id}",
        "body": "recorded by the eval stub",
    }


def read_stdin_body(argv):
    """Read a request body from stdin when the caller passed --input -."""
    if "--input" not in argv:
        return None
    value = argv[argv.index("--input") + 1] if argv.index("--input") + 1 < len(argv) else "-"
    if value == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(value).read_text()
    try:
        return json.loads(raw)
    except ValueError:
        return raw
