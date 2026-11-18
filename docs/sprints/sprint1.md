# Sprint 1 notes

Sprint 1 ran from Saturday 7 November to Sunday 8 November 2026. The review and retrospective were planned for Monday 9 November at 9:30 AM.

## Sprint goal

A minimum working simulator: the command line loads a scenario, runs it day by day and prints results per product.

The goal was not met inside the sprint. The domain modules were mostly done by Sunday night, but the engine and the command line reached `main` on Friday 13 November (PR #64), five days late. This is recorded as DV-10 in `docs/Deviation_Log.md`.

## Backlog and outcome

Status and merge dates are taken from the repository history. 29 of the 63 story points were merged by the end of Sunday 8 November, and all 63 by Wednesday 18 November.

| Item | What | Owner | Points | Merged | PR |
|---|---|---|---:|---|---|
| B-01 | GitHub Project board | Meghana | 3 | Sat 7 Nov | (board, no PR) |
| B-02 | Product model (SCM-F-001) | Meghana | 2 | Sat 7 Nov | #15 |
| B-03 | Simulation clock and event log (SCM-F-030) | Shraddha | 2 | Tue 10 Nov | #50 |
| B-04 | Supplier model (SCM-F-010) | Rushmitha | 2 | Sat 7 Nov | #19 |
| B-05 | Supplier registry (SCM-F-011) | Rushmitha | 2 | Sat 7 Nov | #30 |
| B-06 | Economic order quantity (SCM-F-004) | Shraddha | 2 | Wed 11 Nov | inside #59 (DV-16) |
| B-07 | Warehouse stock (SCM-F-003) | Siri | 3 | Wed 11 Nov | #59 |
| B-08 | Demand generator (SCM-F-020) | Siri | 3 | Wed 11 Nov | #18 |
| B-09 | Customer order model (SCM-F-021) | Meghana | 2 | Sat 7 Nov | #14 |
| B-10 | Customer order book (SCM-F-022) | Spoorthi | 3 | Sun 8 Nov | #42 |
| B-11 | FIFO allocation and backorders (SCM-F-023) | Spoorthi | 3 | Sun 8 Nov | #43 |
| B-12 | Product catalog (SCM-F-002) | Meghana | 2 | Sun 8 Nov | #31 |
| B-13 | Config loader and validation (SCM-F-031) | Meghana | 5 | Wed 11 Nov | #33 |
| B-14 | Purchase order (SCM-F-013) | Rushmitha | 3 | Sun 8 Nov | #44 |
| B-15 | Supplier selection (SCM-F-012) | Rushmitha | 5 | Sun 8 Nov | #45 |
| B-16 | Safety stock and reorder point (SCM-F-005) | Siri | 3 | Wed 11 Nov | #59 |
| B-17 | Purchase order lifecycle (SCM-F-014) | Siri | 5 | Wed 11 Nov | #47 |
| B-18 | Moving average forecast (SCM-F-024) | Meghana | 2 | Sun 8 Nov | #32 |
| B-19 | Simulation engine MVP (SCM-F-035) | Spoorthi | 5 | Fri 13 Nov | #64 |
| B-20 | Command-line interface MVP (SCM-F-035) | Spoorthi | 3 | Fri 13 Nov | #64 |
| B-21 | Sprint 1 demo video | Siri | 1 | Wed 18 Nov | docs/videos/sprint1_demo.mp4 |
| B-22 | Sprint 1 notes (this file) | Shraddha | 1 | Tue 17 Nov | #87 |
| B-42 | SRS, SAD and Test Plan v1.0 in docs/ | Shraddha | 1 | Wed 11 Nov | #52 |

CI with pinned requirements, pytest settings and the sample scenario went in first, on Saturday 7 November (PR #1).

## Progress by day

- Saturday 7 November: CI and project setup (#1), customer order model (#14), product model (#15), supplier model (#19) and supplier registry (#30) merged.
- Sunday 8 November: order book (#42), purchase order (#44), FIFO allocation (#43), supplier selection (#45), moving average forecast (#32) and product catalog (#31) merged.
- Monday 9 to Wednesday 11 November: the remaining Sprint 1 items were merged during Sprint 2: clock and event log (#50), SRS, SAD and Test Plan v1.0 (#52), warehouse, EOQ and reorder point (#59), purchase order lifecycle (#47), demand generator (#18) and config loader (#33).
- Friday 13 November: engine MVP and command line merged together (#64).
- Tuesday 17 November: these notes (#87).
- Wednesday 18 November: the Sprint 1 demo video, recorded on the engine MVP commit d62bfb3 so it shows the Sprint 1 version of the product.

## Blockers

- The engine MVP (B-19) depended on almost every other Sprint 1 item, so it could not be finished until those were merged. The command line (B-20) and the Sprint 1 video (B-21) waited on the engine in turn.
- Warehouse, EOQ and reorder point existed on several branches at once. PR #48 merged an outdated branch with an old inventory.py, PR #59 replaced it, and PRs #61 and #62 were merged with no file changes. B-06 was merged inside #59 rather than in its own PR (DV-16).
- Review of the config loader (B-13) found inputs that crashed or were silently accepted, so validation was widened before merge (DV-07).

## Reassignments

None. B-06 was written by Shraddha and merged by Siri inside PR #59; authorship is recorded in DV-16.

## Review outcome

At the end of Sunday 8 November the domain modules for products, suppliers, purchase orders, customer orders and forecasting were on `main` with their tests passing in CI. There was no runnable simulator to demonstrate, because the engine and command line were not merged.

## Retrospective

- What went well: every merged item came with unit tests and passed CI, and the branch ruleset kept direct pushes off `main`.
- What did not go well: the engine sat at the end of a long dependency chain and slipped, so Sprint 1 ended without a product that runs. Duplicate branches for the same work caused confusing merges.
- Actions for Sprint 2: one item per branch and per pull request; delete a branch once it is merged; pull `main` before starting new work; flag a blocked item in the group as soon as it is blocked.
