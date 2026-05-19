# Walkthrough: agent-teamflow on the todo-api

This walks through a realistic session on the `todo-api` Express app with two developers — Alice and Bob — each running their own Claude Code agent in parallel.

This example uses personal integration branches (`alice-staging`, `bob-staging`). That's one convention — not a requirement. See [SETUP.md](../../SETUP.md) for other branching models you can configure instead.

## Setup recap

The repo has this `.agent-teamflow`:

```json
{
  "issueTracker": "github",
  "project": "your-org/todo-api",
  "branches": {
    "main": "main",
    "staging": "staging"
  },
  "owners": {
    "alice": "alice-staging",
    "bob": "bob-staging"
  }
}
```

Branch structure:

```
feature/5-add-due-dates  ─┐
feature/6-add-tags        ─┤→ alice-staging ─┐
                                              ├→ staging → main
feature/7-search-filter   ─┐                 │
feature/8-pagination      ─┤→ bob-staging  ──┘
```

Skills resolve each developer's lane from `git config user.email`. `alice@company.com` strips to `alice`, which maps to `alice-staging`. Bob's maps to `bob-staging`. Teams without personal lanes omit `owners` entirely and features merge straight to `staging`.

---

## Step 1 — Alice files today's issues

Alice gives Claude a brain dump:

```
/issue add a due date field to todos, store as ISO string, expose via API
```

Claude reads `.agent-teamflow`, resolves Alice as assignee, drafts one issue, and asks for confirmation:

```
--- ISSUE 1 ---
TITLE: Add due date field to todos
TOUCHED FILES: src/index.js
---
## Context
The todo list has no time-awareness. Clients want to show overdue items.

## What to do
- Add `dueDate` (ISO 8601 string, nullable) to the todo object created in POST /todos
- Accept `dueDate` in the request body; validate it is a valid date string or null
- Return `dueDate` in all GET /todos and PATCH /todos/:id responses

## Acceptance criteria
- [ ] POST /todos accepts `{ title, dueDate }` and stores it
- [ ] GET /todos returns `dueDate` on each item
- [ ] PATCH /todos/:id accepts `{ dueDate }` to update the field
- [ ] Invalid date strings return 400

Create all / Edit first / Cancel
```

Alice clicks **Create all**. Issue #5 is filed and assigned to her.

She then runs:

```
/issue add a `tags` array to todos — support filtering GET /todos?tag=<name>
```

Issue #6 is filed (also assigned to Alice, same session).

---

## Step 2 — Bob dispatches a bigger batch

Bob has a larger feature set. He runs `/dispatch` with a brain dump:

```
/dispatch
alice: add search endpoint GET /todos?q=<text> — full text match on title
bob: add pagination to GET /todos — page + pageSize query params, return total count
bob: add a health check endpoint GET /health
```

Claude distributes the tasks, writes `docs/workflow/workflow-20240516-1030.md`, and files three issues:

- Issue #7 — assigned to Alice: "Add full-text search to GET /todos"
- Issue #8 — assigned to Bob: "Add pagination to GET /todos"
- Issue #9 — assigned to Bob: "Add GET /health endpoint"

---

## Step 3 — Alice and Bob resolve in parallel

Both open Claude Code in the same repo at the same time.

**Alice's terminal:**

```
/resolve
```

Claude fetches her open issues: #5, #6, #7. She picks #5 and #6. Claude checks whether `alice-staging` is behind `staging`, finds it's up to date, then spawns two parallel forks — each in its own git worktree:

```
Model assignments: #5 → sonnet, #6 → sonnet

Batch 1: 2 ready

| Issue | Model  | Status | Branch              | Files | Commit  | Summary                        |
|-------|--------|--------|---------------------|-------|---------|--------------------------------|
| #5    | sonnet | ready  | 5-add-due-dates     | 1     | a3f812c | feat(todos): add dueDate field |
| #6    | sonnet | ready  | 6-add-tags          | 1     | d91cc4a | feat(todos): add tags + filter |

MR/PR (alice-staging → staging): https://github.com/your-username/todo-api/pull/10

Worktrees still on disk:
  /tmp/todo-api-5-add-due-dates
  /tmp/todo-api-6-add-tags
```

**Bob's terminal (simultaneously):**

```
/resolve
```

Bob picks #8 and #9. Claude assigns both to sonnet, spawns two forks, and reports:

```
Batch 1: 2 ready

| Issue | Model  | Status | Branch              | Files | Commit  | Summary                              |
|-------|--------|--------|---------------------|-------|---------|--------------------------------------|
| #8    | sonnet | ready  | 8-pagination        | 1     | 7b2e019 | feat(todos): add pagination params   |
| #9    | sonnet | ready  | 9-health-check      | 1     | c44f231 | feat(api): add GET /health endpoint  |

MR/PR (bob-staging → staging): https://github.com/your-username/todo-api/pull/11
```

Neither developer touched the same file at the same time. No conflicts.

---

## Step 4 — Alice ships issue #7 from a worktree

Alice still has #7 open (full-text search). She navigates to a fresh worktree Claude Code session for that issue and implements it herself, then runs:

```
/git-auto-merge
```

Claude:
1. Commits her local changes
2. Pushes branch `7-search-filter` to origin
3. Merges it into `alice-staging` via a temp worktree (no-ff)
4. Updates the existing PR #10 with the new commit in its description

---

## Step 5 — Pre-production review before merging to staging

Before the team merges either PR to staging, Alice runs:

```
/prod-check
```

Claude scopes to her commits since midnight, diffs them, and cross-references callers across the whole repo:

```
| Severity | File:Line     | Risk                        | Why it matters                         | Suggested fix                    |
|----------|---------------|-----------------------------|----------------------------------------|----------------------------------|
| Warning  | src/index.js:8| dueDate not validated as ISO| Invalid strings stored silently        | Add Date.parse() check, return 400|
| Advice   | src/index.js:31| tags filter uses Array.includes| Case-sensitive match may surprise users| Lowercase both sides on compare  |
```

Alice fixes the validation gap, commits, and pushes. The PR updates automatically.

---

## Step 6 — Merge to staging and label issues

The team merges both PRs to staging via GitHub UI. Then Alice runs:

```
/post-merge
```

Claude scans the just-merged MR (#10), finds `Closes #5`, `Closes #6`, `Closes #7` in the description, and labels each issue `done-in-staging`. The issues are now visible in the "waiting for main" column.

Bob does the same after his PR (#11) merges.

---

## What this demonstrates

| Skill | What happened |
|---|---|
| `/issue` | Single-concern issues sized to one branch each — no overlap in `src/index.js` across sibling issues |
| `/dispatch` | Brain dump split across Alice and Bob with no cross-assignee blockers |
| `/resolve` | Alice and Bob each ran parallel forks simultaneously — four branches, zero conflicts |
| `/git-auto-merge` | Shipping from a worktree committed, pushed, and updated the PR in one command |
| `/prod-check` | Caught a missing validation before it hit staging |
| `/post-merge` | Issues labeled `done-in-staging` automatically after the PR merged |
