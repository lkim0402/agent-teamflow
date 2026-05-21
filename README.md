<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/lkim0402/agent-teamflow" alt="License"></a>
  <img src="https://img.shields.io/github/last-commit/lkim0402/agent-teamflow" alt="Last commit">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/claude_code-compatible-8A2BE2" alt="Claude Code">
  <img src="https://img.shields.io/badge/codex-compatible-111111" alt="Codex">
  <img src="https://img.shields.io/badge/team_size-2%2B-orange" alt="Team size 2+">
</p>

<p align="center">
  <img src="docs/images/hero.png" alt="agent-teamflow mascots — a team of coding-agent robots" width="240">
</p>

# agent-teamflow

**Agent workflow runbooks and adapters that let a team's coding agents work in parallel on the same repo without colliding.**

When Alice and Bob both run `/resolve` at the same time on different issues, they need to file separate issues, push to separate branches, and merge cleanly into shared staging — without coordinating manually. agent-teamflow is the convention that makes that work.

It's three pieces:

- **A config file** (`.agent-teamflow`) at the repo root, describing your issue tracker, branches, and per-developer integration lanes.
- **A branching convention** — `feature → personal lane (optional) → shared staging → main`.
- **Nine workflows** — `/issue`, `/dispatch`, `/resolve`, `/git-auto-merge`, `/post-merge`, `/prod-check` for the team flow, plus setup helpers `/teamflow-init`, `/teamflow-update`, `/teamflow-help`.

Most agent tooling supercharges one developer. agent-teamflow is the team layer — built for 2+ developers running agents in parallel against the same codebase.

If you're solo it still works (see [`examples/solo/`](examples/solo/)), but you probably don't need it.

## See it work

Two developers, two terminals, four parallel agents — same repo, no collisions:

```
┌─ alice@laptop ────────────────────────┐  ┌─ bob@laptop ──────────────────────────┐
│ $ claude                              │  │ $ claude                              │
│ > /resolve                            │  │ > /resolve                            │
│                                       │  │                                       │
│ Picked issues #5, #6.                 │  │ Picked issues #8, #9.                 │
│ Starting 2 workers in worktrees off   │  │ Starting 2 workers in worktrees off   │
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

## Quick start

agent-teamflow installs two ways. **For a team that commits to the workflow, vendor it into your repo** — everyone gets the same version automatically. For solo evaluation or personal use across many repos, install globally instead.

### Vendor into your repo (recommended for teams)

From inside your team's repo root. Pick your runtime and follow that path end to end.

---

#### Claude Code only

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git .agent-teamflow-tmp \
  && cp -r .agent-teamflow-tmp/.claude .agent-teamflow-tmp/AGENTS.md . \
  && ln -sf AGENTS.md CLAUDE.md \
  && rm -rf .agent-teamflow-tmp
```

Review what was copied, then commit:

```bash
git add .claude AGENTS.md CLAUDE.md && git commit -m "add agent-teamflow"
```

---

#### Codex only

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git .agent-teamflow-tmp \
  && cp -r .agent-teamflow-tmp/.codex .agent-teamflow-tmp/AGENTS.md . \
  && rm -rf .agent-teamflow-tmp
```

Review what was copied, then commit:

```bash
git add .codex AGENTS.md && git commit -m "add agent-teamflow"
```

---

#### Both Claude Code and Codex

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git .agent-teamflow-tmp \
  && cp -r .agent-teamflow-tmp/.claude .agent-teamflow-tmp/.codex .agent-teamflow-tmp/AGENTS.md . \
  && ln -sf AGENTS.md CLAUDE.md \
  && rm -rf .agent-teamflow-tmp
```

Review what was copied, then commit:

```bash
git add .claude .codex AGENTS.md CLAUDE.md && git commit -m "add agent-teamflow"
```

---

> **Already have a `.claude/` directory** with your own custom commands? `cp -r` will merge — inspect the result before committing.
>
> **Want to merge `AGENTS.md`** with an existing one? After the copy, manually combine the two and delete the conflict.

Then in your agent, run `/teamflow-init` to write `.agent-teamflow` (your team's config). Commit that too.

### Install globally (alternative — personal use only)

One install on your machine; commands work in every repo. Use this for solo evaluation or personal workflows, not for a team repo that already vendors agent-teamflow.

Pick the variant that matches your runtime:

```bash
# Both Claude Code and Codex
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.agent-teamflow \
  && ~/.agent-teamflow/setup --all

# Claude Code only
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.agent-teamflow \
  && ~/.agent-teamflow/setup --claude

# Codex only
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.agent-teamflow \
  && ~/.agent-teamflow/setup --codex
```

Each developer installs separately and updates independently. Behavior is still configured per-repo via `.agent-teamflow`.

Don't combine global and vendor installs for the same workflow — if names overlap, Codex will show duplicate skills.

## What you get

Nine workflows. Three are lifecycle (`/teamflow-init`, `/teamflow-update`, `/teamflow-help`); the others are the actual team workflow. Claude Code exposes them as slash commands; Codex exposes matching skills in `/skills`. Codex custom prompt slash commands are not reliable in current Codex CLI releases, so use the skills there.

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

Everything reads from `.agent-teamflow` at the repo root. Two supported branching models:

```
feature branches → staging → main
```

```
Alice's features → alice-staging ─┐
                                   ├→ staging → main
Bob's features   → bob-staging   ─┘
```

Personal lanes are the multiplayer primitive — Alice and Bob each push to their own lane, so agents never collide on a shared branch. Name the branches whatever fits your team; the skills adapt.

## Examples

[`examples/`](examples/) — three narrative walkthroughs showing the same skills under different team setups:

- [`solo/`](examples/solo/) — one developer, no personal lanes, features land on `staging` directly.
- [`small-team/`](examples/small-team/) — two developers with personal integration branches, parallel `/resolve` runs.
- [`larger-team/`](examples/larger-team/) — four developers sharing one `staging` branch, no personal lanes.

## Setup, troubleshooting, FAQ

For the full config reference, both install paths in depth, common failure modes, and FAQ, see [SETUP.md](SETUP.md).

## Contributing

Adding a skill, fixing a runbook, or improving an example? See [CONTRIBUTING.md](CONTRIBUTING.md). Released under the [MIT License](LICENSE).
