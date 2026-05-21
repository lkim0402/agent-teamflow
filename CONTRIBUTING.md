# Contributing

The fastest way to contribute is to add a new skill, fix a runbook, or improve an example. This guide covers the conventions.

## Repo layout

```
AGENTS.md                  ← shared protocol for all coding agents
CLAUDE.md -> AGENTS.md     ← Claude Code compatibility symlink
.claude/commands/          ← Claude Code slash commands (full workflow content)
.codex/skills/             ← Codex skills (full workflow content)
setup                      ← script that installs runtime adapters
examples/                  ← three narrative walkthroughs (no runnable code)
```

Each workflow is self-contained inside its runtime entrypoint. `AGENTS.md` is the shared protocol. The `setup` script copies Claude Code commands into `~/.claude/commands/` and Codex skills into `${CODEX_HOME:-~/.codex}/skills/<name>/`, rewriting only the `AGENTS.md` reference to an absolute path.

If you're contributing, edit the source files in `.claude/commands/`, `.codex/skills/`, and `AGENTS.md`. **Every workflow has a Claude pair and a Codex pair — when you change one, update the other so both runtimes stay aligned.** User-scope copies are regenerated on every `./setup` run.

## Adding a new workflow

Each workflow needs two paired files with the same body but different frontmatter:

**1. `.claude/commands/<name>.md`** — the Claude Code slash command. Use this shape:

```markdown
---
description: <one-sentence shown in Claude Code's slash-command picker>
---

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below.

# <name>

<one-sentence summary of what the workflow does>

Run in the main conversation when user interaction is required. If the work can run independently, use an isolated implementation worker or worktree when the current agent runtime supports it.

---

## Setup

Read `.agent-teamflow` from the repo root. Extract the fields your workflow needs. If you resolve `<INTEGRATION_BRANCH>` from `owners`, follow the same pattern used in the `git-auto-merge` workflow's Step 0.

## Execution

### Step 1. <name>
<imperative steps with the exact CLI commands>

### Step N. Report
<what the workflow prints when done>

## Hard rules
- <constraints — e.g. never push to main, never delete branches without explicit approval>

Arguments: $ARGUMENTS
```

**2. `.codex/skills/<name>/SKILL.md`** — the Codex skill. Same body, different frontmatter and trailing line:

```markdown
---
name: <name>
description: Use when the user explicitly selects the <name> skill or wants to <do-the-thing>.
---

# <name>

Read `AGENTS.md`, then read `.agent-teamflow` from the repo root, then follow the workflow below. Treat the user's remaining request text as `$ARGUMENTS`.

---

<paste the same body used in the Claude command, without the `Arguments: $ARGUMENTS` line>
```

If the Codex skill needs supporting files, add `.codex/skills/<name>/agents/openai.yaml` (or other files) alongside `SKILL.md` — `setup` copies the whole directory.

## Style

- **No emojis** anywhere — runbooks, wrappers, examples, commit messages, output.
- **No "we" / "I"** in runbooks; use imperatives ("Read", "Run", "Verify").
- **Reference config fields**, not literals — `<branches.staging>`, `<labels.doneInStaging>`, `<WORKFLOW_DIR>`. `AGENTS.md` lists the canonical placeholders.
- **Mention `owners` resolution** by referencing `git-auto-merge.md` Step 0 rather than re-explaining it.
- **Default-value documentation only** for optional fields — don't sprinkle string literals through the runbook.

## Local smoke test

Run `setup` against an isolated `HOME` to confirm generation works without touching your real agent installs:

```bash
HOME=/tmp/at-test CODEX_HOME=/tmp/at-test-codex ./setup --all
ls /tmp/at-test/.claude/commands/
grep AGENTS.md /tmp/at-test/.claude/commands/<name>.md   # verify the absolute path
test -f /tmp/at-test-codex/skills/<name>/SKILL.md
rm -rf /tmp/at-test /tmp/at-test-codex
```

If your workflow reads new fields from `.agent-teamflow`, also try invoking it by hand in a scratch repo to make sure the field-resolution logic is clear.

## Updating CHANGELOG

Every user-visible change goes under the `## [Unreleased]` heading in `CHANGELOG.md`, grouped under `Added`, `Changed`, `Fixed`, or `Removed`. Don't bump the version in the same PR that adds the change — version bumps happen separately when a release is cut.

## Keeping `/teamflow-help` in sync

When you add a new workflow, update the static digest in **both** `.claude/commands/teamflow-help.md` and `.codex/skills/teamflow-help/SKILL.md` to include it. The digest is hand-maintained rather than auto-generated — keep it short and group your new command into the right section (Setup, Issue lifecycle, or Review).

## Commits and PRs

- Branch off `main`. Keep commits small and one-purpose.
- Commit subjects: `<type>: <short summary>` matching the existing log (`feat:`, `docs:`, `refactor:`, `fix:`).
- Open the PR against `main`. CI doesn't exist yet, so describe how you tested the change in the PR body.

## Out of scope for now

- New languages or runtime dependencies — this repo is intentionally bash + markdown only.
- Non-text deliverables (screencasts, images) — happy to link to externally hosted ones, but don't commit binaries.
- Reworking the integration-branch model itself — the `feature → owner-staging → staging → main` shape is the protocol the skills coordinate on. New skill ideas should fit that shape or have a clear case for changing it.
