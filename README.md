# agent-teamflow

A team workflow scaffold for AI coding agents. Drop it into your shared repo so your agents stop working like solo operators.

Most AI agent tooling is designed for one person. This is designed for teams — multiple developers, one shared repo, agents running in parallel without stepping on each other.

## The core idea

Each developer works in their own **lane**: a personal integration branch (`alice-staging`, `bob-staging`) that sits between their feature branches and the shared staging branch. Skills coordinate across lanes so agents can implement in parallel, merge cleanly, and hand off to humans at the right checkpoints.

```
feature branches → <owner>-staging → staging → main
                       ↑
               alice-staging, bob-staging, ...
```

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

Skills are written as agent-readable markdown runbooks in `.claude/commands/`. Claude Code picks them up as slash commands automatically. Other agent runtimes can read the same files directly.

## Quick start

See [SETUP.md](SETUP.md).

## Examples

[`examples/todo-api/`](examples/todo-api/) — a minimal Express app showing the scaffold in action.
