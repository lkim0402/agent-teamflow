---
description: Pick open issues assigned to you and implement them in parallel. Each gets its own worktree + branch. Stops at local commits — run /git-auto-merge to ship.
---

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below.

# resolve

Pick open issues assigned to you and implement them in parallel. Each issue gets its own worktree + branch. Stops at local commits — you run `/git-auto-merge` from each worktree to ship.

Orchestrate this workflow in the main conversation because it needs user interaction. Only the per-issue implementation work may run in isolated workers.

---

## What this command does

1. Read `.agent-teamflow` and resolve the current owner + integration branch.
2. Fetch open issues assigned to that user (or use the `<id>` arg if given).
3. Show the queue with effort tiers (XS → XL) and let the user pick up to **3 issues**.
4. Start one isolated implementation worker per picked issue when the current agent runtime supports parallel workers. Each worker:
   - runs in its own worktree
   - creates a branch off `origin/<INTEGRATION_BRANCH>`
   - reads relevant context docs if your project has them
   - implements the issue
   - commits locally
   - reports back: branch name, worktree path, commit SHA, summary
5. Collect all results and show a summary table.
6. **Stop.** Do not push, do not open MRs. User runs `/git-auto-merge` from each worktree when ready.

## Quiet execution (applies to every step)

The questions, queue overviews, and summary tables below are the *intended* user-facing surface of this command. Everything else — the plumbing — should produce as little transcript noise as possible. These rules bind the **main conversation** and **plumbing-only workers** (the MR/PR worker, the post-merge check worker). They do NOT apply to implementation workers — their granular tool calls never enter the main transcript and are useful progress/debugging signal:

- **Batch commands.** Where a step lists several shell commands, run them as ONE shell call (joined with `&&` or a small inline script), not one tool call per line. One step ≈ one shell call.
- **Quiet flags.** Always use `git fetch -q`, `git push -q`, `git merge -q`, `git checkout -q`, and `git worktree add/remove` with stdout discarded where safe. Errors still surface on stderr — that's what we want.
- **Never dump raw JSON.** Request only the fields a step needs. `gh`'s `--json <fields>` flag already does this; pipe `glab ... --output json` through `jq`, e.g.:

  ```bash
  glab issue list --assignee @me --output json \
    | jq -c 'map({iid, title, web_url, labels, description})'
  ```

  Keep the issue body (`description`/`body`) IN FULL — Step 2's effort scoring needs the whole body (file-path token count, >1500-char rule). The noise being cut is the rest of the payload (author/assignee objects, timestamps, counters), not the body. In Step 3.5, fetch a picked issue's body via `glab issue view <id> --output json | jq -r '.description'` / `gh issue view <id> --json body --jq '.body'`.
- **Suppress incidental output.** Append `>/dev/null` to commands whose stdout is irrelevant (push progress, worktree-add chatter). Never suppress stderr.
- **No play-by-play narration.** Don't print "Now fetching…", "Running git log…" between calls. Report only each step's *conclusion* (e.g. the resolved integration branch, the filtered queue) in the formats the steps below define.

## Input

`$ARGUMENTS`:
- empty → list mode (pick from open assigned issues)
- single integer `42` → skip picker, go straight to issue #42
- multiple integers `42 43 44` → skip picker, start one implementation worker per issue when available (still capped at 3)

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

This step is **owner-gated**, not automatic. Before starting implementation workers, check whether `origin/<branches.staging>` has commits beyond `origin/<INTEGRATION_BRANCH>`:

```bash
git fetch origin <branches.staging> <INTEGRATION_BRANCH>
git log origin/<INTEGRATION_BRANCH>..origin/<branches.staging> --oneline
```

- If the output is empty → already in sync. Print one line and proceed to Step 2.
- If non-empty → ask the owner (ask the user, single-select):
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

Parse the JSON (field-filtered per the Quiet execution section). Capture `id/number`, `title`, `url`, `labels`, and the **full** `body` per issue — the effort scoring below needs the whole body. Only ever *display* the first ~200 chars (picker descriptions, overviews).

**Filter out** any issue whose `labels` array contains the `labels.doneInStaging` value from `.agent-teamflow` (default `done-in-staging`). Those are waiting for the staging→main flow and have no remaining work.

**Also filter out in-flight issues** — work already merged into `<INTEGRATION_BRANCH>` but not yet labeled because the MR/PR hasn't merged to staging yet. Without this, running `/resolve` shortly after a session would resurface issues whose implementation is already on the integration branch.

Detection: scan commit messages on `origin/<INTEGRATION_BRANCH>` since `origin/<branches.staging>` for `#<id>` references:

```bash
git fetch origin <branches.staging> <INTEGRATION_BRANCH>
in_flight_ids=$(git log origin/<branches.staging>..origin/<INTEGRATION_BRANCH> --format=%B \
                | grep -oE '#[0-9]+' | tr -d '#' | sort -u)
```

Drop any issue whose id is in `in_flight_ids`.

Sort remaining issues by id ascending. If the filtered list is empty: tell the user and stop.

**Compute effort tier per issue.** For each remaining issue, derive a score from the title and full body — no extra API call needed.

Scoring (apply all rules, sum the points):

- **file_paths** — count distinct file-path-like tokens in the body. A token counts if it ends in `.ts` / `.tsx` / `.js` / `.jsx` / `.py` / `.go` / `.rs` / `.sql` / `.md` / `.json`, OR starts with `src/` / `lib/` / `apps/` / `packages/` / `docs/`. Cap at 25.
- **db_layer** — `+3` if body contains any of: `migration`, `schema`, `join table`, `backfill`, `ALTER TABLE`, `CREATE TABLE`, `unique index`, `seed`.
- **cross_layer** — `+2` if body mentions 2 or more of: `router`, `schema`, `component`, `page`, `middleware`, `api`, `service`, `model`, `controller`, `view`.
- **body_length** — `+1` if body > 1500 chars.

Tier mapping:

| score | tier | rough estimate |
|-------|------|----------------|
| ≤2    | XS   | ~5 min         |
| 3–5   | S    | ~15 min        |
| 6–9   | M    | ~30 min        |
| 10–14 | L    | ~60 min        |
| 15+   | XL   | ~2 hr+         |

Store `{ id, tier, score }` per issue for use in Steps 2.5 and 3.

### Step 2.5. Queue overview

Before the picker, print a plain-text overview of every issue in the filtered queue with its tier. Sorted by id descending (newest first):

```
Queue overview (N issues):

  #<id>  <tier>  <estimate>   <title (truncated to ~60 chars)>
  ...

Total estimated time: ~<sum> min
```

For the total, use the midpoint of each tier's range (XS=5, S=15, M=30, L=60, XL=120 minutes).

### Step 3. Pick issues

**If ids were passed in $ARGUMENTS:** use those directly (cap at 3; if more, take the first 3 and tell the user).

**If list mode and ≤4 issues:** ask the user with `multiSelect: true`, one option per issue. Label: `#<id> <tier> ~<estimate> — <title>` (truncate title so full label stays ≤70 chars). Description: first sentence of issue body. Question: "Which issues to tackle now? (max 3)"

**If list mode and >4 issues:** show the 4 newest (sort by id descending) as AskUserQuestion options using the same label format. List older issues in the question text so the user can reference them via the auto-added "Other" free-text input. Parse "Other" as comma- or space-separated ids. Merge with multiSelect picks, dedupe, cap at 3. Warn if any "Other" id isn't in the current queue.

If the user picks 0: stop, no-op.

### Step 3.5. Confirm effort and assign model per issue

For each picked issue, fetch the full body if not already available (only ids passed via `$ARGUMENTS` skip Step 2 — queue picks already carry full bodies):

```bash
# GitLab
glab issue view <id> --output json | jq '{iid, title, description, labels}'

# GitHub
gh issue view <id> --json number,title,body,labels
```

Score any just-fetched issue using the Step 2 rules; issues picked from the queue keep their Step 2 full-body score. Store `{ id, tier, score }` for each.

Print a one-liner before spawning workers: e.g. `Effort tiers: #42 -> M (~30 min), #43 -> XS (~5 min)`

**Assign a model per issue (only if the runtime supports per-worker model selection — e.g. Claude Code's Agent tool; skip this entirely on runtimes that don't, like Codex).** Classify each issue and apply the rules in order — first match wins:

**Stronger model** (e.g. `model: "opus"`) — complex, high-judgment work:
- Issue body > 500 characters, OR
- Labels contain any of: `complex`, `architecture`, `security`, `auth`, `refactor`, `migration`, `perf`, `performance`, OR
- Title or body contains any of (case-insensitive): `refactor`, `redesign`, `migrate`, `race condition`, `auth`, `permission`, `security`, `transaction`, `concurrent`

**Default model** (e.g. `model: "sonnet"`) — everything else.

Record `{ id, model }` for each issue. Print a one-liner before spawning: e.g. `Model assignments: #42 → opus, #43 → sonnet`

### Step 4. Start implementation workers

Launch all implementation workers in parallel when the current agent runtime supports safe parallel work. Otherwise process the selected issues sequentially. Each worker uses the effort tier and model (if assigned) from Step 3.5 and the briefing template below.

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
If the project has per-area context documents (check AGENTS.md for a routing table), read the relevant ones before touching code.

## Implement
- Make the changes required by the issue's acceptance criteria.
- Do NOT run the dev server (other workers may be running in parallel; ports may collide).
- **Before committing, run the typecheck on the files you changed** (read the project's scripts — usually a `typecheck` script, or a lint script that includes it). If it reports errors in code you touched, fix them before reporting `STATUS: ready`. Typecheck is parallel-safe (reads files only, no DB/port). Still skip the full test suite — that runs once post-merge.

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

When all implementation workers return, parse each `STATUS:` block and push each worker's data to the **ready worktrees accumulator** (for ready) and a parallel **blocked/unknown** list. Print ONLY a terse one-liner:

`Batch <N>: <ready-count> ready[, <blocked-count> blocked][, <unknown-count> unknown]`

Examples:
- `Batch 1: 3 ready`
- `Batch 2: 2 ready, 1 blocked (#44)`

If any worker was blocked or returned unknown status, note it. The detailed reasons surface in Step 8's table.

### Step 6. Accumulate, then ask to continue

Maintain two session-scoped sets:
- **processed ids** — every id that hit step 4 (whether ready / blocked / unknown).
- **ready worktrees** — every worker that returned `STATUS: ready`.

Re-fetch open assigned issues. Apply the same label filter as Step 2. Subtract processed ids → **remaining queue**.

- **Queue empty** → fall through to Step 7.
- **Queue has 1+ issues** → ask the user (single-select):
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

ask the user (single-select):
- `Merge all (default)` — batch-merge every ready worktree
- `Pick specific subset` — follow-up multi-select
- `Skip — don't merge any`

#### 7c. Batch-merge execution

**Staging-drift re-check first (mid-session fix guard).** The Step 1d sync is a point-in-time snapshot of `<branches.staging>` taken at session start. If a fix lands on staging *during* the session (e.g. someone else ships a hotfix the workers' work depends on or conflicts with), the workers built on a now-stale base and the integration branch is missing it. Re-fetch and compare before merging:

```bash
git fetch origin <branches.staging> <INTEGRATION_BRANCH>
git log origin/<INTEGRATION_BRANCH>..origin/<branches.staging> --oneline
```

If the output is non-empty, staging advanced since the session-start sync. Ask the owner (single-select): "`<branches.staging>` gained N commit(s) since this session started — re-sync into `<INTEGRATION_BRANCH>` before merging? (Avoids shipping work built on a stale base / inheriting bugs staging already fixed.)" Options: `Yes — re-sync now` (run the Step 1d temp-worktree merge, then continue) / `Skip — merge as-is`. If the output is empty, proceed silently.

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

5. ONE isolated worker creates/updates the MR/PR:
   ```
   You are creating/updating a single MR/PR. All feature branches are already merged into <INTEGRATION_BRANCH>.

   Config: read `.agent-teamflow`. Use `issueTracker`, `project`, `branches`.

   1. Detect linked issues via `git log origin/<branches.staging>..origin/<INTEGRATION_BRANCH> --format=%B` grep `#(\d+)`. Also scan branch names for `<digits>-` prefix.
      Union, dedupe, verify each exists — drop 404s, never fabricate.
   2. Check for an existing open MR/PR from <INTEGRATION_BRANCH> → <branches.staging>.
   3. If none: create one. If one exists: update the description.
   4. Description: commit summary block, then a `## Linked issues` section with one `Closes #<id>` per verified id.
   5. Report ONLY the MR/PR URL.

   Never push to <branches.main>. Follow the Quiet execution rules: batch commands, -q flags, field-filtered tracker JSON. No emojis.
   ```

#### 7d. (Optional) Post-merge checks

After merges, ask:
- `Skip (default)`
- `Type-check only`
- `prod-check only`
- `Both`

If anything selected, start ONE isolated worker scoped to `PRE_MERGE_HEAD..origin/<INTEGRATION_BRANCH>`:

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
3. If prod-check: follow the prod-check workflow (the /prod-check command or prod-check skill), scoped to the diff range above.
4. Report:
   STATUS_TYPECHECK: pass | fail | not-run
   STATUS_PRODCHECK: clean | warnings | blockers | not-run
   DETAILS: <multiline; first 15 lines on non-pass>

No emojis. Do not modify files. Do not commit. Do not push.
```

Display the findings inline, noting the scope (`<PRE_MERGE_HEAD short SHA>..<INTEGRATION_BRANCH>`, this session only). The MR/PR is **still open**. If checks are green, fall through to Step 7.5 (cleanup).

**If checks failed or prod-check reported blockers**, do NOT silently fall through. Ask the user (single-select):

- `Ignore — proceed to cleanup (default)` — the result ships as-is; fix later
- `Fix now` — start ONE isolated worker to fix on `<INTEGRATION_BRANCH>`, then re-run the same checks
- `Hold — stop here` — leave the MR/PR open, skip cleanup (Step 7.5) and local sync (Step 7.7), go straight to Step 8 so worktrees stay on disk for manual inspection

**On `Fix now` — bounded fix loop (max 2 attempts):**

1. Set up a temp worktree on the integration branch tip (fixes belong on the integration branch, since that's what the MR/PR ships — not on the soon-to-be-cleaned feature worktrees):
   ```bash
   git fetch origin <INTEGRATION_BRANCH>
   git worktree add /tmp/<INTEGRATION_BRANCH>-fix-wt origin/<INTEGRATION_BRANCH> -b <INTEGRATION_BRANCH>-fix-tmp
   ```
2. Start ONE isolated worker (cwd = the temp fix worktree) with: the failing check output, the diff scope `<PRE_MERGE_HEAD>..origin/<INTEGRATION_BRANCH>`, and instructions to fix ONLY the failure, commit with `fix(<scope>): <summary>`, push to `<INTEGRATION_BRANCH>` (the MR/PR auto-updates), and report `STATUS: fixed` or `STATUS: blocked`.
3. Clean up the temp fix worktree:
   ```bash
   git worktree remove -f /tmp/<INTEGRATION_BRANCH>-fix-wt
   git branch -D <INTEGRATION_BRANCH>-fix-tmp
   ```
4. Re-run the post-merge checks on the new tip.
5. **Green now** → fall through to Step 7.5. **Still failing and attempts < 2** → loop back to 1. **Still failing after 2 attempts OR the fix worker returned `STATUS: blocked`** → STOP looping, report the remaining failure, and behave like `Hold` (skip 7.5/7.7, jump to Step 8) so the user takes over manually.

The 2-attempt cap is mandatory — never loop indefinitely on a failure the worker can't crack.

### Step 7.5. Clean up merged worktrees + branches (with approval)

Ask for explicit approval before deleting anything. List every item by exact name/path.

ask the user (single-select):
- `Approve full cleanup` — description lists EACH worktree path AND EACH branch by exact name
- `Branches only — keep worktrees`
- `Skip — clean up manually later`

If approved, execute in this order:
1. Remote branches: `git push origin --delete <branch>`
2. Worktrees (full cleanup only): `git -C <parent-repo> worktree remove -f -f <path>`
3. Local branches: `git -C <parent-repo> branch -D <branch>`

### Step 7.6. Continue with another batch?

After cleanup, re-fetch the queue. If issues remain, offer to start another batch in the same session instead of making the user re-run `/resolve`.

**7.6a — Re-fetch + filter + re-score.** Run Step 2's full pipeline:
- Fetch open assigned issues.
- Drop `done-in-staging`-labeled issues.
- Drop in-flight ids (re-scan `origin/<branches.staging>..origin/<INTEGRATION_BRANCH>`).
- Subtract the session's processed-ids set (so blocked/unknown issues from earlier batches don't resurface).
- Compute effort tier per remaining issue.

**Skip Step 7.6 entirely** if the resulting queue is empty — go straight to Step 8.

**7.6b — Show the remaining queue overview** (same format as Step 2.5):

```
Batch <N> shipped → MR/PR <url> updated, worktrees cleaned.

<M> issue(s) remain in your queue:

  #<id>  <tier>  <estimate>   <title>
  ...

Total estimated time: ~<sum> min
```

**7.6c — Ask whether to continue** (ask the user, single-select):
- `Yes — start another batch` (description: lists up to 3 of the remaining issues inline)
- `No — done for now` (description: "Falls through to the final summary; re-run /resolve later.")

**7.6d — On `Yes`**: loop back to Step 3. Do NOT re-run Steps 1 or 2. The session's processed-ids and ready-worktrees accumulators carry forward.

**7.6e — On `No`**: fall through to Step 7.7.

### Step 7.7. Sync local checkout to origin

The batch-merge in Step 7c uses a temp worktree — the user's main checkout is intentionally untouched. After merging, offer to pull so the dev server can pick up the new code.

**Skip Step 7.7 entirely** if Step 7b's choice was `Skip` (no merges happened).

**7.7a — Detect main checkout state.** Derive the parent repo from a ready worktree (`git -C <worktree-path> rev-parse --git-common-dir | xargs dirname`), then:

```bash
git -C $MAIN_REPO symbolic-ref --short HEAD
git -C $MAIN_REPO status --porcelain
git -C $MAIN_REPO rev-list --count HEAD..origin/<INTEGRATION_BRANCH>
```

- **On integration branch + clean + behind ≥1 commit** → ask, default Yes.
- **On integration branch + dirty** → ask, warn pull may merge on top of local changes.
- **Not on integration branch** → print a note and skip the prompt.
- **Already up to date** → print one line and skip the prompt.

**7.7b — Ask (if applicable)** (ask the user, single-select):
- `Yes — pull now` (description: first ~3 incoming commit subjects)
- `Skip — pull manually later` (description: `git pull --no-rebase origin <INTEGRATION_BRANCH>`)

**7.7c — On `Yes`**: run `git -C $MAIN_REPO pull --no-rebase origin <INTEGRATION_BRANCH>`. If conflicts, stop and report. On success: `Local checkout synced to <new HEAD short SHA>.`

**7.7c-bis — New-migration guard (local DB schema).** Code reaches the local checkout via the pull, but DB migrations are typically applied by CI on deploy — NOT locally. A freshly-pulled feature that added a column will have the code but not the schema, and any query touching it fails locally. After a successful pull, detect whether the pulled diff added a migration:

```bash
git -C $MAIN_REPO diff --name-only <pre-pull HEAD>..HEAD \
  | grep -E '(migrations?/.*\.(sql|ts|js|py)$|db/migrate/|alembic/versions/)'
```

If it matches, the local DB is now behind the schema. Find the project's migrate command (check package.json scripts / Makefile / project docs — e.g. a `db:migrate` script) and ask (single-select): "This pull added a new DB migration (`<migration name>`). Apply it to your local DB so the merged feature is testable locally?" Options: `Yes — run <migrate command>` (default) / `Skip — apply manually later` (note: features hitting the new column/table will error locally until applied). On `Yes`, run it from `$MAIN_REPO` and confirm completion. If no migration was added or the project has no migration setup, skip this step silently.

**7.7d — On `Skip`**: print `Local checkout is N commits behind — pull when ready.` and fall through.

### Step 8. Final summary

Display ONCE at the very end — a single consolidated table:

```
| Issue | Tier | Status  | Branch         | Files | Commit  | Merge      | Cleanup      | Summary                        |
|-------|------|---------|----------------|-------|---------|------------|--------------|--------------------------------|
| #13   | XS   | ready   | 13-fix-tooltip | 2     | abc123d | merged     | branch+wt rm | Fixed tooltip overlap          |
| #14   | M    | blocked | -              | -     | -       | -          | -            | Build error — see worker notes |
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

- **Cap at 3 parallel implementation workers** — never more.
- **Main thread does no implementation** — only orchestration.
- **Implementation workers must not push, create MRs/PRs, or close issues.**
- **Step 7 batch-merge in main thread, MR/PR step in ONE worker.**
- **No emojis** anywhere.
- **Quiet plumbing** — follow the "Quiet execution" section: one shell call per step, `-q` flags, field-filtered tracker JSON, no narration between calls. The user-facing surface is the questions + tables only.
- **Worktree isolation is non-negotiable for implementation workers.**

## Error handling

- Issue list fetch fails → report the error, stop.
- User picks 0 issues → no-op, exit cleanly.
- Worker returns `STATUS: blocked` → note in Step 5's one-liner, capture reason for Step 8's table. Do not auto-retry.
- Worker returns malformed output → mark as `STATUS: unknown`, surface its last 200 chars in Step 8's table.

Arguments: $ARGUMENTS
