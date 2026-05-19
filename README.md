<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/lkim0402/agent-teamflow" alt="License"></a>
  <img src="https://img.shields.io/github/last-commit/lkim0402/agent-teamflow" alt="Last commit">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/claude_code-compatible-8A2BE2" alt="Claude Code">
  <img src="https://img.shields.io/badge/team_size-2%2B-orange" alt="Team size 2+">
</p>

# agent-teamflow

**Claude Code slash commands that let a team's AI agents work in parallel on the same repo without colliding.**

When Alice and Bob both run `/resolve` at the same time on different issues, they need to file separate issues, push to separate branches, and merge cleanly into shared staging — without coordinating manually. agent-teamflow is the convention that makes that work.

It's three pieces:

- **A config file** (`.agent-teamflow`) at the repo root, describing your issue tracker, branches, and per-developer integration lanes.
- **A branching convention** — `feature → personal lane (optional) → shared staging → main`.
- **Nine slash commands** — `/issue`, `/dispatch`, `/resolve`, `/git-auto-merge`, `/post-merge`, `/prod-check` for the workflow, plus setup helpers `/teamflow-init`, `/teamflow-update`, `/teamflow-help`.

Most agent tooling supercharges one developer. agent-teamflow is the team layer — built for 2+ developers running agents in parallel against the same codebase.

If you're solo it still works (see [`examples/solo/`](examples/solo/)), but you probably don't need it.

## Quick start

agent-teamflow installs two ways. **For a team that commits to the workflow, vendor it into your repo** — everyone gets the same version automatically. For solo evaluation or personal use across many repos, install globally instead.

### Vendor into your repo (recommended for teams)

From inside your team's repo root:

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git .agent-teamflow-tmp \
  && cp -r .agent-teamflow-tmp/.claude .agent-teamflow-tmp/skills .agent-teamflow-tmp/CLAUDE.md . \
  && rm -rf .agent-teamflow-tmp
```

This adds `.claude/commands/`, `skills/`, and `CLAUDE.md` to your repo. Review what was copied, then commit:

```bash
git add .claude skills CLAUDE.md && git commit -m "add agent-teamflow"
```

Now anyone who clones this repo gets the slash commands automatically through Claude Code's project-scope discovery. New hires onboard on day 1. Version drift disappears.

> **Already have a `.claude/` directory** with your own custom commands? `cp -r` will merge — inspect the result before committing.
>
> **Want to merge `CLAUDE.md`** with an existing one? After the copy, manually combine the two and delete the conflict.

In Claude Code, run `/teamflow-init` to write `.agent-teamflow` (your team's config). Then commit that too.

### Install globally (alternative — for trying it out)

One install on your machine; slash commands work in every repo:

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.claude/skills/agent-teamflow && ~/.claude/skills/agent-teamflow/setup
```

Each developer installs separately and updates independently (via `/teamflow-update`). Behavior is still configured per-repo via `.agent-teamflow`.

### Then run a workflow command

Either install path, the workflow is the same:

```
/issue       file a single branch-sized issue from a one-line brain dump
/dispatch    split a bigger brain dump across multiple teammates
/resolve     pick up issues assigned to you and implement them in parallel forks
```

### Vendor vs. global — which?

|  | Vendor (project-scope) | Global (user-scope) |
|---|---|---|
| Versions | Everyone on the team uses the same one (whatever's committed) | Each developer installs and updates independently |
| Onboarding | New hires get it on day 1 | New hires have to install themselves |
| Discoverability | `.claude/commands/` is visible in the repo | Nothing in the repo says "we use this" |
| Repo footprint | Adds ~12 files + 1 config | Just `.agent-teamflow` |
| Updates | Re-vendor when you want to pull upstream changes | `/teamflow-update` per developer |

Both modes use the same skills and the same config schema. Start with whichever fits, switch later if needed.

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

Nine slash commands. Three are lifecycle (`/teamflow-init`, `/teamflow-update`, `/teamflow-help`); the others are the actual team workflow.

| Command | What it does |
|---|---|
| `/teamflow-init` | Bootstrap the current repo — writes `.agent-teamflow`, optionally creates integration branches |
| `/teamflow-update` | Pull the latest agent-teamflow and re-register slash commands |
| `/teamflow-help` | Print this list of commands (useful for teammates who just installed) |
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

## Setup, troubleshooting, FAQ

For the full config reference, both install paths in depth, common failure modes, and FAQ, see [SETUP.md](SETUP.md).

## Contributing

Adding a skill, fixing a runbook, or improving an example? See [CONTRIBUTING.md](CONTRIBUTING.md). Released under the [MIT License](LICENSE).
