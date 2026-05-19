# dispatch

Split a brain dump into parallel issues for multiple team members, write a workflow file, and push.

Run this entire workflow as a **forked agent** — call the Agent tool without `subagent_type` so docs/CLI output stays out of the main conversation. Report only the final result (workflow file path, issue URLs, commit/push status).

---

## What this command does

You are distributing today's work across multiple team members. The user gives you a brain dump. You decide who does what, write a workflow file, file issues, and push.

## Setup

Read `.agent-teamflow` from the repo root. Extract `issueTracker`, `project`, `owners`, and `paths.workflowDir` (default `docs/workflow` if missing) — refer to it as `<WORKFLOW_DIR>` below.

The `owners` map keys are the assignee aliases (e.g. `"alice"`, `"bob"`). Values are their integration branch names — but for dispatch, you primarily need the keys as assignee identifiers.

## Inputs

`$ARGUMENTS` — the brain dump, either inline text or a file reference.
- If `$ARGUMENTS` starts with `/`, `~/`, or `./`, or ends in `.md`/`.txt`, Read it and use the file contents as the brain dump.

Tasks may include explicit assignment hints (e.g. `"alice: fix X"`, `"bob does Y"`). Honor them. Match case-insensitively against `owners` map keys. If no hints, distribute by area of expertise inferred from recent file activity, or alternate round-robin as fallback.

## Hard constraints

- **No cross-assignee blockers.** Tasks within one assignee may be sequential; tasks across assignees must be independent. If the brain dump implies a cross-assignee dependency, restructure so the dependent piece lives entirely with one assignee, or flag it in the workflow file under `## Dependencies (manual coordination)` and do NOT create the blocked issue yet.
- **No emojis** anywhere — workflow file, issue titles, bodies, commit messages.
- **Read before write.** If the project has per-area context docs (check CLAUDE.md or a `docs/` directory), read the relevant ones before writing issue bodies. Issue bodies must reference actual files, not vague "update the X page" phrasing.

## Execution

### 1. Parse the brain dump

- Extract individual tasks.
- Detect explicit assignee hints. Record them.
- For tasks without hints, decide based on recent file activity in per-owner areas, or round-robin.
- Verify the no-cross-assignee-blocker constraint. Restructure if violated.

### 2. Read relevant context docs

If the project has per-area context docs, read the ones relevant to each task before writing issue bodies.

### 3. Write the workflow file

Path: `<WORKFLOW_DIR>/workflow-<YYYYMMDD-HHMM>.md` (use local time: `date +%Y%m%d-%H%M`).

Create `<WORKFLOW_DIR>/` if it doesn't exist.

Structure:

```markdown
# Workflow <YYYY-MM-DD HH:MM>

## Brain dump (source)

<verbatim copy of $ARGUMENTS>

## Split

### <owner-alias-1>

1. **<issue title>** — <one-line summary>
   - Touches: <area(s)> / <file paths>
   - Acceptance: <what "done" means>
   - Issue: <leave blank; fill after creation>

2. ...

### <owner-alias-2>

1. ...

## Dependencies (manual coordination)

<empty if none, or list cross-assignee items that need human sequencing>

## Notes

<assumptions made when splitting>
```

### 4. Create issues

For each task, create sequentially:

```bash
# GitLab
glab issue create --title "<title>" --description "<body>" --assignee <username>

# GitHub
gh issue create --title "<title>" --body "<body>" --assignee <username>
```

Issue body must contain:
- **Context:** which area
- **What to do:** concrete description referencing actual files
- **Acceptance criteria:** bullet list
- **Source:** relative path to the workflow file

Capture the returned issue URL for each task.

### 5. Patch the workflow file with issue URLs

After all issues are created, edit the workflow file and fill in the `Issue:` lines with the returned URLs.

### 6. Commit and push

```bash
git add <WORKFLOW_DIR>/workflow-<timestamp>.md
git commit -m "chore(workflow): dispatch <YYYY-MM-DD> tasks"
git push origin HEAD
```

Do not touch integration branches, staging, or main.

### 7. Report

- Workflow file path
- Per-assignee bullet list of issues with URLs
- Commit SHA + branch pushed
- Any assumptions or flagged dependencies

## Error handling

- If an issue creation fails: keep going for the rest, note the failure in the final report. Do NOT roll back.
- If the workflow file already exists at the exact timestamp: append `-2`, `-3`, etc.
- If git push fails: report the error and the local commit SHA; do not retry blindly.
