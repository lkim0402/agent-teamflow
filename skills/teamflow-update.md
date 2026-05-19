# teamflow-update

Pull the latest agent-teamflow into the install directory and re-register the user-scope slash commands. Use this when a teammate ships a new skill or a runbook is updated upstream.

Run as a **forked agent** — call Agent without `subagent_type` so the git/setup output stays out of the main conversation. Report only the final summary.

---

## Setup

The install directory is the directory containing this runbook's parent — i.e. if this file lives at `/Users/foo/.claude/skills/agent-teamflow/skills/teamflow-update.md`, the install dir is `/Users/foo/.claude/skills/agent-teamflow`. Read the absolute path the wrapper passes to you and derive it.

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

Capture the output. The script prints `Installed <N> agent-teamflow slash commands into <path>` — that's the count of regenerated commands.

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

Slash commands regenerated: <N>
```

If no new commits: `Already up to date at <PRE_SUBJECT>.` (and skip everything else).

## Hard rules

- **Fast-forward only** — never rebase, never merge. If the install dir has diverged from origin, report and stop so the user can decide.
- **Never run `git reset --hard`** or any destructive git op to "fix" the install. If something is wrong, tell the user.
- **Never edit files in the install dir** — the only mutation is `git pull` and re-running `./setup`.
- **No emojis.**
