# sessions.py — 30-day login sessions and per-user Google tokens, kept in ./data (gitignored, mode 600).
#
# A session is a random 256-bit id. The browser holds the id in an HttpOnly cookie; we store only its
# SHA-256 hash, so a leaked sessions.json cannot be replayed as a cookie.
import hashlib, json, os, secrets, threading, time

DATA_DIR = os.environ.get("WUT_DATA", "data")
SESSION_DAYS = 30
SESSION_SECONDS = SESSION_DAYS * 24 * 3600

_lock = threading.Lock()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _file(*parts: str) -> str:
    os.makedirs(os.path.join(DATA_DIR, *parts[:-1]), mode=0o700, exist_ok=True)
    return os.path.join(DATA_DIR, *parts)


def _write_private(path: str, text: str) -> None:
    tmp = f"{path}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)                      # atomic: a crash never leaves half a file


def _load() -> dict:
    try:
        with open(_file("sessions.json")) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    _write_private(_file("sessions.json"), json.dumps(data))


def create(user: dict) -> str:
    """Start a session for user {email, name, picture}; returns the raw id for the cookie."""
    sid = secrets.token_urlsafe(32)
    now = time.time()
    with _lock:
        data = {k: v for k, v in _load().items() if v["expires"] > now}      # drop expired ones
        data[_hash(sid)] = {**user, "expires": now + SESSION_SECONDS}
        _save(data)
    return sid


def get(sid: str | None) -> dict | None:
    if not sid:
        return None
    with _lock:
        s = _load().get(_hash(sid))
    return s if s and s["expires"] > time.time() else None


def delete(sid: str | None) -> None:
    if not sid:
        return
    with _lock:
        data = _load()
        if data.pop(_hash(sid), None) is not None:
            _save(data)


# ---- the user's Google tokens (access + refresh), one file per account ----

def _token_file(email: str) -> str:
    return _file("tokens", _hash(email.lower())[:24] + ".json")


def save_token(email: str, creds_json: str) -> None:
    with _lock:
        _write_private(_token_file(email), creds_json)


def load_token(email: str) -> dict | None:
    try:
        with open(_token_file(email)) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def delete_token(email: str) -> None:
    with _lock:
        try:
            os.remove(_token_file(email))
        except FileNotFoundError:
            pass
