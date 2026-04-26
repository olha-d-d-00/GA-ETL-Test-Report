# GA Sample ETL

Small ETL pipeline for a Junior Python Backend / Data Analyst test task.

The project:

- reads run parameters from Google Sheets;
- queries `bigquery-public-data.google_analytics_sample.ga_sessions_*`;
- stores aggregated daily data in a BigQuery table in the user's project;
- reloads the configured date range with `WRITE_TRUNCATE`, so rerunning the same period does not append duplicates;
- writes a summary report back to Google Sheets.

Google Sheet used for the test run:

https://docs.google.com/spreadsheets/d/1ZW2rLd1KU7yPhuqzF0mjawc_UGOWf4Lj7Ql2K37flQ4/edit

## Project Structure

```text
src/ga_etl/
  config.py        # config parsing and validation
  sheets.py        # Google Sheets API wrapper
  bigquery_etl.py  # BigQuery dataset/query/load/report logic
  main.py          # CLI entry point
tests/             # focused unit tests
examples/          # sample Google Sheet config
DESIGN.md          # answers for the code-reading block
```

## Google Cloud Setup

1. Create or select a Google Cloud project with BigQuery enabled.
2. Enable Google Sheets API in the same project.
3. Create a service account.
4. Grant it these roles:
   - `BigQuery Job User` on the project;
   - `BigQuery Data Editor` on the target dataset/project.
5. Create a JSON key and keep it outside the repository.
6. Share the Google Sheet with the service account email as `Editor`.

The service account JSON is intentionally not committed to this repository.

The public source table is:

```text
bigquery-public-data.google_analytics_sample.ga_sessions_*
```

## Google Sheet Config

Create a sheet tab named `config` with two columns: `key` and `value`.

| key | value |
| --- | --- |
| project_id | ga-etl-test-494520 |
| dataset_id | marketing_analytics |
| target_table | ga_sessions_daily |
| start_date | 2017-08-01 |
| end_date | 2017-08-07 |
| report_spreadsheet_id | 1ZW2rLd1KU7yPhuqzF0mjawc_UGOWf4Lj7Ql2K37flQ4 |
| report_range | report!A1 |

There is also an example in `examples/config_sheet.csv`.

The report is written to the `report` tab.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run

Set environment variables first. The service account JSON path below is an example; the real key should stay outside the repository.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/keys/ga-etl-service-account.json"
export CONFIG_SPREADSHEET_ID="1ZW2rLd1KU7yPhuqzF0mjawc_UGOWf4Lj7Ql2K37flQ4"
export CONFIG_RANGE='config!A:B'
export PYTHONPATH=src

python -m ga_etl.main
```

Expected successful output:

```text
Loaded 20 aggregated rows into target table ga-etl-test-494520.marketing_analytics.ga_sessions_daily.
ETL finished: 2017-08-01..2017-08-07 -> ga-etl-test-494520.marketing_analytics.ga_sessions_daily; report rows: 20
```

You can also pass arguments explicitly:

```bash
PYTHONPATH=src python -m ga_etl.main \
  --credentials "$HOME/keys/ga-etl-service-account.json" \
  --config-spreadsheet-id "1ZW2rLd1KU7yPhuqzF0mjawc_UGOWf4Lj7Ql2K37flQ4" \
  --config-range 'config!A:B'
```

## Run Tests

```bash
pytest
```

The tests do not call Google APIs. They check local validation and deterministic config behavior.

## Idempotency

The ETL writes the configured date range directly into the final BigQuery table with `WRITE_TRUNCATE`.

For this test task, the pipeline is idempotent for the configured period: rerunning it replaces the previous result with fresh data instead of appending duplicates.

This approach also works in BigQuery Sandbox, where DML queries such as `MERGE` are not available without billing.

## Trade-offs

- The config format is intentionally simple: `key/value` is enough for one ETL job and easy to edit by hand.
- Aggregation is done in BigQuery instead of Python to avoid unnecessary data transfer.
- The project avoids Docker, Airflow and extra storage because they would add setup cost without improving this test task.
- BigQuery jobs have a small retry wrapper for transient 5xx/429 errors.
- For a production paid BigQuery project, I would consider a partitioned incremental load or `MERGE`, structured logging, Sheets retries and CI checks.

## Verification

The pipeline was run successfully with:

```text
project_id: ga-etl-test-494520
dataset_id: marketing_analytics
target_table: ga_sessions_daily
period: 2017-08-01..2017-08-07
report rows: 20
```

## Submission Checklist

- Public GitHub repository with this code.
- `DESIGN.md` with answers for Block 1.
- Google Sheet link shared with the reviewer.
- Service account JSON kept outside the repository.
# GA-ETL-Test-Report
