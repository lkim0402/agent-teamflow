# teamflow-init

Interactively bootstrap a repo for agent-teamflow. Detects sensible defaults from `git remote` and existing branches, asks the user for the rest, writes `.agent-teamflow`, and optionally creates personal integration branches on the remote.

Run **in the main conversation** (you need `AskUserQuestion` for the picker steps). Do not fork.

---

## Execution

### Step 0. Refuse to run outside a git repo

```bash
git rev-parse --show-toplevel
```

If it fails: tell the user this command must be run from inside a git repo, and stop.

### Step 1. Check for an existing config

If `.agent-teamflow` already exists at the repo root, Read it and use `AskUserQuestion` (single-select):
- `Overwrite — start fresh`
- `Show current — and exit` (Read and display, then stop)
- `Cancel — leave it alone` (stop)

Only proceed past this step on `Overwrite`.

### Step 2. Detect defaults

Run these in parallel and capture results — failures are fine, they just mean no default:

```bash
git config --get remote.origin.url
git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p'
git branch -r --format='%(refname:short)' | sed 's|^origin/||'
git config user.email
```

Derive:
- `defaultProject` — parse the origin URL. For `git@github.com:foo/bar.git` or `https://github.com/foo/bar.git`, extract `foo/bar`. For GitLab, same shape with possible subgroups.
- `defaultIssueTracker` — if the URL host contains `gitlab`, default `gitlab`; otherwise `github`.
- `defaultMain` — output of `HEAD branch` line, else `main`.
- `stagingCandidates` — remote branches matching `^(staging|develop|release|qa|integration)$`. Used as picker options for the staging field.
- `currentUserAlias` — local part of `git config user.email` (before `@`), lowercased.

### Step 3. Ask for the core fields

Use `AskUserQuestion` with up to 4 questions per call. Pre-fill defaults from Step 2 where possible.

**Q1 — Issue tracker** (single-select):
- `GitHub — gh CLI`
- `GitLab — glab CLI`

Recommend the one matching `defaultIssueTracker`.

**Q2 — Project path:**
Skip if `defaultProject` was detected — show it back and ask if it's right. If wrong or undetected, ask the user to type the `owner/repo` value.

Use AskUserQuestion single-select:
- `Use detected: <defaultProject>` (only if detected)
- `Enter manually`

If `Enter manually`, follow up by asking the user to reply with the path in chat.

**Q3 — Main branch:**
Similar pattern — show `defaultMain` and confirm, or ask for a manual value.

**Q4 — Staging branch:**
If `stagingCandidates` is non-empty, single-select among them plus an `Other` option. Otherwise default to typing in chat.

### Step 4. Ask about personal integration branches

Single-select:
- `Yes — set up personal lanes` (recommended for multi-dev teams; each developer gets `<alias>-staging` style branch between feature branches and the shared staging branch)
- `No — everyone merges to <staging-branch>` (simpler; works for solo developers or teams that prefer a shared branch)

If `No`, skip to Step 6.

### Step 5. Collect owners

Ask the user (in chat, free-form) for a comma-separated list of team-member aliases. Suggest including `currentUserAlias` if detected.

For each alias, generate a default branch name `<alias>-staging` and present the full list as a confirmation:

```
Owners to register:
  alice → alice-staging
  bob   → bob-staging
  carol → carol-staging
```

`AskUserQuestion` single-select:
- `Looks good — use these`
- `Let me change a branch name`

If `Let me change`, ask which alias and the new branch name. Loop until confirmed.

### Step 6. Write `.agent-teamflow`

Compose the JSON. Include `owners` only if Step 4 said yes. Pretty-print (2-space indent). Write to the repo root via `Write`. Do not commit — the user decides when to stage it.

Example written content:

```json
{
  "issueTracker": "github",
  "project": "your-org/your-repo",
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

### Step 7. Offer to create missing integration branches

Skip if Step 4 said no, or if `owners` is empty.

For each owner branch, check if it exists on origin:

```bash
git ls-remote --exit-code --heads origin <branch>
```

Build a list of branches that don't exist yet. If the list is empty, skip this step entirely.

If non-empty, **show the user the exact branches that would be created and ask for explicit approval** via `AskUserQuestion`:

- `Yes — create all listed branches on origin`
- `No — I will create them myself` (recommended if anyone else might already be pushing — never overwrite)

Only on explicit `Yes`, create each missing branch off `origin/<staging-branch>`:

```bash
git fetch origin <staging-branch>
git push origin "origin/<staging-branch>:refs/heads/<owner-branch>"
```

Report each branch as it's created. If any push fails, stop and surface the error — do not retry.

### Step 8. Verify prerequisites

Run and report status. Do not block — these are informational so the user can fix anything missing before running other commands.

```bash
# Issue tracker auth
gh auth status        # if issueTracker = github
glab auth status      # if issueTracker = gitlab

# Git identity
git config user.email
```

Flag specifically:
- Auth failure → tell the user which CLI to log into.
- `git config user.email` empty → tell them to set it.
- Email local part not in `owners` map (when `owners` is set) → warn and suggest adding themselves.

### Step 9. Final report

Print:

```
Wrote .agent-teamflow:
  issueTracker: <github|gitlab>
  project:      <project>
  main:         <main-branch>
  staging:      <staging-branch>
  owners:       <list, or "none — features merge to staging directly">

Integration branches:
  <list of created/existing branches, or "n/a">

Next steps:
  1. Review .agent-teamflow and commit it when ready.
  2. Try one of:
       /issue <a single task>       — file one issue
       /dispatch <brain dump>       — split work across owners
       /resolve                     — pick up your open issues
```

---

## Hard rules

- **No remote branch creation without explicit `Yes` in Step 7.** Branches on origin are shared infra — never assume permission.
- **Never overwrite `.agent-teamflow` without the `Overwrite` selection in Step 1.**
- **Do not commit or push the config file** — the user decides when to stage it.
- **No emojis.**
