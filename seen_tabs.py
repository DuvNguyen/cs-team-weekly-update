# seen_tabs.py — remembers which SEO-sheet tabs the person has already looked at, so Setup can tag a new one "New".
# The first time a sheet is listed every tab counts as seen (nothing is new yet). A tab that shows up later stays new
# until it is picked once. Saved in data/seen_tabs.json, one list per sheet id.
import json
import os
import threading

import sessions

_lock = threading.Lock()
MAX_TAB = 200


def _path() -> str:
    os.makedirs(sessions.DATA_DIR, mode=0o700, exist_ok=True)
    return os.path.join(sessions.DATA_DIR, "seen_tabs.json")


def _load() -> dict:
    try:
        with open(_path()) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, ValueError):
        return {}


def _save(data: dict) -> None:
    sessions._write_private(_path(), json.dumps(data, ensure_ascii=False, indent=2))


def new_tabs(sheet_id: str, tabs: list[str]) -> list[str]:
    """The tabs that were not in the sheet the last time it was listed and have not been picked since."""
    with _lock:
        data = _load()
        if not isinstance(data.get(sheet_id), list):
            data[sheet_id] = list(tabs)                      # first look at this sheet: the baseline
            _save(data)
            return []
        seen = set(data[sheet_id])
        return [t for t in tabs if t not in seen]


def mark_seen(sheet_id: str, tab: str) -> None:
    if not isinstance(tab, str) or not tab.strip() or len(tab) > MAX_TAB:
        return
    with _lock:
        data = _load()
        seen = data.setdefault(sheet_id, [])
        if tab not in seen:
            seen.append(tab)
            _save(data)
