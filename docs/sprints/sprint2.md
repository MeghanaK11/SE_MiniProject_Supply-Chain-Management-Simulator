# Sprint 2 notes

Sprint 2 was planned for Monday 9 to Wednesday 11 November 2026, with the code freeze on Tuesday 10 November at 11:59 PM. The final engine was merged on Monday 16 November (PR #78), the remaining code, tests, reports and documents on Tuesday 17 November, and the last documents and both videos on Wednesday 18 November. The new dates are recorded as DV-11 in `docs/Deviation_Log.md`.

## Sprint goal

The complete product: costs, supplier delays, transport cost, two forecasting methods, KPIs, CSV export, system and non-functional tests, and all four reports.

## Backlog and outcome

Status and merge dates are taken from the repository history. 12 of the 58 planned story points were merged by Wednesday 11 November, and all 58 by Wednesday 18 November. The desktop window added 11 more points during the sprint (B-45 to B-49), for 69 in total, all done.

| Item | What | Owner | Points | Merged | PR |
|---|---|---|---:|---|---|
| B-23 | CI with line and branch coverage (SCM-NF-003) | Meghana | 3 | Mon 9 Nov | #46 |
| B-24 | Random supplier delays (SCM-F-015) | Rushmitha | 3 | Fri 13 Nov | #63 |
| B-25 | Cost tracker (SCM-F-006) | Siri | 3 | Wed 11 Nov | #48 |
| B-26 | Shipments and transport cost (SCM-F-032) | Shraddha | 2 | Tue 17 Nov | #90 |
| B-27 | CSV export and text summary (SCM-F-034) | Spoorthi | 3 | Fri 13 Nov | #64 |
| B-28 | Exponential smoothing (SCM-F-025) | Rushmitha | 3 | Tue 10 Nov | #53 |
| B-29 | KPI calculator (SCM-F-033) | Siri | 3 | Wed 11 Nov | #60 |
| B-30 | Simulation engine v2 (SCM-F-035) | Siri | 5 | Mon 16 Nov | #78 |
| B-31 | Command-line interface v2 (SCM-F-035) | Spoorthi | 3 | Fri 13 Nov; test TC-SIM-11 on Tue 17 Nov | #64, #95 |
| B-32 | Non-functional tests (SCM-NF-001 to 005) | Rushmitha | 3 | Sat 14 Nov | #75 |
| B-33 | System validation tests ST-01 to ST-08 | Spoorthi | 5 | Tue 17 Nov | #89 |
| B-34 | Demo scenario files | Shraddha | 2 | Sun 15 Nov | #58 |
| B-35 | Deviation log, SRS v1.1 and SAD v1.1 | Meghana | 3 | Tue 17 Nov | #54 |
| B-36 | Unit Test Report | Rushmitha | 3 | Mon 16 Nov | #77 |
| B-37 | Test Plan v1.1 | Rushmitha | 3 | Mon 16 Nov; GUI rows on Tue 17 Nov | #76, #83, #92 |
| B-38 | System Validation Report | Spoorthi | 3 | Tue 17 Nov | #93 |
| B-39 | Code Coverage Report | Meghana | 2 | Tue 17 Nov | #79 |
| B-40 | Branch Coverage Report | Siri | 2 | Mon 16 Nov | #73 |
| B-41 | Sprint 2 demo video | Meghana | 2 | Wed 18 Nov | docs/videos/sprint2_demo.mp4 |
| B-43 | Final README | Shraddha | 1 | Tue 17 Nov | #56 |
| B-44 | Sprint 2 notes (this file) | Shraddha | 1 | Tue 17 Nov | #88 |
| B-45 | Desktop window (SCM-F-036), added during the sprint | Meghana | 5 | Tue 17 Nov | #91 |
| B-46 | GUI: Test Plan rows TC-GUI-01 to 07 and RTM entry | Rushmitha | 2 | Tue 17 Nov | #92 |
| B-47 | GUI: system validation of the window | Spoorthi | 2 | Tue 17 Nov | #93 |
| B-48 | GUI: README section for the desktop window | Shraddha | 1 | Tue 17 Nov | #56 |
| B-49 | GUI: manual check on Windows and screenshots | Siri | 1 | Wed 18 Nov | #104 |

B-45 to B-49 were added during the sprint, after the TA confirmed on 17 November that a GUI is required. The window is new requirement SCM-F-036 with tests TC-GUI-01 to 07, recorded as DV-18.

## Progress by day

- Monday 9 November: line and branch coverage with an 80% gate added to CI (#46).
- Tuesday 10 November: clock and event log (#50) and exponential smoothing with MAE and MAPE (#53) merged.
- Wednesday 11 November: SRS, SAD and Test Plan v1.0 (#52), cost tracker (#48), purchase order lifecycle (#47), warehouse, EOQ and reorder point (#59), demand generator (#18), config loader (#33) and KPI calculator (#60) merged.
- Friday 13 November: supplier delays (#63) and the engine MVP with the command line and CSV export (#64) merged.
- Saturday 14 November: PDF names fixed (#74) and non-functional tests merged (#75).
- Sunday 15 November: demo scenarios merged (#58).
- Monday 16 November: engine v2 with delays and transport cost (#78), Test Plan v1.1 (#76, #83), Branch Coverage Report (#73) and Unit Test Report (#77) merged.
- Tuesday 17 November: Sprint 1 and 2 notes (#87, #88), shipments (#90), system validation tests (#89), the desktop window (#91) and its Test Plan rows (#92), deviation log with SRS and SAD v1.1 (#54), Code Coverage Report (#79), System Validation Report (#93), README (#56), the CLI test TC-SIM-11 (#95) and the matching Test Plan and System Validation Report updates (#97, #98) merged.
- Wednesday 18 November: GUI screenshots from a manual check on Windows (#104), PDFs of the SRS, SAD and Test Plan v1.1 with the final deviation log (#96), and both demo videos merged.

## Blockers and resolutions

- The engine MVP from Sprint 1 was late, so everything that needed a running simulator (engine v2, KPIs on real runs, demo scenarios, system tests, reports) moved later. The code freeze moved from 10 November to 16 November, and every report states the commit it was run on (DV-10, DV-11).
- An interim engine v2 was written as a separate function instead of extending the MVP class. It was not merged; the features were rebuilt on the class in #78 (DV-08).
- Shipments (B-26) was not ready when the engine needed it, so the engine computes transport cost itself when a purchase order is placed. The shipments module was merged later with its own tests and is not called by the engine (DV-12).
- Code review found inputs that crashed or were silently accepted in config loading, forecasting and the event log; validation was tightened (DV-07, DV-14, DV-15).
- The system tests (B-33) were not written by the freeze. They were merged on 17 November (DV-17).
- On 17 November the TA confirmed that a GUI is required. The desktop window was added as SCM-F-036 and the SRS, SAD, Test Plan and deviation log were updated the same day (DV-18).
- On one Windows laptop a window test failed once with a Tcl start-up error. It was an environment problem, the test passed on a rerun, and the System Validation Report records it.

## Reassignments

None.

## Review outcome

At the end of the sprint the simulator runs end to end from the command line and from the desktop window, with the sample scenario and three demo scenarios. On `main` there are 430 tests, all passing, with 98% coverage including branches; 7be175a is the last commit that changed code or tests, and later commits only add documents and videos. The unreliable-suppliers scenario is the only one that lowers service level (93.33%), which is the expected effect of late deliveries. The four test reports, the deviation log and the v1.1 documents are in `docs/`.

## Retrospective

- What went well: reviews caught real defects before merge, each merged module has unit tests, every difference from the SRS, SAD and Test Plan is recorded in the deviation log, and the late GUI requirement was added with its tests and documents in one day.
- What did not go well: the sprint plan's dates were not met, mostly because of the late engine, several branches were opened against an outdated `main`, and a lot of work was merged on the last day.
- Actions: tag the final release once `main` is complete, rehearse the demo with each person explaining their own modules, and delete the merged branches.
