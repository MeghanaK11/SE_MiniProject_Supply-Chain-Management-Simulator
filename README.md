# Supply Chain Management Simulator

## Project Description

The Supply Chain Management Simulator is a command-line application that simulates one warehouse selling several products to customers and restocking from multiple suppliers. Each day, it receives deliveries, generates customer demand, fulfils orders oldest first, forecasts demand, and places purchase orders when stock runs low. It also reports costs and KPIs and generates daily CSV reports.

This is a Software Engineering mini project.

## Team

| Member | Role |
|---|---|
| Kallepalli Sai Meghana | Repository owner, Scrum Master |
| D R Rushmitha | QA Lead, Developer |
| Siri Krishna C R | Developer |
| Spoorthi Poornachandra | Developer |
| Shraddha | Developer |

## Requirements

- Python 3.12
- Git
- pip

## Setup Instructions

Clone the repository:

```bash
git clone https://github.com/MeghanaK11/SE_MiniProject_Supply-Chain-Management-Simulator.git
cd SE_MiniProject_Supply-Chain-Management-Simulator
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Simulator

Run the simulator for 30 days:

```bash
python -m src.main --days 30
```

## Running Tests


Run unit tests:

```bash
python -m pytest -m "not system and not nfr"
```

Run system tests:

```bash
python -m pytest -m system
```

Run non-functional requirement (NFR) tests:

```bash
python -m pytest -m nfr
```


## Demo Scenarios


The demo scenario files are available in `data/scenarios/`.

Run each scenario using:

```bash
python -m src.main --config data/scenarios/sample_config.json
python -m src.main --config data/scenarios/high_demand.json
python -m src.main --config data/scenarios/unreliable_suppliers.json
python -m src.main --config data/scenarios/exp_smoothing.json
```

### Scenario Results

Results on `main` at commit `39db368`, 30 days, seed 42.

| Scenario | What changes | Fill rate | Service level | Total cost (Rs) |
|---|---|---:|---:|---:|
| sample_config.json (baseline) | Nothing | 100.00% | 100.00% | 507,543.50 |
| high_demand.json | P-001 base demand 20 to 40 | 100.00% | 100.00% | 585,220.50 |
| unreliable_suppliers.json | Every supplier reliability 0.5 | 100.00% | 93.33% | 510,653.10 |
| exp_smoothing.json | Exponential smoothing, alpha 0.5 | 100.00% | 100.00% | 521,369.50 |

Unreliable suppliers is the only scenario that lowers service level (three delayed deliveries). The other two show their effect in total cost.



## Project Documentation

- Software Requirements Specification (SRS): `docs/`
- Software Architecture and Design (SAD): `docs/`
- Software Test Plan: `docs/`
- Reports: `docs/reports/`
- Sprint notes: `docs/sprints/`
- Demo videos: `docs/videos/`

## Workflow

Every feature is developed on its own branch, tested, submitted through a pull request, checked by CI, and reviewed before merging into the main branch.

Direct pushes to the main branch are blocked.

## Project Board

See the GitHub project board for task assignments and progress.
