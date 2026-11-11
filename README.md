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
| Spoorthi Poomachandra | Developer |
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

Run all tests:

```bash
python -m pytest -v
```

Unit tests, system tests and non-functional requirement (NFR) tests are included in the test suite.

## Demo Scenarios

The demo scenario files are available in:

```text
data/scenarios/
```

Use the available scenario configurations to demonstrate different simulator behaviours.

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
