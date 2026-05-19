# Walkthrough: solo developer

One developer, one shared repo, no personal integration branches. Feature branches merge directly into `staging`, then `staging` flows to `main` on release.

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

No `owners` map. Skills fall back to `branches.staging` as the merge target for every command.

## Branch structure

```
feature/12-add-rate-limit ─┐
feature/13-fix-csv-export ─┼→ staging → main
feature/14-search-pagination ─┘
```

---

## Scenario — shipping a small batch of fixes

Sam runs a side project alone. They've got three things they want to land before tomorrow's release.

### Step 1 — File the issues

```
/issue add a rate limit to the public API — 60 req/min per IP, return 429 with Retry-After
```

Claude reads `.agent-teamflow`, resolves Sam as the current user (from `git config user.email`), and drafts a single issue. Sam reviews and clicks **Create all**. Issue #12 is filed.

Sam runs `/issue` two more times for the CSV export bug (#13) and the search pagination feature (#14).

### Step 2 — Resolve one issue at a time

```
/resolve
```

Claude lists Sam's three open issues. Sam picks #12 only — he wants to verify the rate-limit logic carefully before tackling the others.

Claude spawns **one** fork in an isolated worktree. The fork:

1. Branches `12-add-rate-limit` off `origin/staging` (no personal lane to fall back from)
2. Implements the rate limiter
3. Commits locally and reports back

Sam reviews the diff in the worktree, makes a small tweak, then runs:

```
/git-auto-merge
```

Because there's no `owners` entry for Sam, this skill resolves the integration branch as `staging` directly. It:

1. Pushes `12-add-rate-limit`
2. Merges it into `staging` via a temp worktree (no-ff)
3. Opens PR #20 (`staging` → `main`) with `Closes #12` in the body

### Step 3 — Knock out the other two in parallel

Back to the main repo. Sam runs `/resolve` again, picks #13 and #14, and Claude spawns two parallel forks. Both branch off `origin/staging` (now containing the rate-limit commit). Both come back ready.

Sam runs `/git-auto-merge` from each worktree. Each one pushes its feature branch and merges into `staging`. PR #20 auto-updates with the new commits and adds `Closes #13` and `Closes #14`.

### Step 4 — Pre-release safety check

Before merging PR #20 to `main`, Sam runs:

```
/prod-check
```

Claude scopes to Sam's commits since midnight, diffs them, and cross-references callers across the whole repo. It finds one Warning:

```
| Severity | File:Line          | Risk                            | Suggested fix                  |
|----------|--------------------|---------------------------------|--------------------------------|
| Warning  | src/middleware.js:8| Rate-limit map never evicts keys| Add TTL cleanup or use LRU map |
```

Sam fixes the leak, commits, runs `/git-auto-merge` again. PR #20 updates.

### Step 5 — Merge to main, then label

Sam merges PR #20 to `main` via the GitHub UI. Then:

```
/post-merge
```

Wait — for a solo developer, what does `/post-merge` do?

It looks for the most recent merged PR from `staging` → `main` (since there's no integration lane), reads `Closes #12`, `#13`, `#14` from the body, and labels each one `done-in-staging`. In the solo flow, `done-in-staging` is effectively a "shipped" marker — the issues will auto-close when the PR was merged, but the label still serves as a clean visual filter for "done" vs "in-flight" issues in the tracker.

If Sam wanted a different label name, he'd add `"labels": { "doneInStaging": "shipped" }` to his config.

---

## What this demonstrates

| Skill | Solo-mode behavior |
|---|---|
| `/issue` | Same as multi-dev — drafts one branch-sized issue per concern |
| `/resolve` | Forks branch off `staging` directly (no `owners` lookup match) |
| `/git-auto-merge` | Two-step flow becomes one: feature → `staging`, then PR to `main` |
| `/prod-check` | More valuable solo — no second pair of eyes, so the diff review fills the gap |
| `/post-merge` | Still useful as a "shipped" label even without integration lanes |

The takeaway: every skill works without `owners`. The config drops one field, the merge path collapses by one hop, everything else is identical.
