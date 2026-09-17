import os
import json
import gspread
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from src.models.tool import ToolRecord
from src.utils.logging import setup_logger

load_dotenv()
logger = setup_logger("google_sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADERS = [
    "Name",
    "Description",
    "Official Website",
    "Official Logo",
    "GitHub Repository",
    "Categories",
    "Source",
    "Source URL",
    "Record ID",
    "Website Verified",
    "Logo Verified",
    "Description Grounded"
]


class GoogleSheetsExporter:
    """
    Exports data to Google Sheets using the Google Sheets API via gspread.
    """

    def __init__(self, credentials_json: str = None, sheet_id: str = None):
        cred_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not cred_env:
            cred_env = "credentials/google-sheets-service-account.json"
        self.credentials_json = credentials_json or cred_env
        self.sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID")
        self.worksheet_name = "Tools"
        self.client = None
        self._authenticate()

    def _authenticate(self):
        if not self.credentials_json or not self.sheet_id:
            logger.warning("Google Sheets credentials not fully configured in environment.")
            return

        try:
            if os.path.exists(self.credentials_json):
                with open(self.credentials_json, "r", encoding="utf-8") as f:
                    cred_info = json.load(f)
            else:
                cred_info = json.loads(self.credentials_json)

            if "private_key" in cred_info and "\\n" in cred_info["private_key"]:
                cred_info["private_key"] = cred_info["private_key"].replace("\\n", "\n")

            creds = Credentials.from_service_account_info(cred_info, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            logger.info(f"Successfully authenticated as {cred_info.get('client_email')}")
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets API: {e}")
            self.client = None

    def record_to_row(self, record: Union[ToolRecord, Dict[str, Any]]) -> List[str]:
        if isinstance(record, ToolRecord):
            t = record.model_dump()
        else:
            t = record

        name = t.get("name") or ""
        desc = t.get("description") if t.get("description") is not None else ""
        official_url = t.get("official_url") or ""
        official_website = official_url if official_url.startswith("http") else ""
        logo_url = t.get("logo_url") or ""
        github_repo_url = t.get("github_repo_url") or ""

        cats = t.get("categories", [])
        categories_str = " | ".join(cats) if isinstance(cats, list) else str(cats)

        disc = t.get("discovery_source", {})
        if isinstance(disc, dict):
            source_name = disc.get("name", "GitHub API Search")
            source_url = disc.get("url", github_repo_url)
        else:
            source_name = str(disc) if disc else "GitHub API Search"
            source_url = github_repo_url

        rec_id = t.get("id", "")
        web_ver = "True" if t.get("website_verified", False) else "False"
        logo_ver = "True" if t.get("logo_verified", False) else "False"
        desc_grounded = "True" if t.get("description_grounded", False) else "False"

        return [
            name,
            desc,
            official_website,
            logo_url,
            github_repo_url,
            categories_str,
            source_name,
            source_url,
            rec_id,
            web_ver,
            logo_ver,
            desc_grounded
        ]

    def export(self, records: List[Union[ToolRecord, Dict[str, Any]]]) -> str:
        """
        Batches and uploads records to Google Sheets.
        Returns the spreadsheet URL upon success.
        """
        if not self.client:
            logger.warning("Skipping Google Sheets export due to missing or unauthenticated client.")
            return ""

        logger.info(f"Initiating Google Sheets export for {len(records)} records to Sheet ID: {self.sheet_id}")
        spreadsheet = self.client.open_by_key(self.sheet_id)

        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows="100", cols="20")

        worksheet.clear()

        rows = [HEADERS]
        for r in records:
            rows.append(self.record_to_row(r))

        worksheet.update(values=rows, range_name="A1")
        logger.info(f"Published {len(records)} records to worksheet '{self.worksheet_name}' successfully.")

        try:
            spreadsheet.share("", perm_type="anyone", role="reader")
            logger.info("Public reader sharing verified for spreadsheet.")
        except Exception as e:
            logger.warning(f"Note on sharing: {e}")

        url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit"
        return url

    def read_back_data(self) -> List[List[str]]:
        if not self.client:
            raise RuntimeError("Client not authenticated")
        spreadsheet = self.client.open_by_key(self.sheet_id)
        worksheet = spreadsheet.worksheet(self.worksheet_name)
        return worksheet.get_all_values()

