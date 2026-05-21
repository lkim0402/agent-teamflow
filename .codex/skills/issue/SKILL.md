---
name: issue
description: Use when the user explicitly selects the issue skill or wants to create one or more branch-sized GitHub/GitLab issues from a brain dump; drafts, previews, then posts with confirmation.
---

# issue

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below. Treat the user's remaining request text as `$ARGUMENTS`.

---

Create one or more issues from a single brain dump. Splits the input into branch-sized chunks (so `/resolve` can pick each up as one worker/branch without batch-merge conflicts), drafts each, asks for confirmation, then posts.

**Why branch-sized:** `/resolve` treats each issue as one worktree + one branch. If two issues touch overlapping line ranges in the same file, the sequential batch-merge halts with a conflict. Scoping issues at branch granularity from the start prevents this.

The heavy work (splitting, composing bodies) may run in an isolated worker when the current agent runtime supports one. The confirmation prompt and issue creation run in the main conversation.

Never post any issue without explicit user confirmation.

## Input

`$ARGUMENTS` — a task description (a single concern or a brain dump). May start with an assignee hint:

```
/issue lkim: fix the tooltip overlap on hover
/issue alice: refactor the auth middleware
/issue fix the export button  ← no hint, defaults to current owner
```

Resolve the assignee prefix (case-insensitive, trailing `:` optional) against the `owners` map in `.agent-teamflow`. If no prefix matches, treat the whole input as the task description and default to the **current PC owner** (from `git config user.email`, strip domain, match against owner keys).

If `$ARGUMENTS` is a file path (starts with `/`, `~/`, or `./`, or ends in `.md`/`.txt`), Read it and treat its contents as the task description.

The chosen assignee applies to **every** issue created in this session. For mixed-assignee sessions, use `/dispatch`.

## Setup

Read `.agent-teamflow`. Extract `issueTracker`, `project`, and `owners`.

---

## Execution

### 1. Parse (main)

- Strip the assignee prefix if present.
- Resolve the assignee per the rules above.

### 2. Compose drafts

Use an isolated worker if available. Otherwise compose in the main session. Pass the task description and assignee, and follow these drafting rules:

**2a. Split into branch-sized chunks.** Rules (priority order):

- **Same file → same chunk.** Two pieces of work editing the same file MUST go into the same issue. Overlapping edits produce a merge conflict in batch-merge. Even complementary changes — keep them together.
- **Tightly-coupled cross-layer change → same chunk.** If a feature spans schema + server + UI but they're one logical change, keep it as one issue.
- **Different files + independent concerns → different chunks.**
- **Same area but different files → prefer different chunks.**

If the input describes one concern → 1 issue. If N independent concerns → N issues. No upper cap, but warn if N > 4.

**2b. For each chunk, compose:**

- Check if the project has per-area context docs (look for a AGENTS.md routing table or a `docs/` directory). If so, read the relevant ones before writing the issue body.
- **Title**: short, imperative. Under ~70 chars. No emojis.
- **Body** (markdown):
  ```markdown
  ## Context

  <which area/menu, why this matters — 1-3 lines>

  ## What to do

  <concrete steps referencing actual files/components>

  ## Acceptance criteria

  - [ ] <bullet 1>
  - [ ] <bullet 2>
  ```
  If the source already has richer structure, preserve it rather than collapsing into the minimal template.
- List **touched files** in Context or What to do so the user can verify the split.

**2c. Return as:**

```
RATIONALE: <one-line explanation of the split>

--- ISSUE 1 ---
TITLE: <title>
TOUCHED FILES: <comma-separated paths, or "n/a (cross-cutting)">
---
<body markdown>

--- ISSUE 2 ---
...
```

**Do NOT create any issue.** This step only drafts.

### 3. Preview to user (main)

Display all drafts with rationale and touched files. For N > 1, include `Issue k/N` banners. For N == 1, render as a single draft.

### 4. Ask for confirmation (main)

ask the user (single-select):
- `Create all` — create all N issues as drafted
- `Edit first` — user provides free-text edits; re-run drafting, then re-confirm (cap at 3 iterations)
- `Change assignee` — keep bodies, change assignee for all; go straight to step 6
- `Cancel` — do nothing

### 5. Act on selection (main)

- **`Create all`**: proceed to step 6.
- **`Edit first`**: ask for free-text changes, re-run drafting for draft v2, loop to step 3.
- **`Change assignee`**: ask for new assignee alias, normalize, go to step 6.
- **`Cancel`**: print `Cancelled` and exit.

### 6. Create issues (main)

For each drafted issue, create sequentially:

```bash
# GitLab
glab issue create --title "<title>" --description "<body>" --assignee <username>

# GitHub
gh issue create --title "<title>" --body "<body>" --assignee <username>
```

If a creation fails mid-batch: stop, report which one failed and the exact error, then ask (ask the user) whether to continue with remaining or abort.

### 7. Report

```
Filed #<id> (<assignee>): <title> — <url>
```

---

## Branch-sized — rule of thumb

A chunk is "branch-sized" if it satisfies all three:
1. **Atomic merge** — can be merged without depending on another chunk in this session.
2. **No file collision with sibling chunks** — every file it edits is touched by no other chunk.
3. **Coherent rationale** — one decision/intent, defensible to a reviewer in one paragraph.

## Hard rules

- **Always split when criteria say to split, always merge when criteria say to merge.**
- **Never post without explicit user confirmation.**
- **No code changes, no dev server, no commits.** This skill only touches the issue tracker.
- **No emojis.**
