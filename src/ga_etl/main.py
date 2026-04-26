from __future__ import annotations

import argparse
import os

from ga_etl.bigquery_etl import BigQueryGAETL
from ga_etl.config import parse_config_rows
from ga_etl.sheets import GoogleSheetsClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GA sample ETL from Google Sheets config.")
    parser.add_argument(
        "--credentials",
        default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        help="Path to service account JSON. Defaults to GOOGLE_APPLICATION_CREDENTIALS.",
    )
    parser.add_argument(
        "--config-spreadsheet-id",
        default=os.getenv("CONFIG_SPREADSHEET_ID"),
        help="Google Sheet ID with ETL config.",
    )
    parser.add_argument(
        "--config-range",
        default=os.getenv("CONFIG_RANGE", "config!A:B"),
        help="Range with key/value config rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.credentials:
        raise SystemExit("Missing --credentials or GOOGLE_APPLICATION_CREDENTIALS.")
    if not args.config_spreadsheet_id:
        raise SystemExit("Missing --config-spreadsheet-id or CONFIG_SPREADSHEET_ID.")

    sheets = GoogleSheetsClient(args.credentials)
    config_rows = sheets.read_values(args.config_spreadsheet_id, args.config_range)
    config = parse_config_rows(config_rows)

    etl = BigQueryGAETL(config.project_id, args.credentials)
    report = etl.run(config)
    sheets.write_values(config.report_spreadsheet_id, config.report_range, report)

    print(
        "ETL finished: "
        f"{config.start_date.isoformat()}..{config.end_date.isoformat()} -> "
        f"{config.target_table_id}; report rows: {max(len(report) - 3, 0)}"
    )


if __name__ == "__main__":
    main()

