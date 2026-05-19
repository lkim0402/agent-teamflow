# resolve

Pick open issues assigned to you and implement them in parallel. Each issue gets its own worktree + branch. Stops at local commits — you run `/git-auto-merge` from each worktree to ship.

You orchestrate this command **in the main thread** (you need AskUserQuestion to interact with the user). Only the per-issue implementation work runs in parallel forks. Do not run this whole command as a forked agent.

---

## What this command does

1. Read `.agent-teamflow` and resolve the current owner + integration branch.
2. Fetch open issues assigned to that user (or use the `<id>` arg if given).
3. Let the user pick up to **3 issues** to tackle now.
4. Spawn one parallel fork per picked issue. Each fork:
   - runs in its own auto-created worktree (`isolation: "worktree"`)
   - creates a branch off `origin/<INTEGRATION_BRANCH>`
   - reads relevant context docs if your project has them
   - implements the issue
   - commits locally
   - reports back: branch name, worktree path, commit SHA, summary
5. Collect all results and show a summary table.
6. **Stop.** Do not push, do not open MRs. User runs `/git-auto-merge` from each worktree when ready.

## Input

`$ARGUMENTS`:
- empty → list mode (pick from open assigned issues)
- single integer `42` → skip picker, go straight to one fork for issue #42
- multiple integers `42 43 44` → skip picker, spawn one fork per issue (still capped at 3)

---

## Execution

### Step 1. Resolve current user and integration branch

**1a — Read config.** Read `.agent-teamflow` from the repo root. Extract `issueTracker`, `project`, `branches`, and `owners`.

**1b — User.** Run `git config user.email`, strip the domain to get the local part. Match against the `owners` map keys (case-insensitive). Fall back to `glab auth status` / `gh auth status` if needed. If both fail, stop and tell the user to configure `git config user.email`.

**1c — Integration branch.** Look up the user's shorthand in `owners` to get the candidate branch name. Check if `origin/<candidate>` exists:

```bash
git ls-remote --exit-code --heads origin <candidate>
```

If it exists, use it as `<INTEGRATION_BRANCH>`. If not, fall back to `branches.staging` and warn. Report which branch was resolved and why.

**1d — Optionally sync the integration branch from staging (ALWAYS ask the owner first).**

This step is **owner-gated**, not automatic. Before spawning any forks, check whether `origin/<branches.staging>` has commits beyond `origin/<INTEGRATION_BRANCH>`:

```bash
git fetch origin <branches.staging> <INTEGRATION_BRANCH>
git log origin/<INTEGRATION_BRANCH>..origin/<branches.staging> --oneline
```

- If the output is empty → already in sync. Print one line and proceed to Step 2.
- If non-empty → ask the owner (AskUserQuestion, single-select):
  - `Yes — sync now` (list first ~5 commit subjects in description)
  - `Skip — keep current state`

If `Yes`, sync via a temp worktree:

```bash
git worktree add /tmp/<INTEGRATION_BRANCH>-sync-wt origin/<INTEGRATION_BRANCH> -b <INTEGRATION_BRANCH>-sync-tmp
cd /tmp/<INTEGRATION_BRANCH>-sync-wt
git merge origin/<branches.staging> --no-edit
git push origin HEAD:<INTEGRATION_BRANCH>
cd -
git worktree remove /tmp/<INTEGRATION_BRANCH>-sync-wt
git branch -D <INTEGRATION_BRANCH>-sync-tmp
```

If `git merge` produces conflicts, stop and report — the owner must resolve manually.

### Step 2. Fetch open assigned issues (skip if ids in $ARGUMENTS)

```bash
# GitLab
glab issue list --assignee @me --output json

# GitHub
gh issue list --assignee @me --json number,title,url,labels,body
```

Parse the JSON. Capture `id/number`, `title`, `url`, `labels`, and the first 200 chars of `body` per issue.

**Filter out** any issue whose `labels` array contains `done-in-staging` (or your equivalent "already shipped" label). Those are waiting for the staging→main flow and have no remaining work.

Sort remaining issues by id ascending.

If the filtered list is empty: tell the user and stop.

### Step 3. Pick issues

**If ids were passed in $ARGUMENTS:** use those directly (cap at 3; if more, take the first 3 and tell the user).

**If list mode and ≤4 issues:** AaskUserQuestion with `multiSelect: true`, one option per issue. Label: `#<id> <title>` (truncate at ~60 chars). Description: first sentence of issue body. Question: "Which issues to tackle now? (max 3)"

**If list mode and >4 issues:** present a numbered list and ask the user to reply with comma-separated numbers. Parse the reply. Cap at 3.

If the user picks 0: stop, no-op.

### Step 3.5. Assign model per issue

Fetch the full issue body for each picked issue. Classify and assign a model — first match wins:

**Opus** — for complex, high-judgment work:
- Issue body > 500 characters, OR
- Labels contain any of: `complex`, `architecture`, `security`, `auth`, `refactor`, `migration`, `perf`, `performance`, OR
- Title or body contains (case-insensitive): `refactor`, `redesign`, `migrate`, `race condition`, `auth`, `permission`, `security`, `transaction`, `concurrent`

**Sonnet** — everything else (default).

Print a one-liner before spawning: e.g. `Model assignments: #42 → opus, #43 → sonnet`

### Step 4. Spawn parallel forks

Launch **all forks in a single message** using multiple `Agent` tool calls (no `subagent_type`; `isolation: "worktree"`). Each fork uses the model assigned in Step 3.5. Fill in the briefing template below per issue.

### Fork briefing template

```
You are implementing one issue end-to-end up to a local commit. You are running in a fresh git worktree. Do not push, do not open MRs/PRs, do not close the issue. Stop at the local commit.

## Config
Read `.agent-teamflow` from the repo root. Use `issueTracker`, `project`, and `branches` from it.

## Issue
- id: #<id>
- title: <title>
- url: <url>
- body:
<full issue body>

## Branch setup
1. `git fetch origin <INTEGRATION_BRANCH>`
2. `git checkout -b <id>-<short-slug-of-title> origin/<INTEGRATION_BRANCH>` (slug: lowercase, hyphenated, ≤30 chars, ASCII only)
3. Verify with `git status`.

## Context docs
If the project has per-area context documents (check CLAUDE.md for a routing table), read the relevant ones before touching code.

## Implement
- Make the changes required by the issue's acceptance criteria.
- Do NOT run the dev server (other forks are running in parallel; ports may collide).
- Type-check is fine; skip the full test suite to keep parallel runs sane.

## Commit
- `git add` only the files you intentionally changed (never blanket `-A`).
- Commit message format: `<type>(<scope>): <short summary> (#<id>)`. No emojis.

## Report back (mandatory final output)

STATUS: ready
ISSUE: #<id>
BRANCH: <branch-name>
WORKTREE: <absolute worktree path>
COMMIT: <SHA>
FILES: <count>
SUMMARY: <one-line description of what changed>
NOTES: <anything the user should know, or "none">

If you couldn't complete the work:

STATUS: blocked
ISSUE: #<id>
BRANCH: <branch-name or none>
WORKTREE: <path or none>
REASON: <what blocked you>

Never close the issue. Never push. Never run /git-auto-merge.
```

### Step 5. Collect (per batch) — terse one-liner only

When all forks return, parse each `STATUS:` block and push each fork's data to the **ready worktrees accumulator** (for ready) and a parallel **blocked/unknown** list. Print ONLY a terse one-liner:

`Batch <N>: <ready-count> ready[, <blocked-count> blocked][, <unknown-count> unknown]`

Examples:
- `Batch 1: 3 ready`
- `Batch 2: 2 ready, 1 blocked (#44)`

If any fork was blocked or returned unknown status, note it. The detailed reasons surface in Step 8's table.

### Step 6. Accumulate, then ask to continue

Maintain two session-scoped sets:
- **processed ids** — every id that hit step 4 (whether ready / blocked / unknown).
- **ready worktrees** — every fork that returned `STATUS: ready`.

Re-fetch open assigned issues. Apply the same label filter as Step 2. Subtract processed ids → **remaining queue**.

- **Queue empty** → fall through to Step 7.
- **Queue has 1+ issues** → AskUserQuestion (single-select):
  - `Yes — pick from remaining`
  - `Stop — proceed to merge step`
  - `Yes` → loop back to Step 3. Skip Step 1.
  - `Stop` → fall through to Step 7.

### Step 7. Final merge phase

Skip entirely if the ready-worktrees accumulator is empty.

#### 7a. Pre-merge summary table

Show what's about to be merged. For each ready worktree, run `git -C <worktree-path> diff --stat origin/<INTEGRATION_BRANCH>..HEAD`:

```
Pre-merge summary (vs origin/<INTEGRATION_BRANCH>):

| Issue | Branch           | Files | +/- lines | Changed paths (top 3) |
|-------|------------------|-------|-----------|------------------------|
| #21   | 21-fix-tooltip   | 2     | +15 / -3  | src/components/X.tsx   |
```

#### 7b. Merge confirmation

AskUserQuestion (single-select):
- `Merge all (default)` — batch-merge every ready worktree
- `Pick specific subset` — follow-up multi-select
- `Skip — don't merge any`

#### 7c. Batch-merge execution

Capture `PRE_MERGE_HEAD` first:
```bash
git fetch origin <INTEGRATION_BRANCH>
PRE_MERGE_HEAD=$(git rev-parse origin/<INTEGRATION_BRANCH>)
```

1. For each selected worktree, push its feature branch:
   ```bash
   git -C <worktree-path> push -u origin <branch-name>
   ```

2. Set up ONE temp worktree on `origin/<INTEGRATION_BRANCH>`:
   ```bash
   git worktree add /tmp/<INTEGRATION_BRANCH>-batch-wt origin/<INTEGRATION_BRANCH> -b <INTEGRATION_BRANCH>-batch-tmp
   ```

3. Sequentially merge each feature branch with `--no-ff`:
   ```bash
   cd /tmp/<INTEGRATION_BRANCH>-batch-wt
   # for each <feature-branch>:
   IID=$(echo "<feature-branch>" | grep -oE '^[0-9]+' | head -1)
   MSG="merge <feature-branch> (closes #${IID}) into <INTEGRATION_BRANCH>"
   git fetch origin <feature-branch>
   git merge --no-ff -m "$MSG" origin/<feature-branch>
   git push origin HEAD:<INTEGRATION_BRANCH>
   ```
   If any merge conflicts: STOP, report which branch failed, do NOT continue.

4. Clean up:
   ```bash
   git worktree remove /tmp/<INTEGRATION_BRANCH>-batch-wt
   git branch -D <INTEGRATION_BRANCH>-batch-tmp
   ```

5. ONE fork creates/updates the MR/PR:
   ```
   You are creating/updating a single MR/PR. All feature branches are already merged into <INTEGRATION_BRANCH>.

   Config: read `.agent-teamflow`. Use `issueTracker`, `project`, `branches`.

   1. Detect linked issues via `git log origin/<branches.staging>..origin/<INTEGRATION_BRANCH> --format=%B` grep `#(\d+)`. Also scan branch names for `<digits>-` prefix.
      Union, dedupe, verify each exists — drop 404s, never fabricate.
   2. Check for an existing open MR/PR from <INTEGRATION_BRANCH> → <branches.staging>.
   3. If none: create one. If one exists: update the description.
   4. Description: commit summary block, then a `## Linked issues` section with one `Closes #<id>` per verified id.
   5. Report ONLY the MR/PR URL.

   Never push to <branches.main>. No emojis.
   ```

#### 7d. (Optional) Post-merge checks

After merges, ask:
- `Skip (default)`
- `Type-check only`
- `prod-check only`
- `Both`

If anything selected, spawn ONE fork scoped to `PRE_MERGE_HEAD..origin/<INTEGRATION_BRANCH>`:

```
Run post-merge checks on the just-merged commits only (not all integration-branch work).

Context:
- Integration branch: <INTEGRATION_BRANCH>
- PRE_MERGE_HEAD: <SHA>
- Diff to check: <PRE_MERGE_HEAD>..origin/<INTEGRATION_BRANCH>
- Checks requested: <type-check | prod-check | both>

Steps:
1. `git fetch origin <INTEGRATION_BRANCH>`.
2. If type-check: run the project's typecheck script. Note pre-existing failures separately.
3. If prod-check: follow skills/prod-check.md, scoped to the diff range above.
4. Report:
   STATUS_TYPECHECK: pass | fail | not-run
   STATUS_PRODCHECK: clean | warnings | blockers | not-run
   DETAILS: <multiline; first 15 lines on non-pass>

No emojis. Do not modify files. Do not commit. Do not push.
```

### Step 7.5. Clean up merged worktrees + branches (with approval)

Ask for explicit approval before deleting anything. List every item by exact name/path.

AskUserQuestion (single-select):
- `Approve full cleanup` — description lists EACH worktree path AND EACH branch by exact name
- `Branches only — keep worktrees`
- `Skip — clean up manually later`

If approved, execute in this order:
1. Remote branches: `git push origin --delete <branch>`
2. Worktrees (full cleanup only): `git -C <parent-repo> worktree remove -f -f <path>`
3. Local branches: `git -C <parent-repo> branch -D <branch>`

### Step 8. Final summary

Display ONCE at the very end — a single consolidated table:

```
| Issue | Model  | Status  | Branch         | Files | Commit  | Merge      | Cleanup      | Summary                      |
|-------|--------|---------|----------------|-------|---------|------------|--------------|------------------------------|
| #13   | sonnet | ready   | 13-fix-tooltip | 2     | abc123d | merged     | branch+wt rm | Fixed tooltip overlap        |
| #14   | opus   | blocked | -              | -     | -       | -          | -            | Build error — see fork notes |
```

After the table:
```
MR/PR (<INTEGRATION_BRANCH> → <branches.staging>):
  <URL> — or "no merges performed"

Worktrees still on disk:
  <paths, if any remain>

Queue:
  Done — no remaining open issues.
  (or: "X issues remain — run /resolve again when ready.")
```

---

## Hard rules

- **Cap at 3 parallel implementation forks** — never more.
- **Main thread does no implementation** — only orchestration.
- **Implementation forks must not push, create MRs/PRs, or close issues.**
- **Step 7 batch-merge in main thread, MR/PR step in ONE fork.**
- **No emojis** anywhere.
- **Worktree isolation is non-negotiable for implementation forks.**

## Error handling

- Issue list fetch fails → report the error, stop.
- User picks 0 issues → no-op, exit cleanly.
- Fork returns `STATUS: blocked` → note in Step 5's one-liner, capture reason for Step 8's table. Do not auto-retry.
- Fork returns malformed output → mark as `STATUS: unknown`, surface its last 200 chars in Step 8's table.
