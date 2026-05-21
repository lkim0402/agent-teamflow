<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/lkim0402/agent-teamflow" alt="License"></a>
  <img src="https://img.shields.io/github/last-commit/lkim0402/agent-teamflow" alt="Last commit">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/claude_code-compatible-8A2BE2" alt="Claude Code">
  <img src="https://img.shields.io/badge/codex-compatible-111111" alt="Codex">
  <img src="https://img.shields.io/badge/team_size-2%2B-orange" alt="Team size 2+">
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

Do not combine global and vendor installs for the same workflow. If a repo vendors `.codex/skills/*` and you also have `~/.codex/skills/*` for the same names, Codex may show duplicate skills in `/skills`. Prefer vendor mode for teams; remove the global copy with the uninstall command printed by `setup`.

### Then run a workflow command

Either install path, the workflow is the same. In Claude Code, use slash commands:

```
/issue       file a single branch-sized issue from a one-line brain dump
/dispatch    split a bigger brain dump across multiple teammates
/resolve     pick up issues assigned to you and implement them in parallel workers
```

In Codex, pick the matching skill from `/skills`:

```
issue       file a single branch-sized issue from a one-line brain dump
dispatch    split a bigger brain dump across multiple teammates
resolve     pick up issues assigned to you and implement them in parallel workers
```

### Vendor vs. global — which?

|  | Vendor (project-scope) | Global (user-scope) |
|---|---|---|
| Versions | Everyone on the team uses the same one (whatever's committed) | Each developer installs and updates independently |
| Onboarding | New hires get it on day 1 | New hires have to install themselves |
| Discoverability | `AGENTS.md`, `.claude/`, and `.codex/` are visible in the repo | Nothing in the repo says "we use this" |
| Repo footprint | Adds shared runtime dirs + 1 config | Just `.agent-teamflow` |
| Updates | Re-vendor when you want to pull upstream changes | `/teamflow-update` per developer |

Both modes use the same skills and the same config schema. Pick one mode per user/repo. For team repos, prefer vendor mode so everyone sees one committed copy of the workflow.

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

The actual workflow logic lives inside each runtime entrypoint — plain markdown runbooks any agent can read. `AGENTS.md` is the shared protocol. `.claude/commands/*.md` contains the Claude Code slash commands; `.codex/skills/*/SKILL.md` contains the matching Codex skills. Each pair holds the full workflow content, so updating one means updating the other.

## Setup, troubleshooting, FAQ

For the full config reference, both install paths in depth, common failure modes, and FAQ, see [SETUP.md](SETUP.md).

## Contributing

Adding a skill, fixing a runbook, or improving an example? See [CONTRIBUTING.md](CONTRIBUTING.md). Released under the [MIT License](LICENSE).
