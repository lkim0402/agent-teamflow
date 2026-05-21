---
name: git-auto-merge
description: Use when the user explicitly selects the git-auto-merge skill or wants to commit, push a feature branch, merge into their integration branch, then open or update an MR/PR to staging.
---

# git-auto-merge

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below. Treat the user's remaining request text as `$ARGUMENTS`.

---

Commit, push the feature branch, merge into the owner's integration branch (auto-detected from `.agent-teamflow`), then open or update an MR/PR from that integration branch to staging.

Run this workflow in an isolated worker if the current agent runtime supports one; otherwise run it in the main session. Keep intermediate git output concise and report only the final result (branch push status, MR/PR URL, and which integration branch was used) to the user.

## Setup

Read `.agent-teamflow` from the repo root first. Extract:
- `issueTracker` — `"gitlab"` or `"github"`
- `project` — repo path for `--repo` flags
- `branches.main` — production branch (never touch)
- `branches.staging` — QA target branch
- `owners` — map of shorthand → integration branch name

## Step 0: Resolve `<INTEGRATION_BRANCH>`

```bash
EMAIL=$(git config user.email)
OWNER=${EMAIL%@*}  # strip domain
```

Look up `OWNER` in the `owners` map (case-insensitive match against keys). If found:
```bash
CANDIDATE="<owners[OWNER]>"  # e.g. "alice-staging"
if git ls-remote --exit-code --heads origin "$CANDIDATE" >/dev/null 2>&1; then
    INTEGRATION_BRANCH="$CANDIDATE"
else
    INTEGRATION_BRANCH="<branches.staging>"  # fallback
fi
```

If `OWNER` not found in the map, fall back to `branches.staging` and warn.

Report which `INTEGRATION_BRANCH` was resolved.

## Step 1. Save local work

Stage all current modifications, commit with a descriptive message based on the changes, and push the current feature branch to `origin`.

## Step 2. Merge into `<INTEGRATION_BRANCH>`

```bash
git fetch origin <INTEGRATION_BRANCH>
git worktree add /tmp/<INTEGRATION_BRANCH>-wt origin/<INTEGRATION_BRANCH> -b <INTEGRATION_BRANCH>-tmp
cd /tmp/<INTEGRATION_BRANCH>-wt
git merge origin/<feature-branch> --no-edit
git push origin HEAD:<INTEGRATION_BRANCH>
cd -
git worktree remove /tmp/<INTEGRATION_BRANCH>-wt
git branch -D <INTEGRATION_BRANCH>-tmp
```

## Step 3. Merge into staging

```bash
git worktree add /tmp/staging-wt origin/<branches.staging> -b staging-tmp
cd /tmp/staging-wt
git merge origin/<INTEGRATION_BRANCH> --no-edit
git push origin HEAD:<branches.staging>
cd -
git worktree remove /tmp/staging-wt
git branch -D staging-tmp
```

## Step 4. Detect linked issues

Collect issue ids this MR/PR resolves from two sources:
- **Feature branch name** — if it starts with `<digits>-` (the `/resolve` convention), the leading digits are an id.
- **Commit messages** — scan `git log origin/<branches.staging>..HEAD --format=%B` for `#<digits>` references.

Union, dedupe, sort ascending. Verify each id exists before using it:
```bash
# GitLab
glab issue view <id> --repo <project>

# GitHub
gh issue view <id> --repo <project>
```

Drop any that 404. Never fabricate an id.

## Step 5. Create or update MR/PR

Check for an existing open MR/PR from `<INTEGRATION_BRANCH>` → `<branches.staging>`.

```bash
# GitLab
glab mr list --source-branch <INTEGRATION_BRANCH> --target-branch <branches.staging>

# GitHub
gh pr list --head <INTEGRATION_BRANCH> --base <branches.staging>
```

If none exists, create one. If one exists, update the description.

Title and description must summarize new commits in `<INTEGRATION_BRANCH>` not yet in `<branches.staging>`:
```bash
git log origin/<branches.staging>..origin/<INTEGRATION_BRANCH> --oneline
```

Append linked issues under a `## Linked issues` heading:
```
## Linked issues

Closes #42
Closes #43
```

Note: auto-close fires when the MR/PR merges into the project's default branch (`branches.main`), not into staging. The `Closes #N` reference is still valuable for cross-linking.

## Constraints

- No emojis in output, commit messages, or MR/PR descriptions.
- Stop and ask the user only if a merge conflict occurs.
- Never fabricate issue ids.
- **Never push to `<branches.main>` directly.**

---

## After completion: cleanup notice

Append the following to your final report **as plain instructions for the user to run themselves**. Do NOT execute these.

```
Cleanup is up to you. If this was an ephemeral worktree branch and you want to discard it:

  git push origin --delete <feature-branch>   # remove branch from origin
  /exit                                        # then choose "remove" at the
                                               # agent worktree prompt
```

---

## ABSOLUTE PROHIBITION on automated deletion

- **NEVER** run `git push origin --delete ...` automatically.
- **NEVER** run `git branch -D ...` or `git branch -d ...` automatically.
- **NEVER** run `git worktree remove ...` on any worktree other than the `/tmp/*` ones this skill itself created in steps 2 and 3.
- **NEVER** delete, rename, force-push, or rewrite history on any long-lived branch.
- **NEVER** infer deletion intent from prior conversation, memory, or shorthand like "clean up", "remove it".

**Exception (with explicit per-turn approval):**

Deletion is permitted only if the user explicitly requests it in the current turn AND you ask via ask the user with each item listed by its exact path or branch name, AND the user clicks Approve. Approval does NOT persist across turns.
