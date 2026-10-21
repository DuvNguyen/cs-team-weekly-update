import json
import pytest
from fastapi.testclient import TestClient

import auth_web, server, settings_web


@pytest.fixture
def client(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"client_secret_path": str(tmp_path / "client_secret.json")}))
    monkeypatch.setenv("WUT_CONFIG", str(cfg))
    monkeypatch.setattr(settings_web, "ENV_PATH", tmp_path / ".env")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    return TestClient(server.app), tmp_path


SECRET = json.dumps({"web": {"client_id": "id", "client_secret": "s"}})


def test_first_run_is_open_then_locked(client):
    c, tmp = client
    assert c.get("/api/setup-status").json() == {"client_secret": False}
    assert c.put("/api/settings/client-secret", json={"content": SECRET}).status_code == 200
    assert (tmp / "client_secret.json").exists()
    assert c.get("/api/setup-status").json() == {"client_secret": True}
    assert c.get("/api/settings").status_code == 401          # now needs a session


def test_rejects_wrong_file(client):
    c, _ = client
    assert c.put("/api/settings/client-secret", json={"content": "{}"}).status_code == 400
    assert c.put("/api/settings/client-secret", json={"content": "nope"}).status_code == 400


def test_env_import_merges_and_whitelists(client):
    c, tmp = client
    (tmp / ".env").write_text("KEEP=1\nGEMINI_API_KEY=old\n")
    r = c.put("/api/settings/env", json={"content": "GEMINI_API_KEY=abc123\nWUT_DEMO=1\n"})
    assert r.json() == {"updated": ["GEMINI_API_KEY"]}
    assert (tmp / ".env").read_text() == 'KEEP=1\nGEMINI_API_KEY="abc123"\n'
    assert c.put("/api/settings/env", json={"content": "OTHER=1"}).status_code == 400
