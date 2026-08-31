#!/usr/bin/env python3
"""Post code-review findings to a GitLab MR — as drafts, or published with a verdict.

Handles an arbitrary number of notes, verifies each positioned note actually
resolved against the diff (GitLab returns HTTP 200 even when it didn't), falls
back to a positionless note when resolution fails, and optionally purges this
skill's own stale drafts.

Notes file format (JSON array):
  [
    {"note": "text", "new_path": "src/a.go", "new_line": 47, "old_path": "src/a.go"},
    {"note": "general remark", "general": true}
  ]
  - old_path defaults to new_path (correct for new/unmodified files).
  - "general": true posts a positionless note (a plain discussion comment).

Every note is marked with a robot emoji — trailing, or on its own line when the
note ends in a code fence. That marker is what --purge
keys on, so a rerun only ever deletes drafts this skill created (a human's own
drafts don't carry it), and what --mode direct keys on to skip a finding already
published on the MR.

--mode direct publishes each draft this run created, one id at a time, and never
calls draft_notes/bulk_publish — that endpoint publishes *every* pending draft the
authenticated user has on the MR, including ones they wrote by hand.

--verdict acts on the MR after the comments are published, so an approval never
lands without its reasoning. GitLab exposes no API for a reviewer's
"requested changes" state, so request-changes clears any approval this account
holds and posts the summary as a note instead; the caller must tell the user the
merge-blocking state needs a click in the UI.

Examples:
  post_review_notes_gitlab.py --project acme%2Fmy-service --mr 42 \
    --base-sha B --start-sha S --head-sha H --notes notes.json --purge
  post_review_notes_gitlab.py ... --mode direct --verdict approve
  post_review_notes_gitlab.py ... --mode direct --verdict request-changes --summary-file summary.md
  post_review_notes_gitlab.py ... --notes notes.json --dry-run   # print actions, no network
"""

import argparse
import json
import re
import subprocess
import sys

MARKER = "🤖"
CLOSING_FENCE = re.compile(r"^\s{0,3}(?:`{3,}|~{3,})\s*$")
SUGGESTION_FENCE = re.compile(r"^\s{0,3}(?:`{3,}|~{3,})suggestion", re.M)


def with_marker(text):
    """Mark a note as this skill's, unless it already ends with the marker."""
    text = text.rstrip()
    if text.endswith(MARKER):
        return text
    # A closing fence only closes its block when nothing else shares the line, so a note
    # ending in a suggestion block takes the marker on a line of its own.
    if CLOSING_FENCE.match(text.rsplit("\n", 1)[-1]):
        return f"{text}\n\n{MARKER}"
    return f"{text} {MARKER}"


def has_suggestion(text):
    """True when the note carries a suggestion block, which only applies on a diff note."""
    return SUGGESTION_FENCE.search(text) is not None


def normalize(text):
    """Collapse a note to a comparable form: marker dropped, whitespace flattened."""
    return re.sub(r"\s+", " ", text.replace(MARKER, "")).strip()


def glab_api(path, method="GET", body=None, paginate=False, dry_run=False, tolerate=False):
    """Call `glab api`. Returns parsed JSON (or None). Raises on hard failure unless tolerated."""
    cmd = ["glab", "api", "--method", method]
    if paginate:
        cmd.append("--paginate")
    if body is not None:
        cmd += ["--header", "Content-Type: application/json", "--input", "-"]
    cmd.append(path)
    if dry_run:
        printable = cmd if body is None else cmd + ["<<", json.dumps(body)]
        print(f"  DRY-RUN: {' '.join(printable)}")
        if method == "GET":
            return []  # no pre-existing drafts, notes, or discussions
        if method == "DELETE":
            return {}
        pos = body.get("position") if body else None
        return {"id": 0, "position": pos, "line_code": "dry_run" if pos else None}
    proc = subprocess.run(
        cmd,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip()
        if tolerate:
            return {"error": err}
        raise RuntimeError(err)
    out = proc.stdout.strip()
    if not out:
        return None
    if paginate:
        decoder = json.JSONDecoder()
        items, i = [], 0
        while i < len(out):
            while i < len(out) and out[i].isspace():
                i += 1
            if i >= len(out):
                break
            obj, end = decoder.raw_decode(out, i)
            items.extend(obj if isinstance(obj, list) else [obj])
            i = end
        return items
    return json.loads(out)


def mr_path(project, mr, suffix=""):
    return f"projects/{project}/merge_requests/{mr}{suffix}"


def draft_notes_path(project, mr, draft_id=None):
    base = mr_path(project, mr, "/draft_notes")
    return base if draft_id is None else f"{base}/{draft_id}"


def current_username(dry_run):
    if dry_run:
        return "(dry-run)"
    return (glab_api("user", dry_run=False) or {}).get("username")


def already_published(project, mr, username, dry_run):
    """This account's published 🤖 notes, as ({(path, line)}, {normalized text})."""
    discussions = glab_api(mr_path(project, mr, "/discussions"), paginate=True, dry_run=dry_run) or []
    anchors, texts = set(), set()
    for d in discussions:
        for n in d.get("notes") or []:
            body = n.get("body") or ""
            if MARKER not in body or (n.get("author") or {}).get("username") != username:
                continue
            texts.add(normalize(body))
            pos = n.get("position") or {}
            if pos.get("new_path") and pos.get("new_line"):
                anchors.add((pos["new_path"], int(pos["new_line"])))
    return anchors, texts


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


def apply_verdict(project, mr, verdict, head_sha, summary_file, dry_run, published_texts=frozenset()):
    """Approve, or clear approval and post the summary — GitLab can't set 'requested changes'."""
    if verdict == "approve":
        resp = glab_api(
            mr_path(project, mr, "/approve"),
            method="POST",
            body={"sha": head_sha},
            dry_run=dry_run,
            tolerate=True,
        ) or {}
        if resp.get("error"):
            err = resp["error"]
            hint = " — the head moved since the review started" if "409" in err else ""
            print(f"verdict: approve FAILED ({err}){hint}")
            return False
        print(f"verdict: approved MR !{mr} at {head_sha[:8]}")
        return True

    resp = glab_api(mr_path(project, mr, "/unapprove"), method="POST", dry_run=dry_run, tolerate=True) or {}
    if resp.get("error"):
        print(f"verdict: no approval to clear ({resp['error']})")
    else:
        print("verdict: cleared this account's approval")
    with open(summary_file) as f:
        summary = with_marker(f.read().strip())
    # Marked like every other note, so a rerun recognises it instead of posting a second copy.
    if normalize(summary) in published_texts:
        print("verdict: summary already on the MR, left as it is")
    else:
        glab_api(mr_path(project, mr, "/notes"), method="POST", body={"body": summary}, dry_run=dry_run)
        print("verdict: posted the request-changes summary as a note")
    print("verdict: GitLab has no API for a reviewer's 'requested changes' state — tell the user to set it in the UI")
    return True


def main():
    ap = argparse.ArgumentParser(description="Post MR review findings as draft or published notes.")
    ap.add_argument("--project", required=True, help="URL-encoded project path, e.g. acme%%2Fmy-service")
    ap.add_argument("--mr", required=True, help="MR iid")
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--start-sha", required=True)
    ap.add_argument("--head-sha", required=True)
    ap.add_argument("--notes", required=True, help="Path to notes JSON array")
    ap.add_argument("--mode", choices=("draft", "direct"), default="draft",
                    help="draft: leave as drafts for the user to submit. direct: publish each one.")
    ap.add_argument("--verdict", choices=("approve", "request-changes", "none"), default="none",
                    help="Act on the MR after publishing (--mode direct only)")
    ap.add_argument("--summary-file", help="Markdown file holding the verdict summary (--verdict request-changes)")
    ap.add_argument("--purge", action="store_true", help="Delete this skill's prior drafts first")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without calling the network")
    args = ap.parse_args()

    if args.verdict != "none" and args.mode != "direct":
        sys.exit("--verdict requires --mode direct")
    if args.verdict == "request-changes" and not args.summary_file:
        sys.exit("--verdict request-changes requires --summary-file")

    with open(args.notes) as f:
        notes = json.load(f)
    if not isinstance(notes, list):
        sys.exit("notes file must be a JSON array")

    if args.purge:
        purge_own_drafts(args.project, args.mr, args.dry_run)

    anchors, texts = set(), set()
    if args.mode == "direct":
        username = current_username(args.dry_run)
        anchors, texts = already_published(args.project, args.mr, username, args.dry_run)

    refs = {"base_sha": args.base_sha, "start_sha": args.start_sha, "head_sha": args.head_sha}
    published, skipped = 0, []

    for i, item in enumerate(notes, 1):
        text = with_marker(item["note"])
        positioned = not item.get("general") and "new_line" in item
        anchor = (item["new_path"], int(item["new_line"])) if positioned else None

        if args.mode == "direct":
            if anchor and anchor in anchors:
                skipped.append(f"{anchor[0]}:{anchor[1]} (same line)")
                continue
            if normalize(text) in texts:
                where = f"{anchor[0]}:{anchor[1]}" if anchor else "general"
                skipped.append(f"{where} (identical text)")
                continue

        if not positioned:
            resp = post_one(args.project, args.mr, {"note": text}, args.dry_run) or {}
            draft_id, resolved = resp.get("id"), None
        else:
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
            draft_id = resp.get("id")
            # GitLab always echoes back the position you sent — check line_code instead,
            # which GitLab only populates when the position actually anchored to the diff.
            resolved = resp.get("line_code") is not None or args.dry_run
            if not resolved:
                # GitLab accepted the draft (HTTP 200) but couldn't anchor it to the diff —
                # it would never publish as an inline comment. Delete and re-post positionless.
                glab_api(draft_notes_path(args.project, args.mr, draft_id), method="DELETE")
                retry = post_one(args.project, args.mr, {"note": text}, dry_run=False) or {}
                draft_id = retry.get("id")

        where = f"{item['new_path']}:{item['new_line']}" if positioned else "general"
        if resolved is None:
            state = "general=True"
        elif resolved:
            state = "resolved=True"
        else:
            state = "resolved=False -> reposted positionless"
        if resolved is not True and has_suggestion(text):
            state += " (suggestion block inert off the diff)"
        if args.mode == "direct":
            if draft_id is None:
                print(f"note {i}: FAILED — no draft id returned, nothing published ({where})")
                continue
            glab_api(draft_notes_path(args.project, args.mr, draft_id) + "/publish",
                     method="PUT", dry_run=args.dry_run)
            published += 1
            print(f"note {i}: published id={draft_id} {state} ({where})")
        else:
            print(f"note {i}: draft id={draft_id} {state} ({where})")

    if args.mode == "direct":
        print(f"posted:  {published} comment(s)")
        if skipped:
            print(f"skipped: {len(skipped)} already on the MR")
            for s in skipped:
                print(f"  · {s}")
        if args.verdict != "none":
            apply_verdict(args.project, args.mr, args.verdict, args.head_sha,
                          args.summary_file, args.dry_run, texts)


if __name__ == "__main__":
    main()
