---
name: teamflow-update
description: Use when the user explicitly selects the teamflow-update skill or wants to pull the latest agent-teamflow into the install directory and re-register runtime adapters.
---

# teamflow-update

Read `AGENTS.md`, then follow the workflow below. This workflow does not require `.agent-teamflow`; it updates the install itself. Treat the user's remaining request text as `$ARGUMENTS`.

---

Pull the latest agent-teamflow into the install directory and re-register the user-scope runtime adapters. Use this when a teammate ships a new skill or a runbook is updated upstream.

Run this workflow in an isolated worker if the current agent runtime supports one; otherwise run it in the main session. Keep git/setup output concise and report only the final summary.

## Setup

The install directory is the directory containing this runbook's parent — for the documented global install, that is usually `~/.agent-teamflow`. If a runtime wrapper passes an absolute runbook path, derive the install dir from that path.

If `.git` does not exist at that path: stop and tell the user the install looks corrupted — they should reclone with the README's quick-start command.

## Execution

### Step 1. Capture the pre-update state

```bash
cd <INSTALL_DIR>
PRE_HEAD=$(git rev-parse HEAD)
PRE_SUBJECT=$(git log -1 --format='%h %s')
```

### Step 2. Fetch and fast-forward

```bash
git fetch origin
POST_HEAD=$(git rev-parse origin/HEAD 2>/dev/null || git rev-parse origin/main)
```

If `PRE_HEAD` equals `POST_HEAD`: print `Already up to date at <PRE_SUBJECT>.` and stop. Skip Step 3.

Otherwise:

```bash
git pull --ff-only
```

If `git pull` fails because the working tree has local changes (the user customized the runbooks): stop and report — the user must resolve manually. Do NOT discard their changes.

### Step 3. Re-run setup

```bash
./setup
```

Capture the output. The script prints adapter install counts for Claude Code and/or Codex.

### Step 4. Summarize the diff

Show the user a terse list of new commits, not the full log:

```bash
git log --format='%h %s' "${PRE_HEAD}..HEAD"
```

### Step 5. Report

```
Updated agent-teamflow:
  From: <PRE_SUBJECT>
  To:   <POST_SUBJECT (one-line)>

New commits:
  <hash> <subject>
  <hash> <subject>

Adapters regenerated: <summary from setup output>
```

If no new commits: `Already up to date at <PRE_SUBJECT>.` (and skip everything else).

## Hard rules

- **Fast-forward only** — never rebase, never merge. If the install dir has diverged from origin, report and stop so the user can decide.
- **Never run `git reset --hard`** or any destructive git op to "fix" the install. If something is wrong, tell the user.
- **Never edit files in the install dir** — the only mutation is `git pull` and re-running `./setup`.
- **No emojis.**
