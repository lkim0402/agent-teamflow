# Setup

## 1. Create your integration branches

For each team member, create a personal integration branch on your remote:

```bash
git checkout -b alice-staging origin/staging
git push origin alice-staging

git checkout -b bob-staging origin/staging
git push origin bob-staging
```

These sit between feature branches and the shared `staging` branch.

## 2. Copy the skills into your repo

```bash
cp -r .claude your-repo/
cp CLAUDE.md your-repo/CLAUDE.md   # or append to your existing CLAUDE.md
```

Or symlink if you want to track updates from this repo.

## 3. Create `.agent-teamflow` in your repo root

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

| Field | What it does |
|---|---|
| `issueTracker` | `"gitlab"` or `"github"` — determines which CLI (`glab`/`gh`) skills use |
| `project` | Repo path passed to `--repo` flags |
| `branches.main` | Production branch (skills never push here directly) |
| `branches.staging` | QA/integration target — where MRs/PRs point |
| `owners` | Map of git username shorthand → personal integration branch name |

## 4. Verify prerequisites

```bash
# GitHub
gh auth status

# GitLab
glab auth status

# git identity (skills use this to resolve the current owner)
git config user.email
```

The local part of your email (before `@`) should match a key in `owners`. For example, `alice@company.com` → looks up `alice` in `owners`.

## 5. Try it

Open Claude Code in your repo and run:

```
/issue add a health check endpoint to the API
```

That's it. The skill reads `.agent-teamflow`, resolves your identity, drafts an issue, and asks for confirmation before posting.

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
