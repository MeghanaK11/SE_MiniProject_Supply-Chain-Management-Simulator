"""Command-line interface for the supply chain simulator (SCM-F-035, SCM-NF-004).

Usage: python -m src.main [--config PATH] [--days N] [--out PATH]

Exit codes: 0 success, 2 invalid input (missing file, bad config or value),
1 unexpected failure. Errors are one line on stderr starting with "Error:".
"""
import argparse
import sys

from src.config_loader import load_config, validate_config
from src.reports import export_daily_csv, format_summary
from src.simulation import SupplyChainSimulation

DEFAULT_CONFIG = "data/sample_config.json"
DEFAULT_OUT = "output/results.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Run a supply chain scenario day by day, print a summary and write a CSV.",
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="path to the scenario JSON file (default: %(default)s)")
    parser.add_argument("--days", type=int, default=None,
                        help="number of days to simulate (default: the value in the config)")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="path of the CSV file to write (default: %(default)s)")
    return parser


def _one_line(message) -> str:
    """Collapse a message to a single line."""
    return " ".join(str(message).split())


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        if args.days is not None:
            config["simulation"]["days"] = args.days
            validate_config(config)
        result = SupplyChainSimulation(config).run()
        export_daily_csv(result.daily_records, args.out)
        print(format_summary(result.kpis, result.costs))
        print(f"Results written to {args.out}")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {_one_line(exc)}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Error: unexpected failure: {_one_line(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())