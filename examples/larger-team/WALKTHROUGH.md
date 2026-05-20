# Walkthrough: larger team, shared staging (no personal lanes)

Four developers, one shared `staging` branch. Every feature branch merges directly into `staging`. No personal integration branches — the team has decided the per-developer lane overhead isn't worth it for their flow.

This is a common setup. It works fine with agent-teamflow **as long as `/issue` is doing its job of sizing issues so they don't touch overlapping files**. When everyone merges to the same branch, branch-sizing is what keeps batch-merges from imploding.

## Config

```json
{
  "issueTracker": "github",
  "project": "your-org/your-repo",
  "branches": {
    "main": "main",
    "staging": "staging"
  }
}
```

No `owners` map. When a developer runs `/git-auto-merge` or `/resolve`, the skills look them up in `owners`, find nothing, and fall back to `branches.staging` (with a warning). Every feature branch merges straight to `staging`.

## Branch structure

```
feature/30-search-tokenizer    ─┐
feature/31-export-csv          ─┤
feature/32-admin-audit-log     ─┼→ staging → main
feature/33-webhook-retry       ─┤
feature/34-2fa-recovery        ─┘
```

The team: Alice, Bob, Carol, Dan. Each works on independent areas.

---

## Scenario — coordinating a four-person sprint

### Step 1 — Dan files the sprint

Dan is leading this sprint. He runs:

```
/dispatch /tmp/sprint-brief.md
```

The brief lists five separate features. The agent reads `.agent-teamflow`, finds no `owners` map, and asks Dan for the assignee aliases to distribute across — Dan provides `alice,bob,carol,dan`. The agent splits the work:

- #30 — Alice: "Tokenize search input for partial word matches"
- #31 — Bob: "Add CSV export to the orders report"
- #32 — Carol: "Admin audit log for permission changes"
- #33 — Bob: "Retry failed webhooks with exponential backoff"
- #34 — Dan: "2FA recovery codes — generate, store, redeem"

A workflow log is written to `docs/workflow/workflow-20260519-0900.md` and committed. (If the team prefers a different path, they'd set `"paths": { "workflowDir": ".sprints" }` in their config.)

### Step 2 — Parallel resolve across the team

All four developers run `/resolve` in their own terminals over the next hour.

**Alice's resolve:**

```
/resolve
```

The agent looks up Alice in `owners` — not found. It falls back to `staging`, warns Alice that `<INTEGRATION_BRANCH>` resolved to `staging` (the shared branch), and asks if she wants to sync. She clicks **Yes**. The worker branches `30-search-tokenizer` off `origin/staging` and implements.

**Bob's resolve** (he has two issues — #31 and #33):

Same fallback. two workers spawn off `origin/staging`. They branch as `31-export-csv` and `33-webhook-retry`. Both implement against the same base.

**Carol's** and **Dan's** runs are identical in structure.

### Step 3 — Why branch-sizing matters here

Each developer ran `/git-auto-merge` independently from their worktree. Each one:

1. Pushes their feature branch
2. Merges directly into `staging` via a temp worktree (no-ff)
3. The PR title becomes `<feature-branch> → staging`; description lists `Closes #N`

There is no integration-branch buffer. If two issues had been drafted to touch `src/auth/middleware.ts`, the second `/git-auto-merge` would have hit a merge conflict.

This is exactly why `/issue` enforces branch-sizing — same file goes into same chunk. In a shared-staging team, this rule is load-bearing rather than nice-to-have.

### Step 4 — Pre-release `/prod-check` becomes critical

Before the next release window, **someone needs to run `/prod-check`** scoped to all five commits — not just their own. The scope flag supports a commit range:

```
/prod-check 1a2b3c4..HEAD
```

Where `1a2b3c4` is the merge base from the last release. The agent diffs all five features together and cross-references callers across the whole repo. It catches a real one:

```
| Severity | File:Line                | Risk                                          | Suggested fix                       |
|----------|--------------------------|-----------------------------------------------|-------------------------------------|
| Critical | src/auth/codes.ts:42     | 2FA recovery codes stored unhashed in DB      | bcrypt on write; verify with compare|
| Warning  | src/exports/csv.js:18    | Streams large queries without LIMIT/cursor    | Add cursor pagination               |
| Advice   | src/webhooks/retry.ts:30 | Jitter range too narrow under high concurrency| Widen jitter to ±25%                |
```

Dan files a hotfix issue (#35), assigns it to himself, and runs `/resolve 35` — straight to one worker, skipping the picker. The hashing fix lands within an hour, in a new feature branch off the latest `staging`.

### Step 5 — Merge to main and label

After release-day testing, the release manager merges `staging` → `main`. Each developer runs `/post-merge` to label their issues `done-in-staging`. (Auto-close fires from the `Closes #N` references in each individual PR's body once those PRs are present in `main`.)

---

## What this demonstrates

| Skill | Shared-staging behavior |
|---|---|
| `/dispatch` | Same as small-team — needs explicit assignee list when `owners` is absent |
| `/resolve` | Falls back to `staging` as `<INTEGRATION_BRANCH>`, warns the developer |
| `/git-auto-merge` | Merges feature directly into `staging`, opens PR `feature → staging` |
| `/issue` | **Most important here** — branch-sizing prevents serial-conflict cascades |
| `/prod-check` | The team's main pre-release gate — used at sprint-end, not per-developer |
| `/post-merge` | Same as elsewhere — `done-in-staging` label until `main` flow |

## When to graduate to personal lanes

This team chose shared staging for simplicity. If they hit any of these, they should consider adding `owners`:

- **Two developers regularly need work-in-progress to live somewhere** that survives a `git push` without polluting `staging`.
- **`/resolve` syncs from `staging`** start picking up half-merged work that breaks the worker's branch.
- **Pre-release `/prod-check`** gets noisy because everyone's commits are interleaved.

When that happens, see [`small-team/`](../small-team/) for the personal-lanes setup.
