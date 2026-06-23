#!/usr/bin/env python3
"""Post code-review findings as GitLab MR draft notes — reliably.

Replaces the inline bash/python that used to live in SKILL.md Step 7. Handles an
arbitrary number of notes, verifies each positioned note actually resolved against
the diff (GitLab returns HTTP 200 even when it didn't), falls back to a positionless
note when resolution fails, and optionally purges this skill's own stale drafts.

Notes file format (JSON array):
  [
    {"note": "text", "new_path": "src/a.go", "new_line": 47, "old_path": "src/a.go"},
    {"note": "general remark", "general": true}
  ]
  - old_path defaults to new_path (correct for new/unmodified files).
  - "general": true posts a positionless draft note (a plain discussion comment).

The signature line "Co-reviewed with :robot:" is what --purge keys on, so it only
ever deletes drafts this skill created — never the human reviewer's own drafts.

Examples:
  post_review_notes.py --project acme%2Fmy-service --mr 42 \
    --base-sha B --start-sha S --head-sha H --notes notes.json --purge
  post_review_notes.py ... --notes notes.json --dry-run   # print actions, no network
"""

import argparse
import json
import subprocess
import sys

SIGNATURE = "Co-reviewed with :robot:"


def glab_api(path, method="GET", body=None, dry_run=False):
    """Call `glab api`. Returns parsed JSON (or None). Raises on hard failure."""
    cmd = ["glab", "api", "--method", method]
    if body is not None:
        cmd += ["--header", "Content-Type: application/json", "--input", "-"]
    cmd.append(path)
    if dry_run:
        printable = cmd if body is None else cmd + ["<<", json.dumps(body)]
        print(f"  DRY-RUN: {' '.join(printable)}")
        if method == "GET":
            return []  # no pre-existing drafts to purge
        if method == "DELETE":
            return {}
        return {"id": 0, "position": body.get("position") if body else None}  # POST
    proc = subprocess.run(
        cmd,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    out = proc.stdout.strip()
    if not out:
        return None
    return json.loads(out)


def draft_notes_path(project, mr, draft_id=None):
    base = f"projects/{project}/merge_requests/{mr}/draft_notes"
    return f"{base}/{draft_id}" if draft_id else base


def purge_own_drafts(project, mr, dry_run):
    """Delete only drafts bearing this skill's signature, so reruns don't duplicate."""
    existing = glab_api(draft_notes_path(project, mr), dry_run=dry_run) or []
    removed = 0
    for n in existing:
        if SIGNATURE in (n.get("note") or ""):
            glab_api(draft_notes_path(project, mr, n["id"]), method="DELETE", dry_run=dry_run)
            removed += 1
    print(f"purge: removed {removed} stale draft(s) created by this skill")


def post_one(project, mr, body, dry_run):
    return glab_api(draft_notes_path(project, mr), method="POST", body=body, dry_run=dry_run)


def main():
    ap = argparse.ArgumentParser(description="Post MR review findings as draft notes.")
    ap.add_argument("--project", required=True, help="URL-encoded project path, e.g. acme%%2Fmy-service")
    ap.add_argument("--mr", required=True, help="MR iid")
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--start-sha", required=True)
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--notes", required=True, help="Path to notes JSON array")
    ap.add_argument("--purge", action="store_true", help="Delete this skill's prior drafts first")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without calling the network")
    args = ap.parse_args()

    with open(args.notes) as f:
        notes = json.load(f)
    if not isinstance(notes, list):
        sys.exit("notes file must be a JSON array")

    if args.purge:
        purge_own_drafts(args.project, args.mr, args.dry_run)

    refs = {"base_sha": args.base_sha, "start_sha": args.start_sha, "head_sha": args.head_sha}

    for i, item in enumerate(notes, 1):
        text = item["note"]
        if SIGNATURE not in text:
            text = f"{text}\n\n{SIGNATURE}"

        if item.get("general") or "new_line" not in item:
            body = {"note": text}
            resp = post_one(args.project, args.mr, body, args.dry_run)
            print(f"note {i}: id={(resp or {}).get('id')} general=True")
            continue

        new_path = item["new_path"]
        body = {
            "note": text,
            "position": {
                **refs,
                "position_type": "text",
                "new_path": new_path,
                "old_path": item.get("old_path", new_path),
                "new_line": int(item["new_line"]),
            },
        }
        resp = post_one(args.project, args.mr, body, args.dry_run) or {}
        resolved = resp.get("position") is not None
        if resolved or args.dry_run:
            print(f"note {i}: id={resp.get('id')} resolved={resolved} ({new_path}:{item['new_line']})")
            continue

        # GitLab accepted the draft (HTTP 200) but couldn't anchor it to the diff —
        # it would never publish as an inline comment. Delete and re-post positionless.
        glab_api(draft_notes_path(args.project, args.mr, resp["id"]), method="DELETE")
        retry = post_one(args.project, args.mr, {"note": text}, dry_run=False) or {}
        print(f"note {i}: id={retry.get('id')} resolved=False -> reposted positionless ({new_path})")


if __name__ == "__main__":
    main()
