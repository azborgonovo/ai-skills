#!/usr/bin/env python3
"""Post code-review findings as a GitHub PR pending review — reliably.

GitHub's review-creation call is atomic: if any one inline comment in the
`comments` array doesn't land on a line that's actually part of the diff, the
whole call is rejected (HTTP 422) and none of the comments are created —
unlike GitLab, which accepts the draft either way and only tells you it
didn't anchor via a null `line_code`. So this script fetches the PR's own
diff first and validates every anchor locally before ever calling the API:
anything that doesn't land on an added ('+') line gets folded into the
review's body instead of risking the whole batch.

Notes file format (JSON array) — same shape as the GitLab script's:
  [
    {"note": "text", "new_path": "src/a.go", "new_line": 47},
    {"note": "general remark", "general": true}
  ]
  - "general": true (or omitting new_line) folds the note into the review body.

The signature line "Co-reviewed with :robot:" is what --purge keys on, so it
only ever deletes pending reviews this skill created — never a human
reviewer's own in-progress pending review. The posted footer extends that
fixed prefix with the reviewing model (and effort, if known) via
--model/--effort, e.g. "Co-reviewed with :robot: using Sonnet 5 (high
effort)" — but the purge match stays on the bare prefix so it still finds
prior drafts posted under a different model or effort.

Examples:
  post_review_notes_github.py --owner acme --repo my-service --pr 42 \
    --head-sha abc123 --notes notes.json \
    --model "Sonnet 5" --effort high --purge
  post_review_notes_github.py ... --notes notes.json --dry-run   # print actions, no network
"""

import argparse
import json
import re
import subprocess
import sys

SIGNATURE = "Co-reviewed with :robot:"


def build_signature(model, effort):
    """Extend the fixed purge-key prefix with model/effort, when known."""
    if not model:
        return SIGNATURE
    if effort:
        return f"{SIGNATURE} using {model} ({effort} effort)"
    return f"{SIGNATURE} using {model}"


def gh_api(path, method="GET", body=None, paginate=False, dry_run=False):
    """Call `gh api`. Returns parsed JSON (or None). Raises on hard failure."""
    cmd = ["gh", "api", "--method", method]
    if paginate:
        cmd.append("--paginate")
    if body is not None:
        cmd += ["--input", "-"]
    cmd.append(path)
    if dry_run:
        printable = cmd if body is None else cmd + ["<<", json.dumps(body)]
        print(f"  DRY-RUN: {' '.join(printable)}")
        if method == "GET":
            return [], None
        if method == "DELETE":
            return {}, None
        return {"id": 0, "state": "PENDING", "html_url": "(dry-run)"}, None  # POST
    proc = subprocess.run(
        cmd,
        input=json.dumps(body) if body is not None else None,
        capture_output=True,
        text=True,
    )
    out = proc.stdout.strip()
    if proc.returncode != 0:
        return None, (out or proc.stderr.strip())
    if not out:
        return None, None
    # --paginate concatenates one JSON array/object per page back-to-back
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
        return items, None
    return json.loads(out), None


def added_lines_by_file(files):
    """Map filename -> set of new-file line numbers that appear as '+' in the diff."""
    result = {}
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
    for f in files:
        patch = f.get("patch")
        if not patch:
            continue  # binary or too large to diff — no valid anchors
        valid = set()
        new_line = None
        for line in patch.splitlines():
            m = hunk_re.match(line)
            if m:
                new_line = int(m.group(1))
                continue
            if new_line is None:
                continue
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+"):
                valid.add(new_line)
                new_line += 1
            elif line.startswith("-"):
                pass  # removed line — doesn't exist in the new file
            else:
                new_line += 1  # context line
        result[f["filename"]] = valid
    return result


def create_review(owner, repo, pr, head_sha, body, comments, dry_run):
    # No "event" key at all -> GitHub leaves the review in PENDING state.
    payload = {"commit_id": head_sha, "body": body}
    if comments:
        payload["comments"] = comments
    return gh_api(
        f"repos/{owner}/{repo}/pulls/{pr}/reviews",
        method="POST",
        body=payload,
        dry_run=dry_run,
    )


def purge_own_pending_reviews(owner, repo, pr, dry_run):
    """Delete only PENDING reviews bearing this skill's signature."""
    existing, err = gh_api(f"repos/{owner}/{repo}/pulls/{pr}/reviews", paginate=True, dry_run=dry_run)
    if err:
        print(f"purge: could not list existing reviews ({err}) — skipping")
        return
    removed = 0
    for r in existing or []:
        if r.get("state") == "PENDING" and SIGNATURE in (r.get("body") or ""):
            _, del_err = gh_api(
                f"repos/{owner}/{repo}/pulls/{pr}/reviews/{r['id']}", method="DELETE", dry_run=dry_run
            )
            if not del_err:
                removed += 1
    print(f"purge: removed {removed} stale pending review(s) created by this skill")


def main():
    ap = argparse.ArgumentParser(description="Post MR review findings as a GitHub pending review.")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", required=True, help="PR number")
    ap.add_argument("--head-sha", required=True, help="Head commit SHA (headRefOid)")
    ap.add_argument("--notes", required=True, help="Path to notes JSON array")
    ap.add_argument("--model", help="Reviewing model name, e.g. 'Sonnet 5' — appended to the footer if given")
    ap.add_argument("--effort", help="Reviewing effort level, e.g. 'high' — appended only if --model is also given")
    ap.add_argument("--purge", action="store_true", help="Delete this skill's prior pending review first")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without calling the network")
    args = ap.parse_args()

    with open(args.notes) as f:
        notes = json.load(f)
    if not isinstance(notes, list):
        sys.exit("notes file must be a JSON array")

    signature = build_signature(args.model, args.effort)

    if args.purge:
        purge_own_pending_reviews(args.owner, args.repo, args.pr, args.dry_run)

    files, err = gh_api(f"repos/{args.owner}/{args.repo}/pulls/{args.pr}/files", paginate=True, dry_run=args.dry_run)
    if err:
        sys.exit(f"could not fetch PR diff to validate anchors: {err}")
    valid_lines = added_lines_by_file(files or [])

    comments = []
    comment_raw_texts = []
    general_notes = []
    for item in notes:
        text = item["note"]
        is_general = item.get("general") or "new_line" not in item
        if not is_general:
            path, line = item["new_path"], int(item["new_line"])
            if line not in valid_lines.get(path, set()):
                is_general = True  # doesn't land on an added line — fold to body instead
        if is_general:
            general_notes.append(text)
        else:
            comments.append({
                "path": item["new_path"],
                "line": int(item["new_line"]),
                "side": "RIGHT",
                "body": f"{text}\n\n{signature}",
            })
            comment_raw_texts.append(text)

    body_parts = [signature]
    if general_notes:
        body_parts.append("\n\n".join(f"- {n}" for n in general_notes))
    body = "\n\n".join(body_parts)

    resp, err = create_review(args.owner, args.repo, args.pr, args.head_sha, body, comments, args.dry_run)
    if err:
        print(f"review creation failed with {len(comments)} inline comment(s) ({err}) — retrying with all findings folded into the body")
        fallback_notes = general_notes + comment_raw_texts
        fallback_body = "\n\n".join([signature] + [f"- {n}" for n in fallback_notes])
        resp, err = create_review(args.owner, args.repo, args.pr, args.head_sha, fallback_body, [], args.dry_run)
        if err:
            sys.exit(f"review creation failed even with no inline comments: {err}")
        print(f"review {resp.get('id')}: created with 0 inline comments, {len(fallback_notes)} folded into body (fallback)")
        return

    print(
        f"review {resp.get('id')}: created with {len(comments)} inline comment(s), "
        f"{len(general_notes)} folded into body — {resp.get('html_url', '(dry-run)')}"
    )


if __name__ == "__main__":
    main()
