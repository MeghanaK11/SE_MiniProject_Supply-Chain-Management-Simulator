"""Desktop window for the supply chain simulator (SCM-F-036).

Run with: python -m src.gui

The window lets a user pick a scenario file, optionally change the number of
days, run the simulation, read the KPIs, costs and events, see end-of-day stock
per product on a chart, and save the day-by-day CSV. It uses tkinter, which is
part of the Python standard library (SCM-NF-005). All calculations live in
src/gui_model.py; this module only builds widgets and calls those functions.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from src import gui_model
from src.clock import EVENT_TYPES
from src.reports import export_daily_csv

CHART_WIDTH = 860
CHART_HEIGHT = 400
CHART_MARGIN = 56

# Colours. Slate for text and frames, blue for actions, and green, amber and
# red only where they carry meaning (headline cards and event rows).
BG = "#eef2f7"
SURFACE = "#ffffff"
HEADER = "#1e293b"
HEADER_TEXT = "#f8fafc"
HEADER_SUB = "#94a3b8"
TEXT = "#0f172a"
MUTED = "#64748b"
BORDER = "#d8dee8"
STRIPE = "#f6f8fb"
ACCENT = "#2563eb"
ACCENT_DARK = "#1d4ed8"
GRID = "#e5e9f0"
LEVEL_COLOURS = {
    "good": ("#166534", "#dcfce7"),
    "warn": ("#92400e", "#fef3c7"),
    "bad": ("#991b1b", "#fee2e2"),
    "neutral": ("#1e3a8a", "#e0e7ff"),
    "empty": (MUTED, "#f1f5f9"),
}
EVENT_ROW_COLOURS = {
    "STOCKOUT": "#fee2e2",
    "PO_DELAYED": "#fef3c7",
    "PO_RECEIVED": "#dcfce7",
    "PO_PLACED": "#e0e7ff",
}
LINE_COLOURS = ("#2563eb", "#ea580c", "#0d9488", "#9333ea", "#db2777", "#65a30d")


def _one_line(message) -> str:
    return " ".join(str(message).split())


def _base_family(root) -> str:
    for family in ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans"):
        if family in tkfont.families(root):
            return family
    return tkfont.nametofont("TkDefaultFont").actual("family")


class SimulatorApp(ttk.Frame):
    """The main window: a header, inputs, a status line and three result tabs."""

    def __init__(self, master, root_dir: str = ".", show_error=None, ask_save_path=None):
        self._setup_style(master)
        super().__init__(master, style="App.TFrame")
        self.root_dir = root_dir
        self.show_error = show_error or (lambda title, text: messagebox.showerror(title, text, parent=master))
        self.ask_save_path = ask_save_path or self._ask_save_path
        self.result = None
        self.config_path = None

        master.title("Supply Chain Management Simulator")
        master.configure(background=BG)
        master.minsize(980, 640)
        self.grid(row=0, column=0, sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_inputs()
        self._build_tabs()

    # ----- style --------------------------------------------------------

    def _setup_style(self, master):
        family = _base_family(master)
        self.fonts = {
            "body": (family, 10),
            "bold": (family, 10, "bold"),
            "small": (family, 9),
            "title": (family, 17, "bold"),
            "card": (family, 18, "bold"),
        }
        for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont"):
            tkfont.nametofont(name).configure(family=family, size=10)

        style = ttk.Style(master)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=TEXT, font=self.fonts["body"])
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background=SURFACE)
        style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
        style.configure("Hint.TLabel", background=SURFACE, foreground=MUTED, font=self.fonts["small"])
        style.configure("Field.TLabel", background=SURFACE, foreground=TEXT, font=self.fonts["bold"])
        for name, colour in (("Status.TLabel", MUTED), ("Ok.Status.TLabel", LEVEL_COLOURS["good"][0]),
                             ("Error.Status.TLabel", LEVEL_COLOURS["bad"][0])):
            style.configure(name, background=BG, foreground=colour, font=self.fonts["bold"])

        style.configure("TEntry", fieldbackground=SURFACE, bordercolor=BORDER, lightcolor=BORDER, padding=5)
        style.configure("TCombobox", fieldbackground=SURFACE, bordercolor=BORDER, lightcolor=BORDER, padding=4,
                        arrowcolor=MUTED)
        style.map("TCombobox", fieldbackground=[("readonly", SURFACE)])

        style.configure("TButton", background=SURFACE, foreground=TEXT, bordercolor=BORDER, lightcolor=SURFACE,
                        darkcolor=SURFACE, padding=(12, 6), focuscolor=SURFACE)
        style.map("TButton", background=[("disabled", "#f1f5f9"), ("active", "#e8edf5")],
                  foreground=[("disabled", "#a0aab8")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", bordercolor=ACCENT,
                        lightcolor=ACCENT, darkcolor=ACCENT, font=self.fonts["bold"], focuscolor=ACCENT)
        style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])

        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(0, 4, 0, 0))
        style.configure("TNotebook.Tab", background="#dfe5ee", foreground=MUTED, padding=(16, 7),
                        font=self.fonts["bold"], bordercolor=BORDER)
        style.map("TNotebook.Tab", background=[("selected", SURFACE)], foreground=[("selected", ACCENT)])

        style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT, rowheight=26,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.configure("Treeview.Heading", background="#e8edf5", foreground=HEADER, font=self.fonts["bold"],
                        bordercolor=BORDER, relief="flat", padding=(6, 5))
        style.map("Treeview", background=[("selected", "#bfdbfe")], foreground=[("selected", TEXT)])
        style.map("Treeview.Heading", background=[("active", "#dbe3ef")])
        style.configure("Box.TLabelframe", background=SURFACE, bordercolor=BORDER)
        style.configure("Box.TLabelframe.Label", background=SURFACE, foreground=HEADER, font=self.fonts["bold"])

    # ----- layout -------------------------------------------------------

    def _build_header(self):
        header = tk.Frame(self, background=HEADER, padx=20, pady=14)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(header, text="Supply Chain Management Simulator", background=HEADER, foreground=HEADER_TEXT,
                 font=self.fonts["title"]).grid(row=0, column=0, sticky="w")
        tk.Label(header, text="One warehouse, several products and suppliers, simulated one day at a time",
                 background=HEADER, foreground=HEADER_SUB, font=self.fonts["body"]).grid(row=1, column=0, sticky="w")

    def _build_inputs(self):
        bar = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(14, 0))

        ttk.Label(bar, text="Scenario", style="Field.TLabel").grid(row=0, column=0, padx=(0, 8))
        scenarios = gui_model.list_scenarios(self.root_dir)
        self.scenario_var = tk.StringVar(value=scenarios[0] if scenarios else gui_model.DEFAULT_CONFIG)
        self.scenario_box = ttk.Combobox(bar, textvariable=self.scenario_var, values=scenarios, width=36)
        self.scenario_box.grid(row=0, column=1, sticky="ew")
        ttk.Button(bar, text="Browse...", command=self.browse).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(bar, text="Days", style="Field.TLabel").grid(row=0, column=3, padx=(20, 8))
        self.days_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.days_var, width=7).grid(row=0, column=4)
        ttk.Label(bar, text="blank = config", style="Hint.TLabel").grid(row=0, column=5, padx=(6, 20))

        self.run_button = ttk.Button(bar, text="Run simulation", style="Accent.TButton", command=self.run_simulation)
        self.run_button.grid(row=0, column=6)
        self.save_button = ttk.Button(bar, text="Save CSV...", command=self.save_csv, state="disabled")
        self.save_button.grid(row=0, column=7, padx=(8, 0))
        bar.columnconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Choose a scenario and press Run simulation.")
        self.status_label = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=2, column=0, sticky="w", padx=18, pady=(10, 2))

    def _build_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self.rowconfigure(3, weight=1)

        summary = ttk.Frame(self.tabs, style="Card.TFrame", padding=14)
        self.tabs.add(summary, text="Summary")
        summary.columnconfigure(0, weight=1)
        self._build_cards(summary)
        tables = ttk.Frame(summary, style="Card.TFrame")
        tables.grid(row=1, column=0, sticky="nw", pady=(14, 0))
        self.kpi_table = self._table(tables, ("KPI", "Value"), (230, 110), 0, "Key performance indicators")
        self.cost_table = self._table(tables, ("Cost", "Rs"), (130, 130), 1, "Costs")
        self.count_table = self._table(tables, ("Event", "Count"), (130, 70), 2, "Events")

        chart_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=10)
        self.tabs.add(chart_tab, text="Stock chart")
        self.chart = tk.Canvas(chart_tab, width=CHART_WIDTH, height=CHART_HEIGHT, background=SURFACE,
                               highlightthickness=0)
        self.chart.grid(row=0, column=0, sticky="nsew")
        chart_tab.columnconfigure(0, weight=1)
        chart_tab.rowconfigure(0, weight=1)
        self.chart.bind("<Configure>", lambda _event: self.result is not None and self.draw_chart())
        self.chart.create_text(CHART_WIDTH / 2, CHART_HEIGHT / 2, text="Run a scenario to see stock per product.",
                               fill=MUTED, font=self.fonts["body"])

        events_tab = ttk.Frame(self.tabs, style="Card.TFrame", padding=14)
        self.tabs.add(events_tab, text="Events")
        ttk.Label(events_tab, text="Show", style="Field.TLabel").grid(row=0, column=0, sticky="w")
        self.event_filter = tk.StringVar(value=gui_model.ALL_EVENTS)
        filter_box = ttk.Combobox(events_tab, textvariable=self.event_filter, state="readonly",
                                  values=(gui_model.ALL_EVENTS,) + EVENT_TYPES, width=18)
        filter_box.grid(row=0, column=1, sticky="w", padx=8)
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.show_events())
        legend = ttk.Frame(events_tab, style="Card.TFrame")
        legend.grid(row=0, column=2, sticky="e")
        for index, (event_type, colour) in enumerate(EVENT_ROW_COLOURS.items()):
            tk.Label(legend, text=event_type, background=colour, foreground=TEXT, font=self.fonts["small"],
                     padx=8, pady=2).grid(row=0, column=index, padx=(6, 0))
        self.event_table = ttk.Treeview(events_tab, columns=("day", "type", "message"), show="headings", height=14)
        for column, heading, width, stretch in (("day", "Day", 60, False), ("type", "Type", 130, False),
                                                ("message", "Message", 600, True)):
            self.event_table.heading(column, text=heading, anchor="w")
            self.event_table.column(column, width=width, anchor="w", stretch=stretch)
        self._add_row_tags(self.event_table)
        for event_type, colour in EVENT_ROW_COLOURS.items():
            self.event_table.tag_configure(event_type, background=colour)
        scroll = ttk.Scrollbar(events_tab, orient="vertical", command=self.event_table.yview)
        self.event_table.configure(yscrollcommand=scroll.set)
        self.event_table.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        scroll.grid(row=1, column=3, sticky="ns", pady=(10, 0))
        events_tab.columnconfigure(2, weight=1)
        events_tab.rowconfigure(1, weight=1)

    def _build_cards(self, parent):
        row = ttk.Frame(parent, style="Card.TFrame")
        row.grid(row=0, column=0, sticky="ew")
        self.cards = {}
        for index, (title, _key) in enumerate(gui_model.CARD_ROWS):
            fg, bg = LEVEL_COLOURS["empty"]
            card = tk.Frame(row, background=bg, padx=14, pady=10)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 10, 0))
            row.columnconfigure(index, weight=1, uniform="card")
            title_label = tk.Label(card, text=title, background=bg, foreground=fg, font=self.fonts["small"])
            title_label.grid(row=0, column=0, sticky="w")
            value_label = tk.Label(card, text="Not run yet", background=bg, foreground=fg, font=self.fonts["card"])
            value_label.grid(row=1, column=0, sticky="w")
            self.cards[title] = (card, title_label, value_label)

    def _table(self, parent, headings, widths, column, title):
        box = ttk.LabelFrame(parent, text=title, padding=8, style="Box.TLabelframe")
        box.grid(row=0, column=column, sticky="nw", padx=(0, 12))
        table = ttk.Treeview(box, columns=headings, show="headings", height=7)
        for heading, width in zip(headings, widths):
            anchor = "w" if heading == headings[0] else "e"
            table.heading(heading, text=heading, anchor=anchor)
            table.column(heading, width=width, anchor=anchor)
        self._add_row_tags(table)
        table.grid(row=0, column=0)
        return table

    @staticmethod
    def _add_row_tags(table):
        table.tag_configure("even", background=SURFACE)
        table.tag_configure("odd", background=STRIPE)

    # ----- actions ------------------------------------------------------

    def browse(self):
        path = filedialog.askopenfilename(parent=self.master, title="Choose a scenario file",
                                          initialdir=os.path.join(self.root_dir, "data"),
                                          filetypes=(("Scenario files", "*.json"), ("All files", "*.*")))
        if path:
            self.scenario_var.set(path)

    def run_simulation(self) -> bool:
        """Run the chosen scenario and fill every tab. Returns True on success."""
        path = self.scenario_var.get().strip()
        try:
            days = gui_model.parse_days(self.days_var.get())
            full_path = path if os.path.isabs(path) else os.path.join(self.root_dir, path)
            result = gui_model.run_scenario(full_path, days)
        except (FileNotFoundError, ValueError) as exc:
            self.show_error("Cannot run the simulation", f"Error: {_one_line(exc)}")
            self.status_var.set(f"Error: {_one_line(exc)}")
            self.status_label.configure(style="Error.Status.TLabel")
            return False
        self.result = result
        self.config_path = path
        self._fill_cards(gui_model.summary_cards(result))
        self._fill(self.kpi_table, gui_model.kpi_rows(result.kpis))
        self._fill(self.cost_table, gui_model.cost_rows(result.costs))
        self._fill(self.count_table, gui_model.event_counts(result.events))
        self.show_events()
        self.draw_chart()
        self.save_button.configure(state="normal")
        self.status_var.set(gui_model.run_summary(path, result))
        self.status_label.configure(style="Ok.Status.TLabel")
        return True

    def _fill_cards(self, cards):
        for title, text, level in cards:
            fg, bg = LEVEL_COLOURS[level]
            frame, title_label, value_label = self.cards[title]
            frame.configure(background=bg)
            title_label.configure(background=bg, foreground=fg)
            value_label.configure(text=text, background=bg, foreground=fg)

    def show_events(self):
        if self.result is None:
            return
        rows = gui_model.event_rows(self.result.events, self.event_filter.get())
        self._fill(self.event_table, rows, tag_column=1)

    def draw_chart(self):
        """End-of-day stock per product, one coloured line each, with gridlines and a legend."""
        canvas = self.chart
        canvas.delete("all")
        series = gui_model.stock_series(self.result.daily_records)
        # Fill the canvas once it is on screen; use the default size before that.
        width = max(canvas.winfo_width(), CHART_WIDTH)
        height = max(canvas.winfo_height(), CHART_HEIGHT)
        points = gui_model.chart_points(series, width, height, CHART_MARGIN)
        left, right = CHART_MARGIN, width - CHART_MARGIN
        top, bottom = CHART_MARGIN, height - CHART_MARGIN
        highest = max((max(values) for values in series.values() if values), default=0)
        for fraction in (0, 0.25, 0.5, 0.75, 1):
            y = bottom - fraction * (bottom - top)
            canvas.create_line(left, y, right, y, fill=GRID if fraction else BORDER)
            canvas.create_text(left - 8, y, text=str(round(highest * fraction)), anchor="e", fill=MUTED,
                               font=self.fonts["small"])
        days = max((len(values) for values in series.values()), default=0)
        step = 5 if days > 10 else 1
        for day in range(0, days, step):
            x = left + (day * (right - left) / (days - 1) if days > 1 else 0)
            canvas.create_line(x, bottom, x, bottom + 4, fill=BORDER)
            canvas.create_text(x, bottom + 14, text=str(day), fill=MUTED, font=self.fonts["small"])
        canvas.create_text((left + right) / 2, height - 14, text="Day", fill=MUTED, font=self.fonts["small"])
        canvas.create_text(left, top - 24, text="Stock at end of day (units)", anchor="w", fill=HEADER,
                           font=self.fonts["bold"])
        for index, (product_id, line) in enumerate(sorted(points.items())):
            colour = LINE_COLOURS[index % len(LINE_COLOURS)]
            if len(line) > 1:
                canvas.create_line(*[coord for point in line for coord in point], fill=colour, width=2.5,
                                   capstyle="round", joinstyle="round", tags=("series", product_id))
            legend_x = right - (len(points) - index) * 92
            legend_y = top - 24
            canvas.create_line(legend_x, legend_y, legend_x + 20, legend_y, fill=colour, width=4, capstyle="round")
            canvas.create_text(legend_x + 26, legend_y, text=product_id, anchor="w", fill=TEXT,
                               font=self.fonts["body"])

    def save_csv(self) -> str | None:
        """Ask where to save and write the day-by-day CSV. Returns the path, or None."""
        if self.result is None:
            return None
        path = self.ask_save_path()
        if not path:
            return None
        try:
            export_daily_csv(self.result.daily_records, path)
        except (OSError, ValueError) as exc:
            self.show_error("Cannot save the CSV", f"Error: {_one_line(exc)}")
            return None
        self.status_var.set(f"Results written to {path}")
        self.status_label.configure(style="Ok.Status.TLabel")
        return path

    def _ask_save_path(self):
        return filedialog.asksaveasfilename(parent=self.master, title="Save results as CSV",
                                            defaultextension=".csv", initialfile="results.csv",
                                            filetypes=(("CSV files", "*.csv"),))

    @staticmethod
    def _fill(table, rows, tag_column=None):
        """Replace a table's rows, striping them; event rows are coloured by type."""
        table.delete(*table.get_children())
        for index, row in enumerate(rows):
            tags = ("odd" if index % 2 else "even",)
            if tag_column is not None and row[tag_column] in EVENT_ROW_COLOURS:
                tags = (row[tag_column],)
            table.insert("", "end", values=row, tags=tags)


def main() -> None:
    """Open the window and wait for the user."""
    root = tk.Tk()
    SimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
