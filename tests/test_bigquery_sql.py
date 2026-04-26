from datetime import date

from ga_etl.config import ETLConfig


def test_config_suffixes_are_bigquery_table_suffixes() -> None:
    config = ETLConfig(
        project_id="demo-project",
        dataset_id="marketing_analytics",
        target_table="ga_sessions_daily",
        start_date=date(2017, 8, 1),
        end_date=date(2017, 8, 7),
        report_spreadsheet_id="sheet-id",
        report_range="report!A1",
    )

    assert config.start_suffix == "20170801"
    assert config.end_suffix == "20170807"

