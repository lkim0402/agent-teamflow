# agent-teamflow

A team workflow scaffold for AI coding agents. Drop it into your shared repo so your agents stop working like solo operators.

Most AI agent tooling is designed for one person. This is designed for teams — multiple developers, one shared repo, agents running in parallel without stepping on each other.

## The core idea

Skills read a single config file (`.agent-teamflow`) at the repo root and adapt to your branching model. You describe your branches and who owns what — the skills do the rest.

The minimum setup is just two branches:

```
feature branches → staging → main
```

If your team uses personal integration branches, add them to `owners` and the skills route accordingly:

```
feature branches → alice-staging ─┐
                                   ├→ staging → main
feature branches → bob-staging   ─┘
```

If your team calls things differently — `develop` instead of `staging`, `master` instead of `main`, `alice/integration` instead of `alice-staging` — you just configure those names. The skills don't care what the branches are called.

## What's included

| Skill | What it does |
|---|---|
| `/resolve` | Pick open issues, implement each in a parallel worktree, batch-merge when done |
| `/git-auto-merge` | Commit → push → merge into your lane → open MR/PR to staging |
| `/post-merge` | After merging a MR/PR, label linked issues as `done-in-staging` |
| `/issue` | Turn a brain dump into branch-sized issues (sized to avoid merge conflicts) |
| `/dispatch` | Split a brain dump across multiple team members, file issues, write a workflow log |
| `/prod-check` | Pre-production review of your recent commits — impact, contracts, auth, stability |

## Compatibility

The actual skill logic lives in `skills/` — plain markdown runbooks any agent can read. The `.claude/commands/` files are thin one-liners that point Claude Code at those runbooks. Other agents (Codex, etc.) can read `skills/` directly, or get their own adapter folder that does the same thing.

## Quick start

See [SETUP.md](SETUP.md).

## Examples

[`examples/todo-api/`](examples/todo-api/) — a minimal Express app showing the scaffold in action.
