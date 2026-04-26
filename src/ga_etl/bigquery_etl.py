from __future__ import annotations

from datetime import date, datetime, timezone
from time import sleep
from typing import Any

from google.api_core import exceptions
from google.cloud import bigquery
from google.oauth2 import service_account

from ga_etl.config import ETLConfig


REPORT_HEADERS = [
    "session_date",
    "channel_grouping",
    "device_category",
    "sessions",
    "pageviews",
    "transactions",
    "revenue",
]

RETRYABLE_BIGQUERY_ERRORS = (
    exceptions.BadGateway,
    exceptions.GatewayTimeout,
    exceptions.InternalServerError,
    exceptions.ServiceUnavailable,
    exceptions.TooManyRequests,
)


class BigQueryGAETL:
    def __init__(self, project_id: str, credentials_path: str) -> None:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        self.client = bigquery.Client(project=project_id, credentials=credentials)

    def run(self, config: ETLConfig) -> list[list[object]]:
        self._ensure_dataset(config)
        self._load_target_table(config)
        return self.build_report(config)

    def _ensure_dataset(self, config: ETLConfig) -> None:
        dataset_id = f"{config.project_id}.{config.dataset_id}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        try:
            self.client.create_dataset(dataset, exists_ok=True)
        except exceptions.Forbidden as exc:
            raise RuntimeError(
                f"Cannot create or access dataset '{dataset_id}'. Check service account permissions."
            ) from exc

    def _load_target_table(self, config: ETLConfig) -> None:
        query = f"""
            SELECT
                PARSE_DATE('%Y%m%d', date) AS session_date,
                COALESCE(channelGrouping, 'unknown') AS channel_grouping,
                COALESCE(device.deviceCategory, 'unknown') AS device_category,
                COUNT(DISTINCT CONCAT(fullVisitorId, '-', CAST(visitId AS STRING))) AS sessions,
                COALESCE(SUM(totals.pageviews), 0) AS pageviews,
                COALESCE(SUM(totals.transactions), 0) AS transactions,
                COALESCE(SUM(totals.transactionRevenue), 0) / 1000000 AS revenue,
                CURRENT_TIMESTAMP() AS loaded_at
            FROM `{config.source_table_pattern}`
            WHERE _TABLE_SUFFIX BETWEEN @start_suffix AND @end_suffix
            GROUP BY session_date, channel_grouping, device_category
        """
        job_config = bigquery.QueryJobConfig(
            destination=config.target_table_id,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            query_parameters=[
                bigquery.ScalarQueryParameter("start_suffix", "STRING", config.start_suffix),
                bigquery.ScalarQueryParameter("end_suffix", "STRING", config.end_suffix),
            ],
        )
        self.client.delete_table(config.target_table_id, not_found_ok=True)
        job = self.client.query(query, job_config=job_config)
        self._wait_for_job(job, "Load target table")
        target_rows = self._count_rows(config.target_table_id)
        print(f"Loaded {target_rows} aggregated rows into target table {config.target_table_id}.")

    def build_report(self, config: ETLConfig) -> list[list[object]]:
        query = f"""
            SELECT
                session_date,
                channel_grouping,
                device_category,
                sessions,
                pageviews,
                transactions,
                ROUND(revenue, 2) AS revenue
            FROM `{config.target_table_id}`
            WHERE session_date BETWEEN @start_date AND @end_date
            ORDER BY session_date, channel_grouping, device_category
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", config.start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", config.end_date),
            ],
        )
        job = self.client.query(query, job_config=job_config)
        rows = self._wait_for_job(job, "Build report")
        report: list[list[object]] = [
            ["generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds")],
            [],
            REPORT_HEADERS,
        ]
        report.extend([[self._format_sheet_value(value) for value in row.values()] for row in rows])
        return report

    def _format_sheet_value(self, value: object) -> object:
        if isinstance(value, datetime):
            return value.isoformat(timespec="seconds")
        if isinstance(value, date):
            return value.isoformat()
        return value

    def _count_rows(self, table_id: str) -> int:
        query = f"SELECT COUNT(*) AS row_count FROM `{table_id}`"
        rows = self.client.query(query).result()
        return next(iter(rows))["row_count"]

    def _wait_for_job(self, job: Any, operation_name: str, max_attempts: int = 3) -> Any:
        for attempt in range(1, max_attempts + 1):
            try:
                return job.result()
            except RETRYABLE_BIGQUERY_ERRORS as exc:
                if attempt == max_attempts:
                    raise RuntimeError(
                        f"{operation_name} failed after {max_attempts} attempts."
                    ) from exc
                sleep(2 ** (attempt - 1))
        raise RuntimeError(f"{operation_name} failed unexpectedly.")
