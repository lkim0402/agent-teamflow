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

## llm-wiki 핸드오프 (세션 시작 시)

이 repo는 llm-wiki 허브에서 관리된다. 이 repo를 다루기 시작할 때(코딩이든 논의·계획이든):

1. **항상** `/home/user/workspace/llm-wiki/wiki/projects/agent-teamflow.md`를 읽는다.
   `## 현재 상태 / 다음`이 이 repo의 핸드오프(현재 state + 미래 plan)다.
2. **항상** `/home/user/workspace/llm-wiki/raw/devlog/agent-teamflow-*.md`를
   최신순 **최대 3개**(직전 세션들)를 읽어 결정 이유·디테일을 보강한다.

작업 후엔 Claude Code에서 `/devlog`, Codex에서 `$devlog`로 세션을 기록한다. 위키 "다음"이 갱신돼 다음 세션이 이어받는다.

## 도구 노트 (AI 에이전트 공용)

- 이 repo의 코딩과 llm-wiki 기록은 Claude Code와 Codex 모두 수행할 수 있다.
- **커밋 trailer는 지우지 말고 실제로 관여한 AI 도구를 정확히 남긴다.**
  - Claude Code → `Co-Authored-By: Claude <noreply@anthropic.com>`
  - Codex → `Co-authored-by: Codex <noreply@openai.com>`
  - 여러 AI 도구가 실제로 관여했으면 각 trailer를 한 번씩 남기고 기존 trailer는 보존한다.
- 커밋 메시지 본문에는 **무엇 + 왜**를 남긴다. 이유가 확인되지 않으면 기록 에이전트가 지어내지 않고 사용자에게 묻는다.
- author/committer는 항상 `jaegookyou`로 유지한다. trailer는 AI 관여 표식일 뿐이다.
- llm-wiki 반영은 Claude Code의 `/devlog` 또는 Codex의 `$devlog`를 사용한다. Codex를 코드 repo에서 열 때는 `codex --add-dir /home/user/workspace/llm-wiki`로 위키 쓰기 경로를 허용한다.
