from __future__ import annotations

from google.oauth2 import service_account
from googleapiclient.discovery import build


SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsClient:
    def __init__(self, credentials_path: str) -> None:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=SHEETS_SCOPES,
        )
        self._service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def read_values(self, spreadsheet_id: str, range_name: str) -> list[list[str]]:
        result = (
            self._service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])

    def write_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list[list[object]],
    ) -> None:
        body = {"values": values}
        (
            self._service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

