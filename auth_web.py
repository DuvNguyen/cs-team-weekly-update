# auth_web.py — "Sign in with Google" for the web UI (OAuth 2.0 authorization-code flow + PKCE),
# then a 30-day session cookie. The original auth.py (desktop flow) is left as is.
import json, os, secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

import auth, sessions

# Google adds the identity scopes it grants; don't treat the extra ones as an error.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

DATA_SCOPES = auth.SCOPES
SCOPES = DATA_SCOPES + ["openid", "https://www.googleapis.com/auth/userinfo.email",
                        "https://www.googleapis.com/auth/userinfo.profile"]
SESSION_COOKIE = "wut_session"
OAUTH_COOKIE = "wut_oauth"          # holds state + PKCE verifier for the few minutes of a login

router = APIRouter(prefix="/api/auth")


class NotSignedIn(Exception):
    """The session or the Google token is gone; the user has to sign in again."""


def _public_url() -> str:
    return os.environ.get("WUT_PUBLIC_URL", "http://localhost:3000").rstrip("/")


def _config() -> dict:
    with open(os.environ.get("WUT_CONFIG", "config.json")) as f:
        return json.load(f)


def _flow(state: str | None = None) -> Flow:
    return Flow.from_client_secrets_file(
        _config()["client_secret_path"], scopes=SCOPES, state=state,
        redirect_uri=f"{_public_url()}/api/auth/callback", autogenerate_code_verifier=True)


def _cookie(resp, key: str, value: str, max_age: int) -> None:
    resp.set_cookie(key, value, max_age=max_age, httponly=True, samesite="lax",
                    secure=_public_url().startswith("https"), path="/")


def _home(error: str = "") -> RedirectResponse:
    return RedirectResponse(f"{_public_url()}/" + (f"?auth_error={error}" if error else ""), status_code=302)


# ---------- the gate ----------

DEMO_USER = {"email": "demo@local", "name": "Demo", "picture": ""}


def require_user(request: Request) -> dict:
    if os.environ.get("WUT_DEMO") == "1":
        return DEMO_USER
    user = sessions.get(request.cookies.get(SESSION_COOKIE))
    if not user:
        raise HTTPException(401, "Not signed in")
    return user


# ---------- routes ----------

@router.get("/login")
def login():
    flow = _flow()
    url, state = flow.authorization_url(access_type="offline", prompt="consent")   # offline = refresh token
    resp = RedirectResponse(url, status_code=302)
    _cookie(resp, OAUTH_COOKIE, f"{state}.{flow.code_verifier}", 600)
    return resp


@router.get("/callback")
def callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    saved = request.cookies.get(OAUTH_COOKIE, "")
    saved_state, _, verifier = saved.partition(".")
    if error or not code or not state or not verifier or not secrets.compare_digest(state, saved_state):
        return _redirect_clear("denied" if error else "state")      # state mismatch = possible CSRF
    try:
        flow = _flow(state)
        flow.code_verifier = verifier
        flow.fetch_token(code=code)
        creds = flow.credentials
        claims = id_token.verify_oauth2_token(creds.id_token, GoogleRequest(), creds.client_id)
    except Exception:
        return _redirect_clear("exchange")
    if not set(DATA_SCOPES) <= set(creds.scopes or []):
        return _redirect_clear("scopes")                            # user unticked a permission
    email = claims.get("email", "").lower()
    allowed = [d.strip().lower() for d in os.environ.get("WUT_ALLOWED_DOMAINS", "").split(",") if d.strip()]
    if not email or not claims.get("email_verified") or (allowed and email.split("@")[-1] not in allowed):
        return _redirect_clear("domain")
    sessions.save_token(email, creds.to_json())
    sid = sessions.create({"email": email, "name": claims.get("name", email), "picture": claims.get("picture", "")})
    resp = _home()
    _cookie(resp, SESSION_COOKIE, sid, sessions.SESSION_SECONDS)
    resp.delete_cookie(OAUTH_COOKIE, path="/")
    return resp


def _redirect_clear(error: str) -> RedirectResponse:
    resp = _home(error)
    resp.delete_cookie(OAUTH_COOKIE, path="/")
    return resp


@router.get("/me")
def me(user: dict = Depends(require_user)):
    return {"email": user["email"], "name": user.get("name", ""), "picture": user.get("picture", ""),
            "demo": os.environ.get("WUT_DEMO") == "1"}


@router.post("/logout")
def logout(request: Request):
    user = sessions.get(request.cookies.get(SESSION_COOKIE))
    sessions.delete(request.cookies.get(SESSION_COOKIE))
    if user:
        sessions.delete_token(user["email"])
        _forget(user["email"])
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


_forget_hooks = []


def on_forget(fn) -> None:
    _forget_hooks.append(fn)


def _forget(email: str) -> None:
    for fn in _forget_hooks:
        fn(email)


# ---------- Google credentials for the API calls ----------

def credentials_for(email: str) -> Credentials:
    info = sessions.load_token(email)
    if not info:
        raise NotSignedIn("Google access is missing, sign in again.")
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid:
        try:
            creds.refresh(GoogleRequest())
        except RefreshError:
            raise NotSignedIn("Google access expired or was revoked, sign in again.")
        sessions.save_token(email, creds.to_json())
    return creds
