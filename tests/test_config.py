from datetime import date

import pytest

from ga_etl.config import parse_config_rows


VALID_ROWS = [
    ["key", "value"],
    ["project_id", "demo-project"],
    ["dataset_id", "marketing_analytics"],
    ["target_table", "ga_sessions_daily"],
    ["start_date", "2017-08-01"],
    ["end_date", "2017-08-07"],
    ["report_spreadsheet_id", "sheet-id"],
    ["report_range", "report!A1"],
]


def test_parse_config_rows_returns_valid_config() -> None:
    config = parse_config_rows(VALID_ROWS)

    assert config.project_id == "demo-project"
    assert config.start_date == date(2017, 8, 1)
    assert config.end_suffix == "20170807"
    assert config.target_table_id == "demo-project.marketing_analytics.ga_sessions_daily"


def test_parse_config_rows_rejects_missing_required_key() -> None:
    rows = [row for row in VALID_ROWS if row[0] != "dataset_id"]

    with pytest.raises(ValueError, match="dataset_id"):
        parse_config_rows(rows)


def test_parse_config_rows_rejects_invalid_date_order() -> None:
    rows = [row[:] for row in VALID_ROWS]
    rows[4][1] = "2017-08-10"

    with pytest.raises(ValueError, match="start_date"):
        parse_config_rows(rows)


def test_parse_config_rows_rejects_empty_value() -> None:
    rows = [row[:] for row in VALID_ROWS]
    rows[2][1] = ""

    with pytest.raises(ValueError, match="has no value"):
        parse_config_rows(rows)


def test_parse_config_rows_rejects_unsafe_target_table() -> None:
    rows = [row[:] for row in VALID_ROWS]
    rows[3][1] = "ga_sessions_daily; DROP TABLE"

    with pytest.raises(ValueError, match="target_table"):
        parse_config_rows(rows)
