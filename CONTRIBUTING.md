# Contributing

The fastest way to contribute is to add a new skill, fix a runbook, or improve an example. This guide covers the conventions.

## Repo layout

```
skills/                    ← runbooks (source of truth, agent-agnostic markdown)
.claude/commands/          ← project-scope wrappers (one per skill, thin)
setup                      ← script that generates user-scope wrappers
examples/                  ← three narrative walkthroughs (no runnable code)
```

Skills are plain markdown runbooks. Wrappers are 5-line files that point Claude Code at a runbook. The `setup` script reads the project-scope wrappers and writes user-scope copies into `~/.claude/commands/`, rewriting relative paths to absolute install paths so the commands work from any repo.

If you're contributing, you only ever edit the project-scope sources. The user-scope copies are regenerated on every `./setup` run.

## Adding a new skill

Two files, always paired:

**1. `skills/<name>.md`** — the runbook. Follow the shape used by existing skills:

```markdown
# <name>

<one-sentence summary of what the skill does>

Run as a **forked agent** — call Agent without `subagent_type` so CLI output stays out of the main conversation. (Or: orchestrate in the main thread if the skill uses AskUserQuestion. Be explicit either way at the top.)

---

## Setup

Read `.agent-teamflow` from the repo root. Extract the fields your skill needs. If you resolve `<INTEGRATION_BRANCH>` from `owners`, follow the same pattern used in `git-auto-merge.md` Step 0.

## Execution

### Step 1. <name>
<imperative steps with the exact CLI commands>

### Step N. Report
<what the skill prints when done>

## Hard rules
- <constraints — e.g. never push to main, never delete branches without explicit approval>
```

**2. `.claude/commands/<name>.md`** — the wrapper. Always this shape:

```markdown
---
description: <one-sentence shown in Claude Code's slash-command picker>
---

Read `CLAUDE.md`, then read `.agent-teamflow` from the repo root, then follow `skills/<name>.md` exactly.

Arguments: $ARGUMENTS
```

That's it. Don't put logic in the wrapper — keep it pointing at the runbook so `setup`'s sed rewrite stays trivial.

## Style

- **No emojis** anywhere — runbooks, wrappers, examples, commit messages, output.
- **No "we" / "I"** in runbooks; use imperatives ("Read", "Run", "Verify").
- **Reference config fields**, not literals — `<branches.staging>`, `<labels.doneInStaging>`, `<WORKFLOW_DIR>`. The CLAUDE.md table at the top of the repo lists the canonical placeholders.
- **Mention `owners` resolution** by referencing `git-auto-merge.md` Step 0 rather than re-explaining it.
- **Default-value documentation only** for optional fields — don't sprinkle string literals through the runbook.

## Local smoke test

Run `setup` against an isolated `HOME` to confirm generation works without touching your real Claude Code install:

```bash
HOME=/tmp/at-test ./setup
ls /tmp/at-test/.claude/commands/
cat /tmp/at-test/.claude/commands/<name>.md   # verify absolute paths
rm -rf /tmp/at-test
```

If your skill reads new fields from `.agent-teamflow`, also try invoking the runbook by hand in a scratch repo to make sure the field-resolution logic is clear.

## Updating CHANGELOG

Every user-visible change goes under the `## [Unreleased]` heading in `CHANGELOG.md`, grouped under `Added`, `Changed`, `Fixed`, or `Removed`. Don't bump the version in the same PR that adds the change — version bumps happen separately when a release is cut.

## Keeping `/teamflow-help` in sync

When you add a new slash command, update the static digest in `skills/teamflow-help.md` to include it. The digest is hand-maintained rather than auto-generated — keep it short and group your new command into the right section (Setup, Issue lifecycle, or Review).

## Commits and PRs

- Branch off `main`. Keep commits small and one-purpose.
- Commit subjects: `<type>: <short summary>` matching the existing log (`feat:`, `docs:`, `refactor:`, `fix:`).
- Open the PR against `main`. CI doesn't exist yet, so describe how you tested the change in the PR body.

## Out of scope for now

- New languages or runtime dependencies — this repo is intentionally bash + markdown only.
- Non-text deliverables (screencasts, images) — happy to link to externally hosted ones, but don't commit binaries.
- Reworking the integration-branch model itself — the `feature → owner-staging → staging → main` shape is the protocol the skills coordinate on. New skill ideas should fit that shape or have a clear case for changing it.
