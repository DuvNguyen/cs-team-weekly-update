import json
import time
import pytest
from fastapi.testclient import TestClient

import pipeline, server, sessions


@pytest.fixture
def api(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"clients": [{"property": "https://benjaminsharvell.com/", "name": "Benjamin Sharvell", "category": "Fund raise"},
                                           {"property": "https://b.test/", "name": "Beta", "category": "Retail", "contact": "Sarah"}],
                               "seo_sheet_tab": "", "sender": "Mimi Pham", "gemini_api_key": "x"}))
    monkeypatch.setattr(pipeline, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(pipeline, "DEMO", True)
    monkeypatch.setattr(pipeline, "OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(sessions, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("WUT_DEMO", "1")
    return TestClient(server.app), cfg


def clients(api):
    return api.get("/api/config").json()["clients"]


def save(api, rows):
    return api.put("/api/clients", json=rows)


def greeting(api, name):
    job = api.post("/api/jobs", json={"tab": "", "clients": [name], "start": "2026-10-05", "end": "2026-10-18"}).json()
    for _ in range(100):
        j = api.get(f"/api/jobs/{job['id']}").json()
        if j["status"] == "ready":
            return next(p for p in j["clients"][0]["parts"] if p["kind"] == "greeting")["text"]
        time.sleep(0.1)
    raise AssertionError("job never finished")


def test_the_config_lists_each_clients_greeting_name_when_it_has_one(api):
    c, _ = api
    rows = {r["name"]: r for r in clients(c)}
    assert rows["Beta"]["contact"] == "Sarah" and "contact" not in rows["Benjamin Sharvell"]


def test_saving_a_greeting_name_changes_the_greeting_in_the_email(api):
    c, _ = api
    assert greeting(c, "Benjamin Sharvell") == "Hi Benjamin Sharvell team,"            # no alias yet: the old default
    rows = clients(c)
    rows[0]["contact"] = "Ben"
    assert save(c, rows).status_code == 200
    assert greeting(c, "Benjamin Sharvell") == "Hi Ben,"


def test_an_empty_greeting_name_is_removed_from_the_file_and_the_default_returns(api):
    c, cfg = api
    rows = clients(c)
    rows[1]["contact"] = "   "
    save(c, rows)
    assert "contact" not in json.loads(cfg.read_text())["clients"][1]
    assert greeting(c, "Beta") == "Hi Beta team,"


def test_other_settings_in_the_file_survive_saving_clients(api):
    c, cfg = api
    save(c, clients(c))
    assert json.loads(cfg.read_text())["sender"] == "Mimi Pham"


def test_bad_greeting_names_and_fields_are_rejected(api):
    c, _ = api
    rows = clients(c)
    for bad in ("x" * 61, "Ben\nSmith"):
        rows[0]["contact"] = bad
        assert save(c, rows).status_code == 400, bad
    rows[0]["contact"] = ""
    rows[0]["property"] = "  "
    assert save(c, rows).status_code == 400
    rows[0]["property"] = "https://benjaminsharvell.com/"
    rows[1]["name"] = "Benjamin Sharvell"                         # duplicate names stay rejected
    assert save(c, rows).status_code == 400


def test_whitespace_around_fields_is_trimmed(api):
    c, _ = api
    rows = clients(c)
    rows[0].update(name="  Benjamin Sharvell ", category=" Fund raise ", contact=" Ben ")
    save(c, rows)
    assert clients(c)[0]["contact"] == "Ben" and clients(c)[0]["name"] == "Benjamin Sharvell"
