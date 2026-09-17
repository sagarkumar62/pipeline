import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

cred_val = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/google-sheets-service-account.json")
sheet_id = os.getenv("GOOGLE_SHEET_ID", "1COdZaxjJcangOa56qZ7CbUHowUAEsKcnUchHPSM8DQo")

if os.path.exists(cred_val):
    with open(cred_val, "r", encoding="utf-8") as f:
        cred_info = json.load(f)
else:
    cred_info = json.loads(cred_val)

if "private_key" in cred_info and "\\n" in cred_info["private_key"]:
    cred_info["private_key"] = cred_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(cred_info, scopes=SCOPES)
client = gspread.authorize(creds)

print("AUTH SUCCESS: Authenticated as client_email:", cred_info.get("client_email"))

sh = client.open_by_key(sheet_id)
print(f"SPREADSHEET ACCESS SUCCESS: Title = '{sh.title}', ID = {sheet_id[:6]}...{sheet_id[-4:]}")

worksheets = [w.title for w in sh.worksheets()]
print("Available worksheets:", worksheets)
