# Setup

## 1. Copy the skills into your repo

```bash
cp -r .claude your-repo/
cp CLAUDE.md your-repo/CLAUDE.md   # or append to your existing CLAUDE.md
```

Or symlink if you want to track updates from this repo.

## 2. Create `.agent-teamflow` in your repo root

Start with the minimal config and add fields as you need them:

```json
{
  "issueTracker": "github",
  "project": "your-org/your-repo",
  "branches": {
    "main": "main",
    "staging": "staging"
  }
}
```

That's enough. Skills will merge feature branches directly into `staging`.

### Adding personal integration branches (optional)

If your team uses per-developer integration branches, add `owners`:

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

Skills resolve the current developer from `git config user.email` (local part before `@`), look them up in `owners`, and use their branch. If not found, they fall back to `branches.staging`.

### Field reference

| Field | Required | What it does |
|---|---|---|
| `issueTracker` | yes | `"gitlab"` or `"github"` — determines which CLI (`glab`/`gh`) skills use |
| `project` | yes | Repo path passed to `--repo` flags |
| `branches.main` | yes | Production branch (skills never push here directly) |
| `branches.staging` | yes | Default merge target — where MRs/PRs point |
| `owners` | no | Map of git username shorthand → personal integration branch name |

## 3. Adapting to your branching model

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

## 4. Verify prerequisites

```bash
# GitHub
gh auth status

# GitLab
glab auth status

# git identity (skills derive your username from this)
git config user.email
```

If you're using `owners`, the local part of your email (before `@`) must match a key in the map. `alice@company.com` → looks up `alice`.

## 5. Try it

Open Claude Code in your repo and run:

```
/issue add a health check endpoint to the API
```

The skill reads `.agent-teamflow`, resolves your identity, drafts an issue, and asks for confirmation before posting.

## Directory layout after setup

```
your-repo/
├── .agent-teamflow          ← team config
├── CLAUDE.md                ← tells Claude to read config before any skill
├── skills/                  ← skill logic (agent-agnostic runbooks)
│   ├── resolve.md
│   ├── git-auto-merge.md
│   ├── post-merge.md
│   ├── issue.md
│   ├── dispatch.md
│   └── prod-check.md
├── .claude/
│   └── commands/            ← Claude Code entrypoints (thin wrappers)
│       └── *.md             ← each just says "follow skills/X.md"
└── ... your project files
```

## Updating skills

Edit files in `skills/`. The `.claude/commands/` wrappers just point at them — no changes needed there. For other agents, point them at `skills/` directly or add your own adapter folder.
