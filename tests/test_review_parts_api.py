import json
import time
import pytest
from fastapi.testclient import TestClient

import pipeline, server, sessions


@pytest.fixture
def api(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"clients": [{"property": "https://a.test/", "name": "Alpha", "category": "Retail", "contact": "Sarah"}],
                               "seo_sheet_tab": "", "sender": "Mimi Pham", "gemini_api_key": "x"}))
    monkeypatch.setattr(pipeline, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(pipeline, "DEMO", True)
    monkeypatch.setattr(pipeline, "OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(sessions, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("WUT_DEMO", "1")
    return TestClient(server.app)


def ready_job(api):
    job = api.post("/api/jobs", json={"tab": "", "clients": ["Alpha"], "start": "2026-10-05", "end": "2026-10-18"}).json()
    for _ in range(100):
        j = api.get(f"/api/jobs/{job['id']}").json()
        if j["status"] == "ready":
            return j
        time.sleep(0.1)
    raise AssertionError(f"job never finished: {j['status']} {j.get('error')}")


def part(job, kind):
    return next(p for p in job["clients"][0]["parts"] if p["kind"] == kind)


def patch(api, job, p, **body):
    return api.patch(f"/api/jobs/{job['id']}/clients/Alpha/parts/{p['id']}", json=body)


def test_each_client_email_comes_back_as_parts_with_their_checks(api):
    job = ready_job(api)
    c = job["clients"][0]
    assert [p["kind"] for p in c["parts"]] == ["greeting", "section", "notes", "trends", "signoff"]
    assert all("tags" in p["check"] for p in c["parts"])
    assert part(job, "greeting")["text"] == "Hi Sarah," and part(job, "greeting")["check"]["tags"] == ["template"]
    assert c["parts_total"] == 4 and c["parts_reviewed"] == 2 and c["ready"] is False        # the optional trends part is not counted


def test_confirming_every_part_makes_the_client_ready_and_export_works(api):
    job = ready_job(api)
    assert api.post(f"/api/jobs/{job['id']}/export").status_code in (400, 409)       # nothing reviewed yet
    for kind in ("section", "notes"):
        assert patch(api, job, part(job, kind), status="confirmed").status_code == 200
    j = api.get(f"/api/jobs/{job['id']}").json()
    assert j["clients"][0]["ready"] is True
    assert api.post(f"/api/jobs/{job['id']}/export").status_code == 200


def test_editing_a_part_updates_the_email_and_needs_a_new_confirmation(api):
    job = ready_job(api)
    sec = part(job, "section")
    patch(api, job, sec, status="confirmed")
    c = patch(api, job, sec, text="Our own words about this period.").json()
    edited = next(p for p in c["parts"] if p["id"] == sec["id"])
    assert edited["status"] == "review" and edited["edited"] and "you" in edited["check"]["tags"]
    assert "Our own words about this period." in c["body"]


def test_deleting_the_notes_part_removes_it_from_the_email(api):
    job = ready_job(api)
    c = patch(api, job, part(job, "notes"), status="deleted").json()
    assert "SEO team notes" not in c["body"]


def test_a_part_with_untraceable_details_cannot_be_confirmed_until_edited(api):
    job = ready_job(api)
    sec = part(job, "section")
    pipeline.JOBS[job["id"]]["clients"][0]["parts"][1]["text"] = "We improved site speed by 40%."      # as if Gemini had written it
    r = patch(api, job, sec, status="confirmed")
    assert r.status_code == 409 and "not in the sources" in r.json()["detail"]
    assert patch(api, job, sec, text="We improved site speed by 40% (checked by dev).").status_code == 200
    assert patch(api, job, sec, status="confirmed").status_code == 200


def test_unknown_part_and_bad_status_are_rejected(api):
    job = ready_job(api)
    assert api.patch(f"/api/jobs/{job['id']}/clients/Alpha/parts/nope", json={"status": "confirmed"}).status_code == 400
    assert patch(api, job, part(job, "section"), status="banana").status_code == 400


def test_the_check_is_recomputed_from_the_current_text(api):
    job = ready_job(api)
    sec = part(job, "section")
    c = patch(api, job, sec, text="Clicks are up 99%.").json()
    chk = next(p for p in c["parts"] if p["id"] == sec["id"])["check"]
    assert chk["numbers"]["unmatched"] == ["99%"] and chk["flags"]


def test_confirm_all_endpoint_confirms_the_clean_parts_and_reports_the_rest(api):
    job = ready_job(api)
    pipeline.JOBS[job["id"]]["clients"][0]["parts"][1]["text"] = "We improved site speed by 40%."      # one flagged part
    r = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all")
    assert r.status_code == 200
    body = r.json()
    assert body["confirmed"] == 2 and body["needs_checking"] == 1          # notes and trends are confirmed, the flagged one is not
    assert body["client"]["ready"] is False
    api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all")      # pressing it again changes nothing
    assert api.get(f"/api/jobs/{job['id']}").json()["clients"][0]["parts_reviewed"] == 3


def test_confirm_all_makes_a_clean_client_ready(api):
    job = ready_job(api)
    body = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all").json()
    assert body["needs_checking"] == 0 and body["client"]["ready"] is True


def test_the_sheets_trends_show_up_for_review_and_only_join_the_email_when_confirmed(api):
    job = ready_job(api)
    t = part(job, "trends")
    assert t["optional"] is True and t["check"]["tags"] == ["sheet"] and t["status"] == "review"
    assert t["text"] not in job["clients"][0]["body"]
    for kind in ("section", "notes"):
        patch(api, job, part(job, kind), status="confirmed")
    j = api.get(f"/api/jobs/{job['id']}").json()
    assert j["clients"][0]["ready"] is True                                  # the trends part doesn't block it
    assert api.post(f"/api/jobs/{job['id']}/export").status_code == 200       # exported without the trends
    c = patch(api, job, t, status="confirmed").json()
    assert t["text"] in c["body"]


@pytest.mark.parametrize("status, expected", [
    ("empty", 'nothing in the "SEO Trends/News" column'),
    ("no_column", 'no "SEO Trends/News" column'),
    ("no_row", "no row in the selected sheet tab"),
    ("no_tab", "No SEO sheet tab was chosen"),
    ("tab_error", "could not be opened"),
])
def test_the_client_says_why_it_has_no_trends(api, status, expected):
    job = ready_job(api)
    assert job["clients"][0]["trends_note"] == ""                           # demo data has trends: nothing to say
    pipeline.JOBS[job["id"]]["_ctx"]["Alpha"]["trends_status"] = status
    note = api.get(f"/api/jobs/{job['id']}").json()["clients"][0]["trends_note"]
    assert expected in note
