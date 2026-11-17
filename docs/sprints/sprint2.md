# Sprint 2 notes

Sprint 2 was planned for Monday 9 to Wednesday 11 November 2026, with the code freeze on Tuesday 10 November at 11:59 PM. The final code was merged on Monday 16 November (PR #78), and work on reports, tests and documents continued to Tuesday 17 November. The new dates are recorded as DV-11 in `docs/Deviation_Log.md`.

## Sprint goal

The complete product: costs, supplier delays, transport cost, two forecasting methods, KPIs, CSV export, system and non-functional tests, and all four reports.

## Backlog and outcome

Status as of Tuesday 17 November, taken from the repository history. 12 of the 58 planned story points were merged by Wednesday 11 November, and 39 by Tuesday 17 November.

| Item | What | Owner | Points | Status | PR |
|---|---|---|---:|---|---|
| B-23 | CI with line and branch coverage (SCM-NF-003) | Meghana | 3 | Merged Mon 9 Nov | #46 |
| B-24 | Random supplier delays (SCM-F-015) | Rushmitha | 3 | Merged Fri 13 Nov | #63 |
| B-25 | Cost tracker (SCM-F-006) | Siri | 3 | Merged Wed 11 Nov | #48 |
| B-26 | Shipments and transport cost (SCM-F-032) | Shraddha | 2 | In review | |
| B-27 | CSV export and text summary (SCM-F-034) | Spoorthi | 3 | Merged Fri 13 Nov | #64 |
| B-28 | Exponential smoothing (SCM-F-025) | Rushmitha | 3 | Merged Tue 10 Nov | #53 |
| B-29 | KPI calculator (SCM-F-033) | Siri | 3 | Merged Wed 11 Nov | #60 |
| B-30 | Simulation engine v2 (SCM-F-035) | Siri | 5 | Merged Mon 16 Nov | #78 |
| B-31 | Command-line interface v2 (SCM-F-035) | Spoorthi | 3 | Merged Fri 13 Nov | #64 |
| B-32 | Non-functional tests (SCM-NF-001 to 005) | Rushmitha | 3 | Merged Sat 14 Nov | #75 |
| B-33 | System validation tests ST-01 to ST-08 | Spoorthi | 5 | In review | |
| B-34 | Demo scenario files | Shraddha | 2 | Merged Sun 15 Nov | #58 |
| B-35 | Deviation log, SRS v1.1 and SAD v1.1 | Meghana | 3 | In review | #54 |
| B-36 | Unit Test Report | Rushmitha | 3 | Merged Mon 16 Nov | #77 |
| B-37 | Test Plan v1.1 | Rushmitha | 3 | Merged Mon 16 Nov | #76, #83 |
| B-38 | System Validation Report | Spoorthi | 3 | Not started | |
| B-39 | Code Coverage Report | Meghana | 2 | In review | |
| B-40 | Branch Coverage Report | Siri | 2 | Merged Mon 16 Nov | #73 |
| B-41 | Sprint 2 demo video | Meghana | 2 | To do | |
| B-43 | Final README | Shraddha | 1 | In review | #56 |
| B-44 | Sprint 2 notes (this file) | Shraddha | 1 | In review | |

Added during the sprint: a desktop window for the simulator (new requirement SCM-F-036, tests TC-GUI-01 to 07), built by Meghana and in review. It was added after the TA confirmed on 17 November that a GUI is required (DV-18).

## Progress by day

- Monday 9 November: line and branch coverage with an 80% gate added to CI (#46).
- Tuesday 10 November: clock and event log (#50) and exponential smoothing with MAE and MAPE (#53) merged.
- Wednesday 11 November: SRS, SAD and Test Plan v1.0 (#52), cost tracker (#48), purchase order lifecycle (#47), warehouse, EOQ and reorder point (#59), demand generator (#18), config loader (#33) and KPI calculator (#60) merged.
- Friday 13 November: supplier delays (#63) and the engine MVP with the command line and CSV export (#64) merged.
- Saturday 14 November: PDF names fixed (#74) and non-functional tests merged (#75).
- Sunday 15 November: demo scenarios merged (#58).
- Monday 16 November: engine v2 with delays and transport cost (#78), Test Plan v1.1 (#76, #83), Branch Coverage Report (#73) and Unit Test Report (#77) merged.
- Tuesday 17 November: system validation tests, shipments, the desktop window, the README and these notes submitted for review.

## Blockers and resolutions

- The engine MVP from Sprint 1 was late, so everything that needed a running simulator (engine v2, KPIs on real runs, demo scenarios, system tests, reports) moved later. The code freeze moved from 10 November to 16 November, and every report states the commit it was run on (DV-10, DV-11).
- An interim engine v2 was written as a separate function instead of extending the MVP class. It was not merged; the features were rebuilt on the class in #78 (DV-08).
- Shipments (B-26) was not ready when the engine needed it, so the engine computes transport cost itself when a purchase order is placed (DV-12).
- Code review found inputs that crashed or were silently accepted in config loading, forecasting and the event log; validation was tightened (DV-07, DV-14, DV-15).
- The system tests (B-33) were not written by the freeze, so the Test Plan v1.1 listed ST-01 to ST-08 as planned (DV-17).

## Reassignments

None.

## Review outcome

By Monday 16 November the simulator ran end to end from the command line with all three demo scenarios. On `main` at commit 39db368 there were 410 tests, all passing, with 98% coverage including branches. The unreliable-suppliers scenario is the only one that lowers service level (93.33%), which is the expected effect of late deliveries.

## Retrospective

- What went well: reviews caught real defects before merge, each merged module has unit tests, and every difference from the SRS, SAD and Test Plan is recorded in the deviation log.
- What did not go well: the sprint plan's dates were not met, mostly because of the late engine, and several branches were opened against an outdated `main`.
- Actions: merge the remaining items in dependency order (GUI, system tests, shipments, documents, README last), record the Sprint 2 video, and tag the release once `main` is final.
