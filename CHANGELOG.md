# Changelog

All notable changes to agent-teamflow are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Shared `AGENTS.md` protocol read by both Claude Code and Codex entrypoints.
- Codex skill entrypoints under `.codex/skills/<name>/` so current Codex CLI users can pick workflows explicitly from `/skills`.
- `/teamflow-help` — prints a static digest of all installed agent-teamflow slash commands. Useful for teammates who just ran the installer and want to see what they got.
- Troubleshooting and FAQ sections in `SETUP.md` covering the most likely onboarding failures (auth, missing branches, branch protection, monorepos, GHE, trunk-based dev).

### Changed
- `setup` now supports `--all`, `--claude`, and `--codex`, installing Claude Code commands and/or Codex skills.
- Workflow content is now inlined into each runtime entrypoint (`.claude/commands/*.md` and `.codex/skills/*/SKILL.md`) instead of being referenced from a shared `skills/` directory. Each entrypoint is self-contained.
- Codex skills no longer carry the `at-` prefix — directories renamed from `.codex/skills/at-<name>/` to `.codex/skills/<name>/`, with matching frontmatter, headings, and `agents/openai.yaml` updates. The `/skills` picker now shows `issue`, `resolve`, `dispatch`, etc. directly.
- Runbooks now use runtime-neutral wording for workers, approval prompts, and effort classification.
- **Vendor install is now the recommended path for teams.** README leads with vendoring agent-teamflow into the team repo (workflows committed, everyone on the same version, new hires onboard automatically). Global install is documented as the alternative for solo evaluation and per-developer use.
- README has a vendor-vs-global comparison table to help users pick.
- SETUP.md reorganized: install paths first, with separate Updating/Uninstalling guidance for each mode.

### Removed
- `skills/` directory (canonical runbooks) — replaced by the inlined content inside each runtime entrypoint.
- `.codex/prompts/` directory (legacy prompt wrappers) — Codex now uses `.codex/skills/*/SKILL.md` directly.

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
- At this release, workflow logic lived in `skills/` and `.claude/commands/` held thin wrappers that the `setup` script propagated user-scope (later collapsed; see Unreleased).
