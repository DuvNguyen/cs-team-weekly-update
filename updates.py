# updates.py — read the SEO team's weekly sheet.
# Layout: column A = client name, B = "this week", C = "next week".

def match(rows: list, client_name: str):
    """Return (this_week, next_week) text for the client. Case-insensitive, trimmed.
    Returns ('', '') if the client has no row in the sheet."""
    target = client_name.strip().lower()
    for row in rows:
        if row and row[0].strip().lower() == target:
            this_week = row[1].strip() if len(row) > 1 else ""
            next_week = row[2].strip() if len(row) > 2 else ""
            return this_week, next_week
    return "", ""

def fetch_rows(service, sheet_id: str, rng: str) -> list:
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute()
    return result.get("values", [])
