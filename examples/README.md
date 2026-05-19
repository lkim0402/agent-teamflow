# Examples

Three narrative walkthroughs showing the same skills under different team setups. None of these are runnable projects — each folder contains a `.agent-teamflow` config and a `WALKTHROUGH.md` describing what happens when the skills are invoked.

| Scenario | Team | Branch model | Highlights |
|---|---|---|---|
| [`solo/`](solo/) | 1 dev | `feature → staging → main` | Simplest case. No `owners` map. One agent at a time, no parallelism worry. |
| [`small-team/`](small-team/) | 2 devs | `feature → <owner>-staging → staging → main` | Personal integration branches. `/dispatch` splits work, parallel `/resolve` runs in two terminals. |
| [`larger-team/`](larger-team/) | 4 devs | `feature → staging → main` (no lanes) | Shared `staging` for everyone. Branch-sizing in `/issue` becomes load-bearing. `/prod-check` before staging merge. |

The skills don't care which model you pick — they read your `.agent-teamflow` and adapt. See [SETUP.md](../SETUP.md) for the full config reference.
