"""Non-functional requirement tests (SCM-NF-001, SCM-NF-002, SCM-NF-005).

Every test here is marked nfr, so the Unit Test Report run
(pytest -m "not system and not nfr") leaves them out.
"""
import ast
import sys
import time
from pathlib import Path

import pytest

from src.config_loader import load_config
from src.main import main
from src.simulation import SupplyChainSimulation

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CONFIG = ROOT / "data" / "sample_config.json"
SRC_DIR = ROOT / "src"


@pytest.mark.nfr
def test_nfr_performance_365_days():
    """TC-NFR-01 (SCM-NF-001): 365 days on the sample config finish in under 2.0 seconds."""
    config = load_config(str(SAMPLE_CONFIG))
    start = time.perf_counter()
    result = SupplyChainSimulation(config, days=365).run()
    elapsed = time.perf_counter() - start
    assert len(result.daily_records) == 365 * len(config["products"])
    assert elapsed < 2.0, f"365-day run took {elapsed:.3f} s; the limit is 2.0 s"


@pytest.mark.nfr
def test_nfr_repeatable_csv(tmp_path):
    """TC-NFR-02 (SCM-NF-002): two CLI runs with the same config and seed write byte-identical CSVs."""
    first = tmp_path / "run1.csv"
    second = tmp_path / "run2.csv"
    assert main(["--config", str(SAMPLE_CONFIG), "--out", str(first)]) == 0
    assert main(["--config", str(SAMPLE_CONFIG), "--out", str(second)]) == 0
    first_bytes = first.read_bytes()
    assert first_bytes, "the CSV file is empty"
    assert first_bytes == second.read_bytes()


@pytest.mark.nfr
def test_nfr_standard_library_only():
    """TC-NFR-03 (SCM-NF-005): every module imported by src/ is src itself or in the standard library."""
    source_files = sorted(SRC_DIR.glob("*.py"))
    assert source_files, "no Python files found in src/"
    outside = []
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top != "src" and top not in sys.stdlib_module_names:
                    outside.append(f"{path.name}: {name}")
    assert outside == [], f"non-standard-library imports found: {outside}"
