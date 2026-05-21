# agent-teamflow

## Before every workflow

Read `.agent-teamflow` from the repo root before running any workflow that touches issues, branches, merges, or releases. It provides:

- `issueTracker` — `"gitlab"` or `"github"`. Use `glab` for GitLab, `gh` for GitHub.
- `project` — the issue tracker project path (for example `myorg/myrepo`). Pass as `--repo` when needed.
- `branches.main` — production branch name (for example `master` or `main`).
- `branches.staging` — QA/integration target branch (for example `staging`).
- `owners` — map of git username shorthand to personal integration branch (for example `{ "alice": "alice-staging" }`).

## Owner resolution

1. Run `git config user.email`, strip the domain to get the local part (for example `alice@company.com` -> `alice`).
2. Look up that value in `owners`. If found, check if `origin/<value>` exists via `git ls-remote --exit-code --heads origin <branch>`. If it exists, use it as `<INTEGRATION_BRANCH>`.
3. If not found or the branch does not exist on origin, fall back to `branches.staging` and warn the user.

## Issue tracker commands

| Action | GitLab | GitHub |
|---|---|---|
| List assigned issues | `glab issue list --assignee @me` | `gh issue list --assignee @me` |
| View issue | `glab issue view <id>` | `gh issue view <id>` |
| Create issue | `glab issue create` | `gh issue create` |
| List MRs/PRs | `glab mr list` | `gh pr list` |
| Create MR/PR | `glab mr create` | `gh pr create` |
| Update MR/PR | `glab mr update` | `gh pr edit` |

## Context docs

The project may have per-area context documents. Check `AGENTS.md`, `CLAUDE.md`, and `docs/` for routing notes before touching code. If none exists, continue without extra context.

## Runtime adapters

Each workflow is fully self-contained inside its runtime entrypoint:

- Claude Code reads `.claude/commands/*.md`.
- Codex reads `.codex/skills/*/SKILL.md` after `setup --codex`.

When you change a workflow's behavior (branch, issue, or merge logic), update both runtime entrypoints so Claude Code and Codex stay aligned.
