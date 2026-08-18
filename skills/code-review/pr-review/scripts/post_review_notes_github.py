#!/usr/bin/env python3
"""Post code-review findings to a GitHub PR — as a pending review, or published with a verdict.

Notes file format (JSON array) — same shape as the GitLab script's:
  [
    {"note": "text", "new_path": "src/a.go", "new_line": 47},
    {"note": "general remark", "general": true}
  ]
  - "general": true (or omitting new_line) means the finding has no line anchor.

Only lines that appear with a '+' prefix in the PR's own diff are valid anchors, so
this script fetches that diff and validates every anchor locally before posting.

Every comment is marked with a trailing robot emoji. That marker is what --purge
keys on, so a rerun only ever deletes a pending review this skill created (a human's
own in-progress review doesn't carry it), and what --mode direct keys on to skip a
finding already published on the PR.

The two modes post through different endpoints, because GitHub's review-creation
call is atomic — one bad anchor rejects the whole batch (HTTP 422) — and it demands
a body for the COMMENT and REQUEST_CHANGES events:

  --mode draft   one PENDING review holding every inline comment, with findings that
                 have no anchor folded into its body. Only the user can see it until
                 they submit it from the GitHub UI.
  --mode direct  one call per comment (POST pulls/{n}/comments for anchored findings,
                 POST issues/{n}/comments for the rest), so a bad anchor costs only
                 that finding, then one bodyless review call to carry the verdict.

--verdict acts on the PR after the comments are posted, so an approval never lands
without its reasoning. GitHub rejects approving your own PR, so the caller is
expected to pass --verdict none when the authenticated user authored the change.

Examples:
  post_review_notes_github.py --owner acme --repo my-service --pr 42 \
    --head-sha abc123 --notes notes.json --purge
  post_review_notes_github.py ... --mode direct --verdict approve
  post_review_notes_github.py ... --mode direct --verdict request-changes --summary-file summary.md
  post_review_notes_github.py ... --notes notes.json --dry-run   # print actions, no network
"""

import argparse
import json
import re
import subprocess
import sys

MARKER = "🤖"


def with_marker(text):
    """Mark a comment as this skill's, unless it already ends with the marker."""
    text = text.rstrip()
    return text if text.endswith(MARKER) else f"{text} {MARKER}"


def normalize(text):
    """Collapse a comment to a comparable form: marker dropped, whitespace flattened."""
    return re.sub(r"\s+", " ", text.replace(MARKER, "")).strip()


def gh_api(path, method="GET", body=None, paginate=False, dry_run=False):
    """Call `gh api`. Returns (parsed JSON or None, error string or None)."""
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
        return {"id": 0, "state": "PENDING", "html_url": "(dry-run)"}, None
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


def current_login(dry_run):
    if dry_run:
        return "(dry-run)"
    user, _ = gh_api("user", dry_run=False)
    return (user or {}).get("login")


def already_published(owner, repo, pr, login, dry_run):
    """This account's published 🤖 comments, as ({(path, line)}, {normalized text})."""
    anchors, texts = set(), set()
    review_comments, err = gh_api(f"repos/{owner}/{repo}/pulls/{pr}/comments", paginate=True, dry_run=dry_run)
    if err:
        print(f"dedupe: could not list review comments ({err}) — proceeding without deduplication")
        return anchors, texts
    issue_comments, err = gh_api(f"repos/{owner}/{repo}/issues/{pr}/comments", paginate=True, dry_run=dry_run)
    if err:
        print(f"dedupe: could not list conversation comments ({err}) — anchored findings still deduplicated")
        issue_comments = []
    for c in review_comments or []:
        body = c.get("body") or ""
        if MARKER not in body or (c.get("user") or {}).get("login") != login:
            continue
        texts.add(normalize(body))
        if c.get("path") and c.get("line"):
            anchors.add((c["path"], int(c["line"])))
    for c in issue_comments or []:
        body = c.get("body") or ""
        if MARKER in body and (c.get("user") or {}).get("login") == login:
            texts.add(normalize(body))
    return anchors, texts


def purge_own_pending_reviews(owner, repo, pr, dry_run):
    """Delete only PENDING reviews bearing this skill's marker, in the body or a comment."""
    existing, err = gh_api(f"repos/{owner}/{repo}/pulls/{pr}/reviews", paginate=True, dry_run=dry_run)
    if err:
        print(f"purge: could not list existing reviews ({err}) — skipping")
        return
    removed = 0
    for r in existing or []:
        if r.get("state") != "PENDING":
            continue
        owned = MARKER in (r.get("body") or "")
        if not owned:
            # A pending review whose findings all anchored has an empty body, so the
            # marker only shows up on its inline comments.
            comments, c_err = gh_api(
                f"repos/{owner}/{repo}/pulls/{pr}/reviews/{r['id']}/comments", paginate=True, dry_run=dry_run
            )
            owned = not c_err and any(MARKER in (c.get("body") or "") for c in comments or [])
        if not owned:
            continue
        _, del_err = gh_api(
            f"repos/{owner}/{repo}/pulls/{pr}/reviews/{r['id']}", method="DELETE", dry_run=dry_run
        )
        if not del_err:
            removed += 1
    print(f"purge: removed {removed} stale pending review(s) created by this skill")


def post_pending_review(owner, repo, pr, head_sha, comments, general_notes, dry_run):
    """Draft mode: one PENDING review, with unanchorable findings folded into its body."""
    payload = {"commit_id": head_sha}
    if general_notes:
        payload["body"] = "\n\n".join(f"- {with_marker(n)}" for n in general_notes)
    if comments:
        payload["comments"] = comments
    resp, err = gh_api(f"repos/{owner}/{repo}/pulls/{pr}/reviews", method="POST", body=payload, dry_run=dry_run)
    if err:
        print(f"review creation failed with {len(comments)} inline comment(s) ({err}) — retrying with every finding folded into the body")
        folded = general_notes + [c["body"] for c in comments]
        resp, err = gh_api(
            f"repos/{owner}/{repo}/pulls/{pr}/reviews",
            method="POST",
            body={"commit_id": head_sha, "body": "\n\n".join(f"- {with_marker(n)}" for n in folded)},
            dry_run=dry_run,
        )
        if err:
            sys.exit(f"review creation failed even with no inline comments: {err}")
        print(f"review {resp.get('id')}: created with 0 inline comments, {len(folded)} folded into body (fallback)")
        return
    print(
        f"review {resp.get('id')}: created with {len(comments)} inline comment(s), "
        f"{len(general_notes)} folded into body — {resp.get('html_url', '(dry-run)')}"
    )


def apply_verdict(owner, repo, pr, head_sha, verdict, summary_file, dry_run):
    """Approve, or request changes with the summary GitHub requires for that event."""
    payload = {"commit_id": head_sha, "event": "APPROVE" if verdict == "approve" else "REQUEST_CHANGES"}
    if verdict == "request-changes":
        with open(summary_file) as f:
            payload["body"] = f.read().strip()
    resp, err = gh_api(f"repos/{owner}/{repo}/pulls/{pr}/reviews", method="POST", body=payload, dry_run=dry_run)
    if err:
        hint = " — GitHub rejects acting on your own PR" if "own pull request" in err else ""
        print(f"verdict: {verdict} FAILED ({err}){hint}")
        return False
    print(f"verdict: {verdict} on PR #{pr} at {head_sha[:8]} — {resp.get('html_url', '(dry-run)')}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Post PR review findings as a pending review or published comments.")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", required=True, help="PR number")
    ap.add_argument("--head-sha", required=True, help="Head commit SHA (headRefOid)")
    ap.add_argument("--notes", required=True, help="Path to notes JSON array")
    ap.add_argument("--mode", choices=("draft", "direct"), default="draft",
                    help="draft: one pending review for the user to submit. direct: publish each comment.")
    ap.add_argument("--verdict", choices=("approve", "request-changes", "none"), default="none",
                    help="Act on the PR after posting (--mode direct only)")
    ap.add_argument("--summary-file", help="Markdown file holding the verdict summary (--verdict request-changes)")
    ap.add_argument("--purge", action="store_true", help="Delete this skill's prior pending review first")
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

    if args.purge and args.mode == "draft":
        purge_own_pending_reviews(args.owner, args.repo, args.pr, args.dry_run)

    files, err = gh_api(f"repos/{args.owner}/{args.repo}/pulls/{args.pr}/files", paginate=True, dry_run=args.dry_run)
    if err:
        sys.exit(f"could not fetch PR diff to validate anchors: {err}")
    valid_lines = added_lines_by_file(files or [])

    anchors, texts = set(), set()
    if args.mode == "direct":
        anchors, texts = already_published(
            args.owner, args.repo, args.pr, current_login(args.dry_run), args.dry_run
        )

    comments, general_notes, skipped = [], [], []
    for item in notes:
        text = item["note"]
        anchored = not item.get("general") and "new_line" in item
        if anchored and int(item["new_line"]) not in valid_lines.get(item["new_path"], set()):
            anchored = False  # doesn't land on an added line — no inline home
        anchor = (item["new_path"], int(item["new_line"])) if anchored else None

        if args.mode == "direct":
            if anchor and anchor in anchors:
                skipped.append(f"{anchor[0]}:{anchor[1]} (same line)")
                continue
            if normalize(text) in texts:
                skipped.append(f"{anchor[0]}:{anchor[1]} (identical text)" if anchor else "general (identical text)")
                continue

        if anchored:
            comments.append({
                "path": item["new_path"],
                "line": int(item["new_line"]),
                "side": "RIGHT",
                "body": with_marker(text),
            })
        else:
            general_notes.append(text)

    if args.mode == "draft":
        post_pending_review(args.owner, args.repo, args.pr, args.head_sha, comments, general_notes, args.dry_run)
        return

    posted_inline, posted_conversation = 0, 0
    for c in comments:
        _, err = gh_api(
            f"repos/{args.owner}/{args.repo}/pulls/{args.pr}/comments",
            method="POST",
            body={**c, "commit_id": args.head_sha},
            dry_run=args.dry_run,
        )
        if err:
            print(f"  {c['path']}:{c['line']} inline post failed ({err}) — falling back to a conversation comment")
            general_notes.append(c["body"])
            continue
        posted_inline += 1
        print(f"posted inline: {c['path']}:{c['line']}")

    for n in general_notes:
        _, err = gh_api(
            f"repos/{args.owner}/{args.repo}/issues/{args.pr}/comments",
            method="POST",
            body={"body": with_marker(n)},
            dry_run=args.dry_run,
        )
        if err:
            print(f"  conversation comment failed ({err}) — finding not posted: {normalize(n)[:60]}…")
            continue
        posted_conversation += 1
        print("posted to the conversation: 1 unanchored finding")

    print(f"posted:  {posted_inline} inline, {posted_conversation} in the conversation")
    if skipped:
        print(f"skipped: {len(skipped)} already on the PR")
        for s in skipped:
            print(f"  · {s}")

    if args.verdict != "none":
        apply_verdict(args.owner, args.repo, args.pr, args.head_sha, args.verdict, args.summary_file, args.dry_run)


if __name__ == "__main__":
    main()
