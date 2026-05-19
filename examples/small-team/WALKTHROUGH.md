# Walkthrough: small team with personal integration branches

Two developers, each with their own integration branch sitting between feature branches and the shared `staging`. This is the canonical agent-teamflow setup — agents from both developers run in parallel without overwriting each other's work-in-progress.

## Config

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

Skills resolve each developer's lane from `git config user.email`. `alice@company.com` → `alice` → `alice-staging`. Bob → `bob-staging`.

## Branch structure

```
feature/5-checkout-validation ─┐
feature/6-payment-receipts     ─┤→ alice-staging ─┐
                                                   ├→ staging → main
feature/7-shipping-zones       ─┐                 │
feature/8-cart-pagination      ─┤→ bob-staging  ──┘
```

---

## Scenario — dispatching a day's work across two developers

Alice and Bob are working on an e-commerce repo. Alice owns checkout/payments; Bob owns shipping/cart.

### Step 1 — Bob dispatches the day's work

Bob has a brain dump of what needs to ship. He runs:

```
/dispatch
alice: add validation to the checkout form — block submission if any required field is empty
alice: fix payment receipt emails — they're missing the order total
bob: add shipping zones config — let admins define rates per region
bob: paginate the cart line items when over 50 items
```

Claude reads `.agent-teamflow`, parses the brain dump, honors the explicit `alice:` / `bob:` hints, and verifies no cross-assignee blockers (none here — checkout/payments don't depend on shipping/cart).

It writes `docs/workflow/workflow-20260519-1030.md` capturing the split and rationale, then files four issues:

- #5 — Alice: "Block checkout submission on missing required fields"
- #6 — Alice: "Include order total in payment receipt emails"
- #7 — Bob: "Add shipping zones admin config"
- #8 — Bob: "Paginate cart line items"

### Step 2 — Alice and Bob resolve in parallel

Both developers open Claude Code in the same repo, at the same time.

**Alice's terminal:**

```
/resolve
```

Claude fetches Alice's open issues (#5, #6). She picks both. Claude checks whether `alice-staging` is behind `staging` — it is (Bob merged a doc fix yesterday). It asks Alice if she wants to sync; she clicks **Yes — sync now**. Then it spawns two parallel forks:

```
Model assignments: #5 → sonnet, #6 → sonnet

Batch 1: 2 ready

| Issue | Status | Branch                       | Files | Commit  | Summary                              |
|-------|--------|------------------------------|-------|---------|--------------------------------------|
| #5    | ready  | 5-checkout-validation        | 2     | a3f812c | feat(checkout): validate required    |
| #6    | ready  | 6-payment-receipts           | 1     | d91cc4a | fix(payments): include total in email|

MR/PR (alice-staging → staging): https://github.com/your-org/your-repo/pull/10
```

**Bob's terminal (simultaneously):**

```
/resolve
```

Bob picks #7 and #8. Two forks spawn in his own worktrees, off `bob-staging`. They come back ready and Claude opens PR #11 (`bob-staging` → `staging`).

Neither developer's worktrees touch the other's branches. No conflicts, no coordination needed.

### Step 3 — Pre-staging review

Before either PR merges to `staging`, Alice runs:

```
/prod-check
```

Claude scopes to her commits since midnight and cross-references callers across the whole repo:

```
| Severity | File:Line              | Risk                              | Suggested fix                    |
|----------|------------------------|-----------------------------------|----------------------------------|
| Warning  | src/checkout/form.tsx:24| Required check uses == (loose)   | Use !value.trim() for strings    |
| Advice   | src/emails/receipt.ts:8| Total format hardcodes USD       | Use Intl.NumberFormat with locale|
```

Alice fixes both, commits, pushes. PR #10 auto-updates.

### Step 4 — Merge to staging and label

Alice merges PR #10 via the GitHub UI. Bob does the same for PR #11. Then each runs:

```
/post-merge
```

Claude scans their just-merged PR, reads `Closes #5`, `Closes #6` (Alice) and `Closes #7`, `Closes #8` (Bob) from the body, and labels each issue `done-in-staging`. The issues stay open — they auto-close when `staging` flows to `main` on release day.

---

## What this demonstrates

| Skill | What happened |
|---|---|
| `/dispatch` | Split a brain dump across two assignees with no cross-assignee blockers; wrote a workflow log |
| `/resolve` (×2) | Alice and Bob ran parallel forks simultaneously — four branches, zero conflicts |
| `/git-auto-merge` | Each developer's lane received their work independently; two PRs to `staging` opened |
| `/prod-check` | Caught a loose-equality bug before staging |
| `/post-merge` | Issues labeled `done-in-staging` after each PR merged |

The key win: agents from both developers ran at the same time, in the same repo, without coordinating. Personal lanes (`alice-staging`, `bob-staging`) act as a buffer that prevents any in-flight work from one developer landing on another's branch.
