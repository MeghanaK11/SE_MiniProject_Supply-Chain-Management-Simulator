# Supply Chain Management Simulator

A command-line simulator of one warehouse that sells several products to customers and restocks from several suppliers, one day at a time. Each day it receives deliveries, generates customer demand, fills orders oldest first, forecasts demand, and places purchase orders when stock runs low. At the end it reports costs and KPIs and writes a day-by-day CSV.

Software Engineering mini project.

## Team

| Member | Role |
|---|---|
| Kallepalli Sai Meghana | Repository owner, scrum master |
| D R Rushmitha | QA lead, developer |
| Siri Krishna C R | Developer |
| Spoorthi Poornachandra | Developer |
| Shraddha | Developer |

## Setup

Requires Python 3.12.

```
git clone https://github.com/MeghanaK11/SE_MiniProject_Supply-Chain-Management-Simulator.git
cd SE_MiniProject_Supply-Chain-Management-Simulator
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Run the tests

```
python -m pytest -v
```

## Workflow

Every feature is built on its own branch with its tests, opened as a pull request, checked by CI, and reviewed and merged by the repository owner. Direct pushes to main are blocked.
