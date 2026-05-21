# Changelog

All notable changes to agent-teamflow are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Shared `AGENTS.md` protocol plus Codex prompts under `.codex/prompts/`.
- Codex skill entrypoints under `.codex/skills/at-*/` so current Codex CLI users can pick workflows explicitly from `/skills`.
- Runtime entrypoints now live directly under `.claude/commands/` and `.codex/prompts/`; `CLAUDE.md` is a symlink to `AGENTS.md`, and `CODEX.md` is not used.
- `/teamflow-help` — prints a static digest of all installed agent-teamflow slash commands. Useful for teammates who just ran the installer and want to see what they got.
- Troubleshooting and FAQ sections in `SETUP.md` covering the most likely onboarding failures (auth, missing branches, branch protection, monorepos, GHE, trunk-based dev).

### Changed
- `setup` now supports `--all`, `--claude`, and `--codex`, installing Claude Code commands and/or Codex prompts plus Codex skills.
- Runbooks now use runtime-neutral wording for workers, approval prompts, and effort classification.
- **Vendor install is now the recommended path for teams.** README leads with vendoring agent-teamflow into the team repo (skills committed, everyone on the same version, new hires onboard automatically). Global install is documented as the alternative for solo evaluation and per-developer use.
- README has a vendor-vs-global comparison table to help users pick.
- SETUP.md reorganized: install paths first, with separate Updating/Uninstalling guidance for each mode.

## [0.1.0] - 2026-05-19

Initial public release.

### Added
- **Eight slash commands** covering the multi-developer team workflow:
  - `/teamflow-init` — bootstrap a repo (writes `.agent-teamflow`, optionally creates integration branches).
  - `/teamflow-update` — pull the latest agent-teamflow and re-register slash commands.
  - `/issue` — draft branch-sized issues from a brain dump, post on confirmation.
  - `/dispatch` — split a brain dump across teammates, write a workflow log, file issues.
  - `/resolve` — pick up issues, implement each in parallel worktree workers, batch-merge.
  - `/git-auto-merge` — commit, push, merge into your lane, open/update MR/PR to staging.
  - `/post-merge` — after merging, label linked issues with the "done in staging" label.
  - `/prod-check` — pre-production diff review for impact, contracts, auth, stability.
- **One-paste installer** (`setup` bash script) that registers user-scope slash commands at `~/.claude/commands/`, rewriting paths to absolute so commands work from any repo.
- **`.agent-teamflow` config schema** with required fields (`issueTracker`, `project`, `branches.main`, `branches.staging`), optional `owners` map for personal integration branches, and optional `labels.doneInStaging` (default `done-in-staging`) and `paths.workflowDir` (default `docs/workflow`).
- **Three example walkthroughs** under `examples/` covering distinct team setups: solo developer, small team with personal lanes, larger team on shared staging.
- **Open-source basics**: MIT LICENSE, CONTRIBUTING.md, this CHANGELOG.

### Notes
- GitHub and GitLab are both supported via the `issueTracker` config flag.
- Skills are agent-agnostic markdown runbooks in `skills/`; `.claude/commands/` is a thin Claude Code adapter that the `setup` script propagates user-scope.
