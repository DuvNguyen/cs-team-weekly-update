# updates.py — read the SEO team's weekly sheet.
# Layout: column A = client name, B = "this week", C = "next week", and a column headed "SEO Trends/News" (found by its header).
import re

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


def trends_column(rows: list) -> int | None:
    """Index of the column whose header (in the first rows) mentions "trend", e.g. "SEO Trends/NEws"."""
    for row in rows[:3]:
        for i, cell in enumerate(row):
            if re.search(r"trend", str(cell), re.I):
                return i
    return None

def match_trends(rows: list, client_name: str) -> str:
    """The client's SEO trends / news cell, as written (trimmed). '' when there is no such column, row or text."""
    col = trends_column(rows)
    target = client_name.strip().lower()
    if col is None:
        return ""
    for row in rows:
        if row and str(row[0]).strip().lower() == target:
            text = str(row[col]) if len(row) > col else ""
            return re.sub(r"\n{3,}", "\n\n", "\n".join(line.rstrip() for line in text.strip().splitlines()))
    return ""
