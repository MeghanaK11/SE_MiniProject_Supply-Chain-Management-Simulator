# Supply Chain Management Simulator

A command-line simulator of one warehouse that sells several products to customers and restocks from several suppliers, one day at a time. Each day it receives deliveries, generates customer demand, fills orders oldest first, forecasts demand, and places purchase orders when stock runs low. At the end of a run it prints costs and KPIs and writes a day-by-day CSV.

Software Engineering mini project, PES University.

## Team

| Member | Role |
|---|---|
| Kallepalli Sai Meghana | Repository owner, Scrum Master, Developer |
| D R Rushmitha | QA Lead, Developer |
| Siri Krishna C R | Developer |
| Spoorthi Poornachandra | Developer |
| Shraddha Bamandi | Developer |

## Requirements

- Python 3.12 or newer
- Git
- pip

The simulator uses only the Python standard library. The packages in `requirements.txt` (pytest, pytest-cov, pytest-html) are needed only to run the tests and reports.

## Setup

Clone the repository:

```bash
git clone https://github.com/MeghanaK11/SE_MiniProject_Supply-Chain-Management-Simulator.git
cd SE_MiniProject_Supply-Chain-Management-Simulator
```

Create and activate a virtual environment, then install the dependencies.

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the simulator

```bash
python -m src.main --config data/sample_config.json --days 30 --out output/results.csv
```

All three options are optional:

| Option | Meaning | Default |
|---|---|---|
| `--config` | Scenario file (JSON) | `data/sample_config.json` |
| `--days` | Number of days to simulate | the value in the config |
| `--out` | Where to write the CSV | `output/results.csv` |

So `python -m src.main` on its own runs the sample scenario. The run prints a summary of KPIs and costs, then writes the CSV with one row per product per day: day, product, demand, shipped, stock at end of day, backorder, quantity on order, and forecast.

If the config is missing or invalid, the simulator prints a single line starting with `Error:` and exits with code 2.

## Demo scenarios

Each file in `data/scenarios/` changes one thing from `data/sample_config.json`:

```bash
python -m src.main --config data/scenarios/high_demand.json
python -m src.main --config data/scenarios/unreliable_suppliers.json
python -m src.main --config data/scenarios/exp_smoothing.json
```

Results on `main` at commit `39db368`, 30 days, seed 42:

| Scenario | What changes | Fill rate | Service level | Total cost (Rs) |
|---|---|---:|---:|---:|
| sample_config.json (baseline) | Nothing | 100.00% | 100.00% | 507,543.50 |
| high_demand.json | P-001 base demand 20 to 40 | 100.00% | 100.00% | 585,220.50 |
| unreliable_suppliers.json | Every supplier reliability 0.5 | 100.00% | 93.33% | 510,653.10 |
| exp_smoothing.json | Exponential smoothing, alpha 0.5 | 100.00% | 100.00% | 521,369.50 |

Unreliable suppliers is the only scenario that lowers service level: three deliveries arrive late and cause backorders. The other two show their effect in total cost.

## Running the tests
Run unit tests:

```bash
python -m pytest -m "not system and not nfr"
```

Run system tests:

```bash
python -m pytest -m system
```

Run NFR tests:

```bash
python -m pytest -m nfr
```

Run all tests:

```bash
python -m pytest
```<img width="1431" height="185" alt="image" src="https://github.com/user-attachments/assets/e1acb2d6-d18d-4397-b40d-db15f4242d9f" />

## Documentation

Design documents in `docs/`:

| Document | Files |
|---|---|
| Software Requirements Specification | `SRS_v1.0.docx`, `SRS_v1.0.pdf` (submitted), `SRS_v1.1.docx` (updated to match the build) |
| Software Architecture and Design | `SAD_v1.0.docx`, `SAD_v1.0.pdf` (submitted), `SAD_v1.1.docx` (updated to match the build) |
| Software Test Plan | `Test_Plan_v1.0.docx`, `Test_Plan_v1.0.pdf` (submitted), `Test_Plan_v1.1.docx` (updated to match the tests) |
| Deviation Log | `Deviation_Log.md`: every difference between the documents and the build, and why |

Reports in `docs/reports/`, each with its raw output in a subfolder:

| Report | PDF | Raw output |
|---|---|---|
| Unit Test Report | `Unit_Test_Report.pdf` | `unit/` (JUnit XML and HTML) |
| Code Coverage Report | `Code_Coverage_Report.pdf` | `coverage/line/index.html` |
| Branch Coverage Report | `Branch_Coverage_Report.pdf` | `coverage/branch/index.html` |

## Workflow

Every backlog item is built on its own branch and submitted as a pull request. CI must pass and another team member must approve before the repository owner squash merges it into `main`. Direct pushes to `main` are blocked by a branch ruleset.

## Project board

Backlog, story points, sprints and assignments: [project board](https://github.com/MeghanaK11/SE_MiniProject_Supply-Chain-Management-Simulator/projects)
