"""Tests for the desktop window itself (SCM-F-036).

They open a real Tk window, so they need a display. CI provides one with
xvfb-run; on a laptop the normal desktop is used. Without a display the tests
are skipped rather than failed.
"""
import csv
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")

from src import gui  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def tk_root():
    """One Tk interpreter for the whole module. Creating a new one per test
    sometimes fails on Windows with "Can't find a usable init.tcl"."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"no display available for Tk: {exc}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def window(tk_root):
    top = tk.Toplevel(tk_root)
    top.withdraw()
    errors = []
    saved = {}
    app = gui.SimulatorApp(
        top,
        root_dir=str(ROOT),
        show_error=lambda title, text: errors.append((title, text)),
        ask_save_path=lambda: saved.get("path"),
    )
    yield app, errors, saved
    top.destroy()


def rows(table):
    return [table.item(item, "values") for item in table.get_children()]


def test_window_runs_scenario_and_fills_tabs(window):
    """TC-GUI-05: choosing a scenario and pressing Run fills the KPI, cost and event tables, draws one chart line per product and enables Save CSV."""
    app, errors, _ = window
    assert str(app.save_button["state"]) == "disabled"
    assert app.scenario_var.get() == gui.gui_model.DEFAULT_CONFIG
    app.scenario_var.set("data/scenarios/unreliable_suppliers.json")
    assert app.run_simulation() is True
    assert errors == []
    kpis = dict(rows(app.kpi_table))
    assert kpis["Service level"] == "93.33%"
    assert dict(rows(app.cost_table))["Total"] == "510,653.10"
    assert dict(rows(app.count_table))["PO_DELAYED"] == "3"
    assert len(rows(app.event_table)) == sum(int(count) for _, count in rows(app.count_table))
    assert {app.chart.gettags(item)[1] for item in app.chart.find_withtag("series")} == {"P-001", "P-002", "P-003"}
    assert str(app.save_button["state"]) == "normal"
    assert app.status_var.get() == "unreliable_suppliers.json: 30 days, 3 products, 90 daily records"
    _, _, service_card = app.cards["Service level"]
    assert service_card.cget("text") == "93.33%"
    assert service_card.cget("background") == gui.LEVEL_COLOURS["warn"][1]
    assert str(app.status_label.cget("style")) == "Ok.Status.TLabel"
    app.event_filter.set("PO_DELAYED")
    app.show_events()
    assert [row[1] for row in rows(app.event_table)] == ["PO_DELAYED"] * 3
    assert all(app.event_table.item(item, "tags") == ("PO_DELAYED",) for item in app.event_table.get_children())
    assert app.kpi_table.item(app.kpi_table.get_children()[1], "tags") == ("odd",)
    app.days_var.set("10")
    assert app.run_simulation() is True
    assert app.status_var.get().endswith("10 days, 3 products, 30 daily records")


def test_window_reports_errors_without_crashing(window, tmp_path):
    """TC-GUI-06: a missing file, broken JSON or a bad day count shows one error message, keeps the window usable, and changes no results."""
    app, errors, _ = window
    app.show_events()
    assert rows(app.event_table) == []
    app.scenario_var.set(str(tmp_path / "missing.json"))
    assert app.run_simulation() is False
    broken = tmp_path / "broken.json"
    broken.write_text('{"simulation":', encoding="utf-8")
    app.scenario_var.set(str(broken))
    assert app.run_simulation() is False
    app.scenario_var.set("data/sample_config.json")
    app.days_var.set("0")
    assert app.run_simulation() is False
    assert len(errors) == 3
    assert all(text.startswith("Error: ") and "\n" not in text for _, text in errors)
    assert "not found" in errors[0][1]
    assert "invalid JSON" in errors[1][1]
    assert "days" in errors[2][1]
    assert app.result is None
    assert str(app.save_button["state"]) == "disabled"
    assert rows(app.kpi_table) == []
    assert app.status_var.get().startswith("Error: ")
    assert str(app.status_label.cget("style")) == "Error.Status.TLabel"
    assert app.cards["Service level"][2].cget("text") == "Not run yet"
    app.days_var.set("")
    assert app.run_simulation() is True


def test_window_saves_csv(window, tmp_path, monkeypatch):
    """TC-GUI-07: Save CSV writes the same day-by-day file as the CLI; cancelling the dialog writes nothing; Browse fills in the chosen file; main() opens the window."""
    app, errors, saved = window
    assert app.save_csv() is None
    app.run_simulation()
    assert app.save_csv() is None
    target = tmp_path / "out" / "gui.csv"
    saved["path"] = str(target)
    assert app.save_csv() == str(target)
    with target.open(encoding="utf-8", newline="") as handle:
        written = list(csv.reader(handle))
    assert written[0] == ["day", "product_id", "demand", "shipped", "stock_end", "backorder", "on_order", "forecast"]
    assert len(written) == 91
    assert app.status_var.get() == f"Results written to {target}"
    saved["path"] = str(tmp_path)
    assert app.save_csv() is None
    assert errors and errors[-1][0] == "Cannot save the CSV"

    chosen = str(ROOT / "data" / "scenarios" / "exp_smoothing.json")
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kwargs: chosen)
    app.browse()
    assert app.scenario_var.get() == chosen
    monkeypatch.setattr(gui.filedialog, "askopenfilename", lambda **kwargs: "")
    app.browse()
    assert app.scenario_var.get() == chosen
    monkeypatch.setattr(gui.filedialog, "asksaveasfilename", lambda **kwargs: "picked.csv")
    assert app._ask_save_path() == "picked.csv"

    opened = []
    monkeypatch.setattr(gui.tk.Tk, "mainloop", lambda self: (opened.append(self.title()), self.destroy()))
    gui.main()
    assert opened == ["Supply Chain Management Simulator"]
