#!/usr/bin/env python3
"""Build the offline fixtures that the pr-review eval suite runs against.

Each case gets one directory under `evals/fixtures/`. That directory holds a bare
`origin.git`, a `clone` of it, and an `api/` tree of canned host responses. The stub
`glab`, `gh`, and `twg` executables under `evals/fixtures/bin/` read that `api/` tree,
so a run reaches no network at all.

The canned responses carry the real SHAs of the built repository, so this script writes
them after it builds the repository. Run it through `evals/fixtures/build.sh`.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

SOURCE_BRANCH = "feat/partial-refunds"
TARGET_BRANCH = "main"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Sam Dev",
    "GIT_AUTHOR_EMAIL": "sam@fixture.test",
    "GIT_AUTHOR_DATE": "2026-01-05T09:00:00+00:00",
    "GIT_COMMITTER_NAME": "Sam Dev",
    "GIT_COMMITTER_EMAIL": "sam@fixture.test",
    "GIT_COMMITTER_DATE": "2026-01-05T09:00:00+00:00",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}

# --- repository content ------------------------------------------------------

STANDARDS = """# Coding standards

These rules apply to every change in this repository.

- Every SQL statement binds its values as parameters. Never interpolate a value into
  SQL text.
- Money is a whole number of cents, held as an `int`. Never hold money as a `float`.
- Every public function carries a type hint on each parameter and on the return.
- Never commit a skipped test. Fix it, or delete it.
"""

README = """# payments-service

Refund operations for paid orders.

Run the tests with `python -m pytest`. This repository has no CI pipeline, so the local
run is the only test signal.
"""

BASE_REFUNDS = '''"""Refund operations for the payments service."""

REFUND_WINDOW_DAYS = 90


def _audit(db, order_id: str, actor: str, amount_cents: int) -> None:
    db.execute(
        "INSERT INTO refund_audit (order_id, actor, amount_cents) VALUES (?, ?, ?)",
        (order_id, actor, amount_cents),
    )


def refund_order(db, order_id: str, actor: str) -> dict:
    """Refund a paid order in full."""
    order = db.get_order(order_id)
    if order is None:
        raise LookupError(f"unknown order {order_id}")
    if order["days_since_paid"] > REFUND_WINDOW_DAYS:
        raise ValueError("the refund window has closed")
    _audit(db, order_id, actor, order["total_cents"])
    return {"order_id": order_id, "amount_cents": order["total_cents"]}
'''

HEAD_REFUNDS = BASE_REFUNDS + '''

def create_partial_refund(db, order_id, actor, amount_cents):
    """Refund part of a paid order."""
    order = db.get_order(order_id)
    amount = float(amount_cents)
    if amount > order["total_cents"]:
        raise ValueError("the refund exceeds the order total")
    _audit_partial(db, order_id, actor, amount)
    return {"order_id": order_id, "amount_cents": amount}


def _audit_partial(db, order_id, actor, amount_cents):
    db.execute(
        "INSERT INTO refund_audit (order_id, actor, amount_cents) "
        f"VALUES ('{order_id}', '{actor}', {amount_cents})"
    )
'''

BASE_TESTS = '''import pytest

from svc.refunds import refund_order


class FakeDb:
    def __init__(self, order):
        self.order = order
        self.statements = []

    def get_order(self, order_id):
        return self.order

    def execute(self, sql, params=None):
        self.statements.append((sql, params))


def test_refund_order_returns_the_full_total():
    db = FakeDb({"total_cents": 5000, "days_since_paid": 3})
    assert refund_order(db, "ord-1", "clerk")["amount_cents"] == 5000
'''

HEAD_TESTS = BASE_TESTS + '''

@pytest.mark.skip(reason="flaky on the shared runner")
def test_partial_refund_rejects_more_than_the_total():
    db = FakeDb({"total_cents": 5000, "days_since_paid": 3})
    with pytest.raises(ValueError):
        create_partial_refund(db, "ord-1", "clerk", 9000)
'''

BASE_FILES = {
    "README.md": README,
    "CODING_STANDARDS.md": STANDARDS,
    "svc/refunds.py": BASE_REFUNDS,
    "tests/test_refunds.py": BASE_TESTS,
}

HEAD_FILES = {
    "svc/refunds.py": HEAD_REFUNDS,
    "tests/test_refunds.py": HEAD_TESTS,
}

# --- the work items ----------------------------------------------------------

AC_TEXT = """h3. Acceptance criteria

* AC-1: The endpoint accepts an amount in whole cents and refunds exactly that amount.
* AC-2: The total refunded across every refund on an order never exceeds the order total.
* AC-3: A refund is rejected when the order was paid more than 90 days ago.
* AC-4: Every refund writes an audit row that names the actor and the amount.
"""

WORK_ITEMS = {
    "PAY-118": {
        "summary": "Refund part of a paid order",
        "type": "Story",
        "description": "Support a partial refund on a paid order.\n\n" + AC_TEXT,
    },
    "GH-4521": {
        "summary": "Refund part of a paid order",
        "type": "Story",
        "description": "Support a partial refund on a paid order.\n\n" + AC_TEXT,
    },
}

ISSUE_BODY = """Support a partial refund on a paid order.

### Acceptance criteria

- [ ] AC-1: The endpoint accepts an amount in whole cents and refunds exactly that amount.
- [ ] AC-2: The total refunded across every refund on an order never exceeds the order total.
- [ ] AC-3: A refund is rejected when the order was paid more than 90 days ago.
- [ ] AC-4: Every refund writes an audit row that names the actor and the amount.
"""

# --- the cases ---------------------------------------------------------------

CASES = [
    {
        "dir": "mr-42", "host": "gitlab", "project": "fixture-org/my-service", "iid": 42,
        "title": "PAY-118: refund part of a paid order", "author": "dev-sam",
        "description": "Implements PAY-118. Adds create_partial_refund and its audit row.",
        "jira": "PAY-118",
    },
    {
        "dir": "mr-7", "host": "gitlab", "project": "fixture-org/platform", "iid": 7,
        "title": "Hotfix: refund part of a paid order", "author": "dev-sam",
        "description": "Quick hotfix. No ticket.",
    },
    {
        "dir": "mr-201", "host": "gitlab", "project": "fixture-org/backend", "iid": 201,
        "title": "GH-4521: refund part of a paid order", "author": "dev-sam",
        "description": "Adds create_partial_refund and its audit row.",
        "jira": "GH-4521",
    },
    {
        "dir": "mr-55", "host": "gitlab", "project": "fixture-org/my-service", "iid": 55,
        "title": "PAY-118: refund part of a paid order", "author": "dev-sam",
        "description": "Implements PAY-118.",
        "jira": "PAY-118",
    },
    {
        "dir": "mr-61", "host": "gitlab", "project": "fixture-org/my-service", "iid": 61,
        "title": "PAY-118: refund part of a paid order", "author": "reviewer",
        "description": "Implements PAY-118.",
        "jira": "PAY-118",
    },
    {
        "dir": "mr-410", "host": "gitlab", "project": "fixture-org/backend", "iid": 410,
        "title": "GH-4521: refund part of a paid order", "author": "dev-sam",
        "description": "Implements GH-4521.",
        "jira": "GH-4521",
    },
    {
        "dir": "pr-123", "host": "github", "project": "fixture-org/my-service", "iid": 123,
        "title": "Refund part of a paid order", "author": "dev-sam",
        "description": "Closes #77. Adds create_partial_refund and its audit row.",
        "issue": 77,
    },
    {
        "dir": "pr-88", "host": "github", "project": "fixture-org/webapp", "iid": 88,
        "title": "Refund part of a paid order", "author": "dev-sam",
        "description": "Linked to fixture-org/webapp#45.",
        "issue": 45,
    },
    {
        "dir": "pr-300", "host": "github", "project": "fixture-org/my-service", "iid": 300,
        "title": "Refund part of a paid order", "author": "dev-sam",
        "description": "Closes #77.",
        "issue": 77,
    },
]


def git(*args, cwd, check=True):
    env = dict(os.environ)
    env.update(GIT_ENV)
    proc = subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}: {proc.stderr.strip()}")
    return proc.stdout


def write_tree(root: Path, files: dict) -> None:
    for rel, body in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)


def build_repo(dest: Path) -> dict:
    """Build origin.git and a clone of it. Return the SHAs and the per-file patches."""
    work = dest / ".build"
    work.mkdir(parents=True)
    git("init", "-q", "-b", TARGET_BRANCH, ".", cwd=work)
    write_tree(work, BASE_FILES)
    git("add", "-A", cwd=work)
    git("commit", "-q", "-m", "chore: full refunds and the coding standards", cwd=work)
    base_sha = git("rev-parse", "HEAD", cwd=work).strip()

    git("checkout", "-q", "-b", SOURCE_BRANCH, cwd=work)
    write_tree(work, HEAD_FILES)
    git("add", "-A", cwd=work)
    git("commit", "-q", "-m", "feat: refund part of a paid order", cwd=work)
    head_sha = git("rev-parse", "HEAD", cwd=work).strip()

    origin = dest / "origin.git"
    git("init", "-q", "--bare", str(origin), cwd=dest)
    git("push", "-q", str(origin), f"{TARGET_BRANCH}:{TARGET_BRANCH}",
        f"{SOURCE_BRANCH}:{SOURCE_BRANCH}", cwd=work)

    clone = dest / "clone"
    # --no-hardlinks: a hard-linked git object under the eval directory makes
    # `claude plugin eval` refuse the run, because a case definition must not be
    # reachable by a second name.
    git("clone", "-q", "--no-hardlinks", str(origin), str(clone), cwd=dest)
    # A relative remote URL survives the copy into each case working directory.
    git("remote", "set-url", "origin", "../origin.git", cwd=clone)
    git("checkout", "-q", TARGET_BRANCH, cwd=clone)

    patches = []
    names = git("diff", "--name-only", base_sha, head_sha, cwd=work).split()
    for name in names:
        raw = git("diff", "--unified=3", base_sha, head_sha, "--", name, cwd=work)
        hunks = raw[raw.index("@@"):] if "@@" in raw else ""
        patches.append({"filename": name, "patch": hunks})
    full_diff = git("diff", "--unified=3", base_sha, head_sha, cwd=work)

    shutil.rmtree(work)
    return {"base_sha": base_sha, "head_sha": head_sha,
            "patches": patches, "diff": full_diff}


def sanitize(path: str) -> str:
    """Turn an API path into the file name that the stubs look up."""
    key = path.split("?")[0].strip("/").replace("%2F", "/").replace("%2f", "/")
    return key.replace("/", "_")


def gitlab_api(case: dict, repo: dict, api: Path) -> None:
    project, iid = case["project"], case["iid"]
    mr = {
        "iid": iid,
        "id": 1000 + iid,
        "title": case["title"],
        "description": case["description"],
        "state": "opened",
        "author": {"username": case["author"], "name": case["author"]},
        "source_branch": SOURCE_BRANCH,
        "target_branch": TARGET_BRANCH,
        "changes_count": str(len(repo["patches"])),
        "diff_refs": {
            "base_sha": repo["base_sha"],
            "start_sha": repo["base_sha"],
            "head_sha": repo["head_sha"],
        },
        "head_pipeline": {"status": "success", "id": 9001},
        "pipeline": {"status": "success", "id": 9001},
        "web_url": f"https://gitlab.fixture.test/{project}/-/merge_requests/{iid}",
    }
    base = f"projects/{project}/merge_requests/{iid}"
    write_json(api, sanitize(base), mr)
    changes = dict(mr)
    changes["changes"] = [
        {"new_path": p["filename"], "old_path": p["filename"], "diff": p["patch"],
         "new_file": False, "deleted_file": False,
         "renamed_file": False}
        for p in repo["patches"]
    ]
    write_json(api, sanitize(base + "/changes"), changes)
    write_json(api, sanitize(base + "/discussions"), [])
    write_json(api, sanitize(base + "/notes"), [])
    write_json(api, sanitize(base + "/draft_notes"), [])
    write_json(api, sanitize(base + "/approvals"),
               {"approved_by": [], "approved": False})
    write_json(api, "user", {"id": 7, "username": "reviewer", "name": "Rey Viewer"})
    (api / "mr_diff.patch").write_text(repo["diff"])


def github_api(case: dict, repo: dict, api: Path) -> None:
    owner, name = case["project"].split("/")
    number = case["iid"]
    pr = {
        "number": number,
        "title": case["title"],
        "body": case["description"],
        "state": "OPEN",
        "author": {"login": case["author"]},
        "baseRefName": TARGET_BRANCH,
        "headRefName": SOURCE_BRANCH,
        "baseRefOid": repo["base_sha"],
        "headRefOid": repo["head_sha"],
        "changedFiles": len(repo["patches"]),
        "statusCheckRollup": [
            {"name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS",
             "workflowName": "ci"}
        ],
        "url": f"https://github.com/{owner}/{name}/pull/{number}",
    }
    write_json(api, f"pulls_{owner}_{name}_{number}_view", pr)
    files = [
        {"filename": p["filename"], "status": "modified", "patch": p["patch"],
         "additions": p["patch"].count("\n+"), "deletions": p["patch"].count("\n-"),
         "changes": 0}
        for p in repo["patches"]
    ]
    base = f"repos/{owner}/{name}"
    write_json(api, sanitize(f"{base}/pulls/{number}/files"), files)
    write_json(api, sanitize(f"{base}/pulls/{number}/comments"), [])
    write_json(api, sanitize(f"{base}/issues/{number}/comments"), [])
    write_json(api, sanitize(f"{base}/pulls/{number}/reviews"), [])
    write_json(api, sanitize(f"{base}/pulls/{number}"), {
        "number": number, "title": case["title"], "body": case["description"],
        "user": {"login": case["author"]},
        "head": {"sha": repo["head_sha"], "ref": SOURCE_BRANCH},
        "base": {"sha": repo["base_sha"], "ref": TARGET_BRANCH},
        "html_url": pr["url"],
    })
    write_json(api, "user", {"id": 7, "login": "reviewer", "name": "Rey Viewer"})
    (api / f"pulls_{owner}_{name}_{number}_diff.patch").write_text(repo["diff"])

    if case.get("issue"):
        n = case["issue"]
        issue = {
            "number": n,
            "title": "Refund part of a paid order",
            "body": ISSUE_BODY,
            "labels": [{"name": "enhancement"}],
            "state": "OPEN",
            "url": f"https://github.com/{owner}/{name}/issues/{n}",
        }
        write_json(api, f"issues_{owner}_{name}_{n}_view", issue)
        write_json(api, sanitize(f"{base}/issues/{n}"), issue)


def jira_api(case: dict, api: Path) -> None:
    key = case.get("jira")
    if not key:
        return
    item = WORK_ITEMS[key]
    write_json(api, f"jira_{key}", {
        "data": {
            "items": [{
                "data": {
                    "key": key,
                    "summary": item["summary"],
                    "issuetype": {"name": item["type"]},
                    "renderedFields": {"description": item["description"]},
                    "url": f"https://fixture-org.atlassian.net/browse/{key}",
                }
            }]
        },
        "stats": {"items": 1},
    })


def write_json(api: Path, key: str, payload) -> None:
    (api / f"{key}.json").write_text(json.dumps(payload, indent=2) + "\n")


def build_case(case: dict) -> None:
    dest = FIXTURES / case["dir"]
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    repo = build_repo(dest)
    api = dest / "api"
    api.mkdir()
    if case["host"] == "gitlab":
        gitlab_api(case, repo, api)
    else:
        github_api(case, repo, api)
    jira_api(case, api)
    print(f"built {dest.relative_to(FIXTURES.parent.parent)} "
          f"base={repo['base_sha'][:8]} head={repo['head_sha'][:8]}")


def main(argv: list) -> int:
    wanted = argv[1:] or [c["dir"] for c in CASES]
    for case in CASES:
        if case["dir"] in wanted:
            build_case(case)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
