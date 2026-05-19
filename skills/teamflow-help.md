# teamflow-help

Print a digest of all agent-teamflow slash commands. Run when a teammate has just installed agent-teamflow and forgot what's in it, or whenever someone asks "what does this give me?"

This skill is a static print — no file I/O, no config, no remote calls. It must be kept in sync manually when new commands are added (see CONTRIBUTING.md). The list below is the source of truth.

Run **in the main conversation** — this is interactive feedback for the user. Do not fork.

---

## Execution

### Step 1. Print the digest verbatim

Output the block below exactly. Preserve column alignment so it renders cleanly in a terminal.

```
agent-teamflow — 9 slash commands

Setup
  /teamflow-init    Bootstrap this repo (writes .agent-teamflow, optionally
                    creates personal integration branches on origin)
  /teamflow-update  Pull the latest agent-teamflow and re-register commands
  /teamflow-help    Print this list

Issue lifecycle
  /issue            Draft one or more branch-sized issues from a brain dump
  /dispatch         Split a brain dump across teammates, write a workflow log
  /resolve          Pick up your assigned issues, implement each in a
                    parallel worktree, batch-merge when done
  /git-auto-merge   Commit + push + merge into your lane + open PR to staging
  /post-merge       After a PR merges to staging, label linked issues as
                    "done in staging"

Review
  /prod-check       Pre-production diff review for impact, contracts, auth,
                    stability, and regressions

Docs:            https://github.com/lkim0402/agent-teamflow
Quick start:     README.md
Troubleshooting: SETUP.md (Troubleshooting + FAQ sections)
Contributing:    CONTRIBUTING.md
```

### Step 2. Add a contextual hint if relevant

After printing the digest, check whether `.agent-teamflow` exists at the repo root via `test -f .agent-teamflow`.

- If it does NOT exist: append one line — `Tip: this repo is not configured yet. Run /teamflow-init first.`
- If it DOES exist: append one line — `Tip: this repo is configured. Try /issue, /dispatch, or /resolve to start work.`

That's the whole skill.

## Hard rules

- **Static output** — do not invent commands, do not omit commands, do not reorder. The list reflects what `setup` registers user-scope; anything else would mislead.
- **No emojis.**
- **No file modifications.** This skill is read-only.
