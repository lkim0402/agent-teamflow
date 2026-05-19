# agent-teamflow

## Before every skill

Read `.agent-teamflow` from the repo root before running any slash command. It provides:

- `issueTracker` — `"gitlab"` or `"github"`. Use `glab` for GitLab, `gh` for GitHub.
- `project` — the issue tracker project path (e.g. `myorg/myrepo`). Pass as `--repo` when needed.
- `branches.main` — production branch name (e.g. `master` or `main`).
- `branches.staging` — QA/integration target branch (e.g. `staging`).
- `owners` — map of git username shorthand → their personal integration branch (e.g. `{ "alice": "alice-staging" }`).

## Owner resolution (used by multiple skills)

1. Run `git config user.email`, strip the domain to get the local part (e.g. `alice@company.com` → `alice`).
2. Look up that value in `owners`. If found, check if `origin/<value>` exists via `git ls-remote --exit-code --heads origin <branch>`. If it exists, use it as `<INTEGRATION_BRANCH>`.
3. If not found or branch doesn't exist on origin, fall back to `branches.staging` and warn the user.

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

Your project may have per-area context documents. Check your `CLAUDE.md` for a routing table of which docs to read for which area. If none exists, skip this step.
