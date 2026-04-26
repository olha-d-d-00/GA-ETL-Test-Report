from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re


REQUIRED_CONFIG_KEYS = {
    "project_id",
    "dataset_id",
    "target_table",
    "start_date",
    "end_date",
    "report_spreadsheet_id",
    "report_range",
}

PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
DATASET_OR_TABLE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SOURCE_TABLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_*]+$")


@dataclass(frozen=True)
class ETLConfig:
    project_id: str
    dataset_id: str
    target_table: str
    start_date: date
    end_date: date
    report_spreadsheet_id: str
    report_range: str
    source_table_pattern: str = "bigquery-public-data.google_analytics_sample.ga_sessions_*"

    @property
    def target_table_id(self) -> str:
        return f"{self.project_id}.{self.dataset_id}.{self.target_table}"

    @property
    def start_suffix(self) -> str:
        return self.start_date.strftime("%Y%m%d")

    @property
    def end_suffix(self) -> str:
        return self.end_date.strftime("%Y%m%d")


def parse_config_rows(rows: list[list[str]]) -> ETLConfig:
    """Parse a two-column Google Sheet range into an ETL config."""
    raw_config = _rows_to_dict(rows)
    missing_keys = sorted(REQUIRED_CONFIG_KEYS - raw_config.keys())
    if missing_keys:
        raise ValueError(f"Missing required config keys: {', '.join(missing_keys)}")

    start_date = _parse_date(raw_config["start_date"], "start_date")
    end_date = _parse_date(raw_config["end_date"], "end_date")
    if start_date > end_date:
        raise ValueError("start_date must be earlier than or equal to end_date")

    source_table_pattern = raw_config.get(
        "source_table_pattern",
        "bigquery-public-data.google_analytics_sample.ga_sessions_*",
    )
    _validate_bigquery_identifiers(raw_config, source_table_pattern)

    return ETLConfig(
        project_id=raw_config["project_id"],
        dataset_id=raw_config["dataset_id"],
        target_table=raw_config["target_table"],
        start_date=start_date,
        end_date=end_date,
        report_spreadsheet_id=raw_config["report_spreadsheet_id"],
        report_range=raw_config["report_range"],
        source_table_pattern=source_table_pattern,
    )


def _rows_to_dict(rows: list[list[str]]) -> dict[str, str]:
    config: dict[str, str] = {}
    for row_number, row in enumerate(rows, start=1):
        if not row or not row[0].strip():
            continue
        key = row[0].strip()
        if key.lower() == "key":
            continue
        if len(row) < 2 or not row[1].strip():
            raise ValueError(f"Config key '{key}' has no value in row {row_number}")
        config[key] = row[1].strip()
    return config


def _parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc


def _validate_bigquery_identifiers(raw_config: dict[str, str], source_table_pattern: str) -> None:
    if not PROJECT_ID_PATTERN.fullmatch(raw_config["project_id"]):
        raise ValueError("project_id contains unsupported characters")
    for key in ("dataset_id", "target_table"):
        if not DATASET_OR_TABLE_PATTERN.fullmatch(raw_config[key]):
            raise ValueError(f"{key} must contain only letters, digits and underscores")
    if not SOURCE_TABLE_PATTERN.fullmatch(source_table_pattern):
        raise ValueError("source_table_pattern must look like project.dataset.table_pattern")
