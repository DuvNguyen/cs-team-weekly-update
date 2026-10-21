# settings_web.py — lets the UI import the Google client secret and the .env values (Gemini key),
# so a new Mac needs no file copying. Before the client secret exists nobody can sign in, so the
# routes are open for that first run only; afterwards they need a signed-in session.
import json, os
from pathlib import Path
from dotenv import dotenv_values
from fastapi import APIRouter, Depends, HTTPException, Request
from io import StringIO
from pydantic import BaseModel

import auth_web

ENV_PATH = Path(__file__).parent / ".env"
ENV_KEYS = ("GEMINI_API_KEY", "WUT_ALLOWED_DOMAINS")      # the only .env values the UI may set

router = APIRouter(prefix="/api")


def _secret_path() -> Path:
    try:
        return Path(auth_web._config()["client_secret_path"])
    except (OSError, KeyError, ValueError):
        return Path("client_secret.json")


def _gate(request: Request) -> None:
    if _secret_path().exists():
        auth_web.require_user(request)


class FileIn(BaseModel):
    content: str


@router.get("/setup-status")
def setup_status():
    return {"client_secret": _secret_path().exists()}


@router.get("/settings", dependencies=[Depends(_gate)])
def get_settings():
    key = os.environ.get("GEMINI_API_KEY", "")
    return {"client_secret": _secret_path().exists(), "gemini_key": f"••••{key[-4:]}" if key else ""}


@router.put("/settings/client-secret", dependencies=[Depends(_gate)])
def put_client_secret(body: FileIn):
    try:
        data = json.loads(body.content)
        info = data.get("web") or data.get("installed") or {}
        ok = bool(info.get("client_id") and info.get("client_secret"))
    except (ValueError, AttributeError):
        ok = False
    if not ok:
        raise HTTPException(400, "That is not a Google OAuth client secret file (client_secret.json).")
    path = _secret_path()
    path.write_text(body.content)
    path.chmod(0o600)
    return {"ok": True}


@router.put("/settings/env", dependencies=[Depends(_gate)])
def put_env(body: FileIn):
    values = {k: v for k, v in dotenv_values(stream=StringIO(body.content)).items() if k in ENV_KEYS and v}
    if not values:
        raise HTTPException(400, f"No usable values found. Expected one of: {', '.join(ENV_KEYS)}.")
    if any("\n" in v or "\r" in v for v in values.values()):
        raise HTTPException(400, "Values must be on one line.")
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    for key, value in values.items():
        line = f'{key}="{value.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'
        i = next((n for n, l in enumerate(lines) if l.split("=", 1)[0].strip() == key), None)
        if i is None:
            lines.append(line)
        else:
            lines[i] = line
        os.environ[key] = value
    ENV_PATH.write_text("\n".join(lines) + "\n")
    ENV_PATH.chmod(0o600)
    return {"updated": sorted(values)}
