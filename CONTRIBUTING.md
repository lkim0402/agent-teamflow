# Contributing

The fastest way to contribute is to add a new skill, fix a runbook, or improve an example. This guide covers the conventions.

## Repo layout

```
skills/                    ← runbooks (source of truth, agent-agnostic markdown)
AGENTS.md                  ← shared protocol for all coding agents
CLAUDE.md -> AGENTS.md     ← Claude Code compatibility symlink
.claude/commands/          ← Claude Code wrapper sources
.codex/prompts/            ← Codex prompt sources
.codex/skills/             ← Codex skill source
setup                      ← script that installs runtime adapters
examples/                  ← three narrative walkthroughs (no runnable code)
```

Skills are plain markdown runbooks. `AGENTS.md` contains the shared protocol, while `.claude/` and `.codex/` contain tool-specific entrypoints. The `setup` script writes Claude Code wrappers into `~/.claude/commands/`, Codex prompts into `${CODEX_HOME:-~/.codex}/prompts/`, and Codex skills into `${CODEX_HOME:-~/.codex}/skills/at-*/`.

If you're contributing, edit the source files in `skills/`, `AGENTS.md`, `.claude/`, and `.codex/`. User-scope copies are regenerated on every `./setup` run.

## Adding a new skill

At minimum, update the runbook, the matching wrapper under `.claude/commands/` and `.codex/prompts/`, and the matching thin skill under `.codex/skills/at-<name>/SKILL.md`.

**1. `skills/<name>.md`** — the runbook. Follow the shape used by existing skills:

```markdown
# <name>

<one-sentence summary of what the skill does>

Run in the main conversation when user interaction is required. If the work can run independently, use an isolated implementation worker or worktree when the current agent runtime supports it.

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

**2. `.claude/commands/<name>.md` and `.codex/prompts/<name>.md`** — runtime entrypoints. Use this shape:

```markdown
---
description: <one-sentence shown in Claude Code's slash-command picker>
---

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow `skills/<name>.md` exactly.

Arguments: $ARGUMENTS
```

That's it. Don't put logic in the wrapper — keep it pointing at the runbook so `setup`'s sed rewrite stays trivial.

**3. `.codex/skills/at-<name>/SKILL.md`** — add a thin Codex skill wrapper for direct `/skills` selection. Keep workflow logic in `skills/<name>.md`.

## Style

- **No emojis** anywhere — runbooks, wrappers, examples, commit messages, output.
- **No "we" / "I"** in runbooks; use imperatives ("Read", "Run", "Verify").
- **Reference config fields**, not literals — `<branches.staging>`, `<labels.doneInStaging>`, `<WORKFLOW_DIR>`. `AGENTS.md` lists the canonical placeholders.
- **Mention `owners` resolution** by referencing `git-auto-merge.md` Step 0 rather than re-explaining it.
- **Default-value documentation only** for optional fields — don't sprinkle string literals through the runbook.

## Local smoke test

Run `setup` against an isolated `HOME` to confirm generation works without touching your real agent installs:

```bash
HOME=/tmp/at-test ./setup --all
ls /tmp/at-test/.claude/commands/
cat /tmp/at-test/.claude/commands/<name>.md   # verify absolute paths
ls /tmp/at-test/.codex/prompts/<name>.md
test -f /tmp/at-test/.codex/skills/at-issue/SKILL.md
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
