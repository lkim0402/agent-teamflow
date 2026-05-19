# agent-teamflow

**Coordination layer for AI coding agents in a team repo.** Multiple developers, multiple agents, one shared codebase — without stepping on each other.

Most agent tooling assumes one person at a keyboard. agent-teamflow assumes **N** — Alice and Bob and Carol all using Claude Code at the same time, on the same repo, on the same day. The skills here are the protocol that keeps their work from colliding.

If you're a solo developer it still works (and there's a [solo example](examples/solo/)) — but if you're solo, you don't need it. The pitch is the team case.

## Quick start

**1. Install once on your machine** (clones to `~/.claude/skills/agent-teamflow/` and registers the slash commands user-scope, so they work in every repo):

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.claude/skills/agent-teamflow && ~/.claude/skills/agent-teamflow/setup
```

**2. In any team repo, run `/teamflow-init`** in Claude Code. It detects your remote, asks four short questions, writes `.agent-teamflow`, and (with your approval) creates personal integration branches on origin.

**3. Try one of the workflow commands:**

```
/issue       file a single branch-sized issue from a one-line brain dump
/dispatch    split a bigger brain dump across multiple teammates
/resolve     pick up issues assigned to you and implement them in parallel forks
```

That's it. Each teammate runs the install once. After that, agents from any of them stay out of each other's way.

## What you get

Seven slash commands. The first is one-shot setup; the others are the actual team workflow.

| Command | What it does |
|---|---|
| `/teamflow-init` | Bootstrap the current repo — writes `.agent-teamflow`, optionally creates integration branches |
| `/issue` | Turn a brain dump into branch-sized issues (sized to avoid merge conflicts) |
| `/dispatch` | Split a brain dump across multiple teammates, file issues, write a workflow log |
| `/resolve` | Pick open issues assigned to you, implement each in a parallel worktree, batch-merge when done |
| `/git-auto-merge` | Commit → push → merge into your lane → open MR/PR to staging |
| `/post-merge` | After merging an MR/PR, label linked issues as "done in staging" |
| `/prod-check` | Pre-production review of your recent commits — impact, contracts, auth, stability |

## How the team workflow works

Skills read one config file (`.agent-teamflow`) at the repo root and adapt to your branching model. You describe your branches and who owns what — the skills do the rest.

The minimum two-branch setup:

```
feature branches → staging → main
```

Personal integration branches (recommended for teams of 2+):

```
Alice's feature branches → alice-staging ─┐
                                           ├→ staging → main
Bob's feature branches   → bob-staging   ─┘
```

Personal lanes are the multiplayer primitive. Alice and Bob can both have multiple agents running, all pushing to their own lane, without ever pushing to a branch the other is also writing to. When work is ready, each lane merges into the shared `staging` via a normal PR.

If your team calls things differently — `develop` instead of `staging`, `master` instead of `main`, `alice/integration` instead of `alice-staging` — configure those names. The skills don't care what the branches are called.

## Examples

[`examples/`](examples/) — three narrative walkthroughs showing the same skills under different team setups:

- [`solo/`](examples/solo/) — one developer, no personal lanes, features land on `staging` directly.
- [`small-team/`](examples/small-team/) — two developers with personal integration branches, parallel `/resolve` runs.
- [`larger-team/`](examples/larger-team/) — four developers sharing one `staging` branch, no personal lanes.

## Compatibility

The actual skill logic lives in `skills/` — plain markdown runbooks any agent can read. `.claude/commands/` and the user-scope commands installed by `setup` are thin wrappers that point Claude Code at those runbooks. Other agents (Codex, etc.) can read `skills/` directly, or get their own adapter folder.

## Manual setup

If you don't want to use the global installer (vendoring into the repo, customizing the install path, etc.), see [SETUP.md](SETUP.md).
