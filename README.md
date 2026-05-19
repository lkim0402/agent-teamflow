<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/lkim0402/agent-teamflow" alt="License"></a>
  <img src="https://img.shields.io/github/last-commit/lkim0402/agent-teamflow" alt="Last commit">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/claude_code-compatible-8A2BE2" alt="Claude Code">
  <img src="https://img.shields.io/badge/team_size-2%2B-orange" alt="Team size 2+">
</p>

# agent-teamflow

**Coordination layer for AI coding agents in a team repo.** Multiple developers, multiple agents, one shared codebase — without stepping on each other.

Most agent tooling assumes one person at a keyboard. agent-teamflow assumes **N** — Alice and Bob and Carol all using Claude Code at the same time, on the same repo, on the same day. The skills here are the protocol that keeps their work from colliding.

If you're a solo developer it still works (and there's a [solo example](examples/solo/)) — but if you're solo, you don't need it. The pitch is the team case.

> **Why this exists.** Tools like gstack supercharge one person's workflow. Claude Code's built-in skills are general-purpose primitives. agent-teamflow sits at a different layer: it's the *coordination protocol* for a team where each member is already using AI agents. It assumes 2+ developers, the same repo, work happening in parallel, and answers the question "how do we keep our agents from clobbering each other's work?" The answer is a tiny config file, personal integration branches, and a handful of skills that read both.

## Where this sits

agent-teamflow lives in the gap between solo-developer skill libraries and general-purpose primitives. The point is *team coordination*, not specialist roles or agent generation.

| Project | Niche | Audience |
|---|---|---|
| **agent-teamflow** (this repo) | Coordination protocol for multiple developers running agents on the same repo | Teams of 2+ |
| [gstack](https://github.com/garrytan/gstack) | One developer's "virtual eng team" via specialist roles (CEO, Designer, Eng Manager, QA...) | Solo founders, technical CEOs |
| [harness](https://github.com/revfactory/harness) | Generates agent team architectures from a domain description | Anyone building a new agent team |
| Claude Code built-in skills | General-purpose, domain-agnostic primitives | Everyone |

Different layers, not competitors — you can run agent-teamflow *alongside* gstack or harness in the same repo.

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

## See it work

Two developers, two terminals, four parallel agents — same repo, no collisions:

```
┌─ alice@laptop ────────────────────────┐  ┌─ bob@laptop ──────────────────────────┐
│ $ claude                              │  │ $ claude                              │
│ > /resolve                            │  │ > /resolve                            │
│                                       │  │                                       │
│ Picked issues #5, #6.                 │  │ Picked issues #8, #9.                 │
│ Spawning 2 forks in worktrees off     │  │ Spawning 2 forks in worktrees off     │
│ origin/alice-staging.                 │  │ origin/bob-staging.                   │
│                                       │  │                                       │
│ Batch 1: 2 ready                      │  │ Batch 1: 2 ready                      │
│   #5  → 5-checkout-validation         │  │   #8  → 8-pagination                  │
│   #6  → 6-payment-receipts            │  │   #9  → 9-health-check                │
│                                       │  │                                       │
│ PR #10: alice-staging → staging       │  │ PR #11: bob-staging   → staging       │
└───────────────────────────────────────┘  └───────────────────────────────────────┘
                              \                 /
                               v               v
                          ┌────────────────────────┐
                          │     origin/staging     │
                          └────────────────────────┘
```

Four feature branches, four parallel agents, two developers — zero coordination, zero pushes to branches anyone else is writing to.

## What you get

Eight slash commands. Two are lifecycle (`/teamflow-init`, `/teamflow-update`); the others are the actual team workflow.

| Command | What it does |
|---|---|
| `/teamflow-init` | Bootstrap the current repo — writes `.agent-teamflow`, optionally creates integration branches |
| `/teamflow-update` | Pull the latest agent-teamflow and re-register slash commands |
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

## Contributing

Adding a skill, fixing a runbook, or improving an example? See [CONTRIBUTING.md](CONTRIBUTING.md). Released under the [MIT License](LICENSE).
