---
name: post-merge
description: Use when the user explicitly selects the post-merge skill or wants to label linked issues after merging an integration-to-staging MR/PR.
---

# post-merge

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below. Treat the user's remaining request text as `$ARGUMENTS`.

---

After merging an integration→staging MR/PR, label its linked issues with the configured "done in staging" label so the issue tracker shows the work has reached staging. Issues stay open until staging→main triggers the tracker's native auto-close.

Run this workflow in an isolated worker if the current agent runtime supports one; otherwise run it in the main session. Keep CLI output concise and report only the final summary.

The label name is read from `.agent-teamflow` at `labels.doneInStaging`. If unset, default to the string `done-in-staging`. All references to `<DONE_LABEL>` below resolve to that value.

## Prerequisite

**The MR/PR must already be MERGED.** This skill refuses to operate on:
- MRs/PRs still in `opened`/`open` state — not merged yet
- MRs/PRs in `closed` state — closed-without-merging; no code reached staging

Only `merged` is acceptable. Run this **after** you manually merge in the UI.

## What this command does

1. Find the merged MR/PR to operate on.
2. Parse `Closes #<id>` references from its description.
3. Ensure the `<DONE_LABEL>` label exists in the project (create if missing).
4. Add the label to each linked issue. Idempotent — re-running is safe.
5. Stop. Does NOT close issues. Does NOT merge anything. Does NOT touch branches.

## Input

`$ARGUMENTS`:
- **empty** → find the most recently merged MR/PR (source=`<INTEGRATION_BRANCH>`, target=`<branches.staging>`) by the current user within the last 6 hours.
- **single integer `<id>`** → operate on that specific MR/PR (must be merged).

## Setup

Read `.agent-teamflow` from the repo root. Extract `issueTracker`, `project`, `branches`, `owners`, and `labels.doneInStaging` (default `done-in-staging` if missing) — refer to it as `<DONE_LABEL>` below. Resolve `<INTEGRATION_BRANCH>` using the same owner-resolution logic as `git-auto-merge` Step 0.

## Label spec

- **Name:** `<DONE_LABEL>`
- **Color:** `#36cd96` (green)
- **Description:** `MR/PR resolving this issue has been merged into staging. Will auto-close when staging → main flows.`

Check existence first, only create if missing:

```bash
# GitLab
glab api projects/<encoded-project>/labels | grep -q "<DONE_LABEL>" || \
glab api projects/<encoded-project>/labels --method POST \
  -f "name=<DONE_LABEL>" \
  -f "color=#36cd96" \
  -f "description=MR resolving this issue has been merged into staging."

# GitHub — uses labels on the repo
gh api repos/<project>/labels | grep -q "<DONE_LABEL>" || \
gh api repos/<project>/labels --method POST \
  -f "name=<DONE_LABEL>" \
  -f "color=36cd96" \
  -f "description=PR resolving this issue has been merged into staging."
```

## Execution

### Step 1. Find the MR/PR

If `$ARGUMENTS` empty:
```bash
# GitLab
glab mr list --merged --source-branch <INTEGRATION_BRANCH> --target-branch <branches.staging> --per-page 10 --output json

# GitHub
gh pr list --state merged --head <INTEGRATION_BRANCH> --base <branches.staging> --json number,title,mergedAt,author
```

Filter to MRs/PRs merged within the last 6 hours by the current user.
- Zero matches → exit with `No recently merged MR/PR found in the last 6 hours.`
- One match → use it.
- Multiple matches → ask the user single-select for the user to pick.

If `$ARGUMENTS` is a number: fetch that specific MR/PR and verify it is merged. Refuse if still open or closed-without-merging.

### Step 2. Extract linked ids

From the MR/PR description, grep for `Closes #(\d+)` (also match `Close|Closing|Fixes|Fix|Resolves`). Dedupe.

Verify each id exists. Drop any that 404. Never fabricate.

If no valid ids: exit with `MR/PR has no parseable linked issues. Nothing to label.`

### Step 3. Ensure label exists

(See label spec above.)

### Step 4. Apply label to each linked issue

```bash
# GitLab — additive, does not replace existing labels
glab api -X PUT projects/<encoded-project>/issues/<id> -f "add_labels=<DONE_LABEL>"

# GitHub
gh api repos/<project>/issues/<id>/labels --method POST -f "labels[]=<DONE_LABEL>"
```

Idempotent. Capture each call's status — note failures in the report but continue.

### Step 5. Report

```
MR/PR #<id> (<title>) — merged at <timestamp>

Linked issues labeled `<DONE_LABEL>`:
  #<id> <title>
  #<id> <title>

Failures (if any):
  #<id> — <error message>

Issues are still OPEN — will auto-close when staging → main flows.
```

## Constraints

- No emojis.
- **Never close issues** — only label.
- **Never merge MRs/PRs** — only consume already-merged ones.
- **Never delete branches or worktrees.**
- If CLI fails with auth/permission errors, report verbatim and stop.

## Typical usage sequence

```
/git-auto-merge     → push, merge into integration branch, open MR/PR
(you)               → review the MR/PR in the UI, merge it
/post-merge         → label all linked issues with <DONE_LABEL>
```
