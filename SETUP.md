# Setup

The fast path is in the [README's Quick start](README.md#quick-start). This doc covers both install paths in more depth and is the full config reference.

## Install paths

### Vendor into the repo (recommended for teams)

Skills are committed to your team's repo. Everyone gets the same version automatically; new hires onboard with no extra steps.

From inside your team's repo root:

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git .agent-teamflow-tmp \
  && cp -r .agent-teamflow-tmp/.claude .agent-teamflow-tmp/.codex .agent-teamflow-tmp/AGENTS.md . \
  && ln -sf AGENTS.md CLAUDE.md \
  && rm -rf .agent-teamflow-tmp
```

Review the added files (`.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`) and commit them. Claude Code picks up project-scope slash commands automatically, while Codex exposes matching skills under `/skills` running the same workflows.

**Updating in vendor mode.** There's no `/teamflow-update` for this path — re-vendor by running the install command again (it overwrites the shared paths and symlinks). Diff the changes against your committed copy, then commit the diff.

**Conflict notes.** If your repo already has `.claude/`, `.codex/`, or `AGENTS.md`, `cp -r` will merge / overwrite. Inspect before committing. To preserve your existing `AGENTS.md`, do the copy, then `git diff AGENTS.md` and reconcile manually.

### Global install (alternative — personal use only)

Runtime adapters are installed user-scope, working in every repo on your machine. Each developer installs and updates independently. Use this for solo evaluation or personal workflows, not for a team repo that already vendors agent-teamflow.

```bash
git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.agent-teamflow \
  && ~/.agent-teamflow/setup --all
```

The `setup` script can install one or both adapters:

```bash
./setup --all      # default: Claude Code commands + Codex skills
./setup --claude   # Claude Code commands only
./setup --codex    # Codex skills only
```

For Claude Code, it generates user-scope commands in `~/.claude/commands/`, rewriting the relative `AGENTS.md` reference to an absolute path. For Codex, it generates skills under `${CODEX_HOME:-~/.codex}/skills/<name>/` the same way.

**Updating.** Run `/teamflow-update` from your agent — it pulls the latest agent-teamflow and re-runs setup. Or manually: `cd ~/.agent-teamflow && git pull && ./setup --all`.

**Avoid duplicate Codex skills.** Do not combine global and vendor installs for the same workflow. If a repo vendors `.codex/skills/*` and you also have `~/.codex/skills/*` for the same names, Codex may show duplicate skills in `/skills`. Prefer vendor mode for teams; remove the global copy with the uninstall command printed by `setup`.

### Choosing between them

Vendor wins when:
- You have a team and want everyone on the same version.
- You want new hires to get the workflow with no separate install step.
- You want skills visible in the repo as documentation.

Global wins when:
- You're evaluating agent-teamflow before committing to it.
- You want one tool across many repos on your machine.
- Your team isn't ready to commit shared agent files to the repo.

Both modes use the same skills and the same `.agent-teamflow` config. Pick one mode per user/repo. For team repos, prefer vendor mode so everyone sees one committed copy of the workflow. To migrate from global to vendor, run the vendor install in your team's repo, commit it, then remove the global Codex skills (`rm -rf ~/.codex/skills/{dispatch,issue,...}`). To migrate from vendor to global, remove the committed files and run the global installer.

## `.agent-teamflow` config reference

The config lives at the repo root. `/teamflow-init` writes it for you, but here's the schema:

```json
{
  "issueTracker": "github",
  "project": "your-org/your-repo",
  "branches": {
    "main": "main",
    "staging": "staging"
  },
  "owners": {
    "alice": "alice-staging",
    "bob": "bob-staging"
  }
}
```

### Field reference

| Field | Required | Default | What it does |
|---|---|---|---|
| `issueTracker` | yes | — | `"gitlab"` or `"github"` — determines which CLI (`glab`/`gh`) skills use |
| `project` | yes | — | Repo path passed to `--repo` flags |
| `branches.main` | yes | — | Production branch (skills never push here directly) |
| `branches.staging` | yes | — | Default merge target — where MRs/PRs point |
| `owners` | no | — | Map of git username shorthand → personal integration branch name |
| `labels.doneInStaging` | no | `done-in-staging` | Label `/post-merge` applies to issues whose code has reached staging |
| `paths.workflowDir` | no | `docs/workflow` | Directory `/dispatch` writes workflow log files into |

## Adapting to your branching model

The names in `.agent-teamflow` drive everything — rename fields to match whatever your team already uses.

**Simple (no personal lanes):**
Feature branches merge directly to the shared integration branch. Omit `owners`.

```json
{
  "issueTracker": "github",
  "project": "your-org/your-repo",
  "branches": { "main": "main", "staging": "staging" }
}
```

**Personal lanes:**
Each developer has their own integration branch before the shared one. Add `owners`.

```json
{
  "branches": { "main": "main", "staging": "staging" },
  "owners": { "alice": "alice-staging", "bob": "bob-staging" }
}
```

**Different naming conventions:**
Your branch names, your rules. `develop`/`master`, `alice/integration`, `release` — configure whatever you have.

```json
{
  "branches": { "main": "master", "staging": "develop" },
  "owners": { "alice": "alice/integration", "bob": "bob/integration" }
}
```

**GitLab:**

```json
{
  "issueTracker": "gitlab",
  "project": "your-group/your-repo",
  "branches": { "main": "main", "staging": "staging" }
}
```

## Creating integration branches manually

If you skipped the auto-create in `/teamflow-init` (or did the manual install), each personal lane in `owners` must exist on origin:

```bash
git fetch origin staging
git push origin "origin/staging:refs/heads/alice-staging"
git push origin "origin/staging:refs/heads/bob-staging"
```

The shared `branches.staging` must also exist. Skills never create either automatically without explicit user approval.

## Verifying prerequisites

```bash
# Issue tracker auth
gh auth status        # if issueTracker = "github"
glab auth status      # if issueTracker = "gitlab"

# Git identity (skills derive your username from this)
git config user.email
```

If you're using `owners`, the local part of your email (before `@`) must match a key in the map. `alice@company.com` → looks up `alice`.

## Directory layout

### After vendor install (in your team's repo)

```
your-repo/
├── .agent-teamflow            ← team config
├── AGENTS.md                  ← shared protocol for all agents
├── CLAUDE.md -> AGENTS.md     ← Claude Code compatibility symlink
├── .claude/
│   └── commands/              ← Claude Code slash commands (full workflow content)
├── .codex/
│   └── skills/
│       ├── issue/             ← Codex skills (full workflow content)
│       ├── resolve/
│       └── ...
└── ... your project files
```

Each `.claude/commands/*.md` and `.codex/skills/*/SKILL.md` is self-contained — the full workflow lives inside it, so no other directory needs to be vendored. Claude Code picks up `.claude/commands/*.md` automatically when run from inside the repo. Codex picks up the matching skills in `/skills`. Current Codex CLI releases do not reliably expose custom prompts as slash commands, so select `issue`, `resolve`, and related skills from `/skills`.

### After global install

```
~/.agent-teamflow/              ← source of truth (cloned by the installer)
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── .claude/commands/
├── .codex/skills/issue/
├── .codex/skills/resolve/
├── .codex/skills/...
└── setup

~/.claude/commands/             ← generated when installing Claude support
├── teamflow-init.md
├── resolve.md
└── ...

~/.codex/skills/                 ← generated when installing Codex support
├── issue/SKILL.md
├── resolve/SKILL.md
└── ...
```

`setup` copies each entrypoint file verbatim (rewriting only the `AGENTS.md` reference to an absolute path). The user-scope copy holds the full workflow content — no further indirection.

## Updating

**Vendor install** — re-run the vendor install command from the team repo root. It overwrites `.claude/`, `.codex/`, `AGENTS.md`, and `CLAUDE.md` with the latest from `main`. Diff against your committed copy and commit the changes.

**Global install** — `/teamflow-update` does the work. Or manually: `cd ~/.agent-teamflow && git pull && ./setup --all`. `setup` is idempotent — re-running regenerates the selected user-scope adapters from the latest source.

## Uninstalling

**Vendor install** — remove `.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, and `.agent-teamflow` from the repo. Commit the deletion.

**Global install** — the final lines of `setup`'s output print the exact commands to remove everything it installed. Run those, then delete `.agent-teamflow` from any repo where you configured it.

## Troubleshooting

**Claude slash commands don't appear after install.**
Restart Claude Code (close and reopen). It scans `.claude/commands/` (project-scope, vendor install) and `~/.claude/commands/` (user-scope, global install) on startup. After a vendor install, confirm `ls .claude/commands/teamflow-*.md` from your repo root lists the wrappers. After a global install, confirm `ls ~/.claude/commands/teamflow-*.md`.

**Codex doesn't pick up agent-teamflow globally.**
Confirm `ls ${CODEX_HOME:-$HOME/.codex}/skills/issue/SKILL.md` exists. If it does not, re-run `~/.agent-teamflow/setup --codex`. In Codex, pick `issue`, `resolve`, and related skills from `/skills`, not `/issue`.

**`/issue` or `/dispatch` fails with an auth error.**
The issue tracker CLI isn't logged in. Run `gh auth status` (or `glab auth status`) — if it reports "not logged in", run `gh auth login` / `glab auth login` and retry. For GitHub Enterprise or self-hosted GitLab, also set the host (`GH_HOST=ghe.example.com gh auth login` or `glab auth login --hostname gitlab.example.com`).

**Skills warn "falling back to staging" or "owner not found".**
The local part of your `git config user.email` doesn't match any key in `owners`. Either rename your alias in `.agent-teamflow` (`/teamflow-init` and edit, or hand-edit the JSON), or set `git config user.email` to something matching an entry. Skills then resolve your personal lane correctly.

**Skills warn "branch does not exist on origin".**
Your personal integration branch was never created on the remote. Push it once: `git fetch origin staging && git push origin "origin/staging:refs/heads/<your-alias>-staging"`. Or rerun `/teamflow-init` and approve auto-creation in Step 7.

**`/git-auto-merge` fails when pushing to `staging`.**
Branch protection on `staging` blocks direct pushes. Two options: (a) update protection to allow your service account / bot, or (b) skip the auto-merge to `staging` and create a PR manually from `<your-alias>-staging` → `staging` via the GitHub/GitLab UI. The skill should still successfully push your feature branch and update your personal-lane MR/PR.

**`/resolve` batch-merge stops on a conflict.**
Two feature branches in the same batch touched the same file. The skill halts before pushing the conflicted result — your worktrees are intact. Resolve manually in the affected worktree, commit, then rerun `/git-auto-merge` from that worktree. Going forward, ensure `/issue` keeps "same file in same chunk" so siblings don't collide.

**Setup fails on `bun` or `node` errors.**
agent-teamflow doesn't use either. If you see those errors you're running another tool's setup by mistake. Re-clone agent-teamflow into a clean path: `git clone --depth 1 https://github.com/lkim0402/agent-teamflow.git ~/.agent-teamflow`.

## FAQ

**Do I need this if I'm a solo developer?**
No. The skills still work (see [`examples/solo/`](examples/solo/)), but the value prop is keeping multiple developers' agents from colliding. If it's just you, vanilla Claude Code or Codex workflows may be enough.

**What if my team uses trunk-based development with no staging branch?**
Set `branches.staging` to `main` (or your equivalent). Skills will merge features straight to `main`. The integration-branch buffer is optional — without `owners`, features go directly to the configured target.

**What if our `main` is called `master` (or `production`, or `release`)?**
Configure it that way. Skills never refer to branch names by string literal — they read `branches.main` and `branches.staging` from `.agent-teamflow`.

**Does this work with GitHub Enterprise or self-hosted GitLab?**
Yes. `gh` and `glab` both support custom hosts. Authenticate once (`GH_HOST=...` or `glab auth login --hostname ...`), and the skills' CLI calls inherit that config. No agent-teamflow setting is needed.

**Can I use this in a monorepo?**
Yes, but the config lives at the repo root only — one `.agent-teamflow` per repo, not per package. The branch-sizing rule in `/issue` becomes more important in a monorepo since touching multiple packages is common.

**What if a teammate does not use a supported coding agent (or refuses to install)?**
Fine. They use git as normal; the skills are just helpful automation for whoever has them. Their feature branches still merge into the shared staging the same way. Just don't put them in `owners` — that field is for people whose agents need a personal lane.

**I committed `.agent-teamflow` and now teammates' agents are confused by my settings.**
`.agent-teamflow` is meant to be committed — it's per-repo shared config. The `owners` map is the source of routing, not a per-developer secret. If a teammate's email local part isn't in `owners`, they fall back to `staging` with a warning, which is the right behavior.

**What if I want to skip the global install and just vendor agent-teamflow into one repo?**
That's the recommended path for teams. See [Vendor into the repo](#vendor-into-the-repo-recommended-for-teams) at the top of this file.

**Where do I report a bug or request a feature?**
[github.com/lkim0402/agent-teamflow/issues](https://github.com/lkim0402/agent-teamflow/issues). See [CONTRIBUTING.md](CONTRIBUTING.md) for the conventions around adding new skills.
