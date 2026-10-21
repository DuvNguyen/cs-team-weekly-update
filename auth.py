import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google import genai

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

def _credentials(config: dict) -> Credentials:
    token_path = config["token_path"]
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config["client_secret_path"], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds

def get_services(config: dict) -> dict:
    creds = _credentials(config)
    return {
        "webmasters": build("searchconsole", "v1", credentials=creds),
        "sheets": build("sheets", "v4", credentials=creds),
        "docs": build("docs", "v1", credentials=creds),
        "drive": build("drive", "v3", credentials=creds),
        "gemini": genai.Client(api_key=config["gemini_api_key"]),
    }
