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

Every note this skill posts is marked with a trailing robot emoji, and one extra
positionless note attributes the review as a whole — "Code reviewed using Sonnet 5
(high) 🤖", built from --model/--effort. The emoji is what --purge keys on, so a
rerun only ever deletes drafts this skill created (a human's own drafts don't carry
it) and finds them regardless of which model or effort posted them.

Examples:
  post_review_notes.py --project acme%2Fmy-service --mr 42 \
    --base-sha B --start-sha S --head-sha H --notes notes.json \
    --model "Sonnet 5" --effort high --purge
  post_review_notes.py ... --notes notes.json --dry-run   # print actions, no network
"""

import argparse
import json
import subprocess
import sys

MARKER = "🤖"


def with_marker(text):
    """Mark a note as this skill's, unless it already ends with the marker."""
    text = text.rstrip()
    return text if text.endswith(MARKER) else f"{text} {MARKER}"


def build_attribution(model, effort):
    """The one positionless note that attributes the review as a whole."""
    if not model:
        return with_marker("Code reviewed by an AI agent")
    if effort:
        return with_marker(f"Code reviewed using {model} ({effort})")
    return with_marker(f"Code reviewed using {model}")


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
        pos = body.get("position") if body else None
        return {"id": 0, "position": pos, "line_code": "dry_run" if pos else None}  # POST
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
    """Delete only drafts bearing this skill's marker, so reruns don't duplicate."""
    existing = glab_api(draft_notes_path(project, mr), dry_run=dry_run) or []
    removed = 0
    for n in existing:
        if MARKER in (n.get("note") or ""):
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
    ap.add_argument("--model", help="Reviewing model name, e.g. 'Sonnet 5' — named in the attribution note if given")
    ap.add_argument("--effort", help="Reviewing effort level, e.g. 'high' — named in the attribution note only if --model is also given")
    ap.add_argument("--purge", action="store_true", help="Delete this skill's prior drafts first")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without calling the network")
    args = ap.parse_args()

    with open(args.notes) as f:
        notes = json.load(f)
    if not isinstance(notes, list):
        sys.exit("notes file must be a JSON array")

    if args.purge:
        purge_own_drafts(args.project, args.mr, args.dry_run)

    attribution = post_one(args.project, args.mr, {"note": build_attribution(args.model, args.effort)}, args.dry_run)
    print(f"attribution note: id={(attribution or {}).get('id')}")

    refs = {"base_sha": args.base_sha, "start_sha": args.start_sha, "head_sha": args.head_sha}

    for i, item in enumerate(notes, 1):
        text = with_marker(item["note"])

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
        # GitLab always echoes back the position you sent — check line_code instead,
        # which GitLab only populates when the position actually anchored to the diff.
        resolved = resp.get("line_code") is not None
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
