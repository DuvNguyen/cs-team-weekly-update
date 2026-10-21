# am_settings.py — who signs the AM report and whose workload rows go in it. Lives in data/ next to voice.json.
import json, os
import sessions

DEFAULTS = {"submitter": "Nguyen", "reviewer": "Jonas (COO)",
            "dev_roster": ["Le Minh Tri", "Vi Nguyen"],
            "seo_roster": ["Thang Dam Quyet", "Nguyen Nguyen Thi My"]}
MAX_TEXT, MAX_PEOPLE = 80, 20


def _path() -> str:
    os.makedirs(sessions.DATA_DIR, mode=0o700, exist_ok=True)
    return os.path.join(sessions.DATA_DIR, "am_settings.json")


def load() -> dict:
    try:
        with open(_path()) as f:
            saved = json.load(f)
        return {k: saved[k] if isinstance(saved.get(k), type(v)) else v for k, v in DEFAULTS.items()}
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return json.loads(json.dumps(DEFAULTS))


def _text(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > MAX_TEXT:
        raise ValueError(f"{field} must be 1 to {MAX_TEXT} characters")
    return value.strip()


def _roster(value, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(n, str) for n in value):
        raise ValueError(f"{field} must be a list of names")
    names = list(dict.fromkeys(n.strip() for n in value if n.strip()))
    if len(names) > MAX_PEOPLE or any(len(n) > MAX_TEXT for n in names):
        raise ValueError(f"{field} has too many or too long names")
    return names


def save(data: dict) -> dict:
    clean = {"submitter": _text(data.get("submitter"), "Submitter"), "reviewer": _text(data.get("reviewer"), "Reviewer"),
             "dev_roster": _roster(data.get("dev_roster"), "Developers"), "seo_roster": _roster(data.get("seo_roster"), "SEO team")}
    sessions._write_private(_path(), json.dumps(clean, ensure_ascii=False, indent=2))
    return clean
