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


def test_a_flagged_part_can_be_confirmed_on_purpose_and_still_shows_its_warning(api):
    job = ready_job(api)
    sec = part(job, "section")
    pipeline.JOBS[job["id"]]["clients"][0]["parts"][1]["text"] = "We improved site speed by 40%."      # as if Gemini had written it
    c = patch(api, job, sec, status="confirmed").json()
    got = next(p for p in c["parts"] if p["id"] == sec["id"])
    assert got["status"] == "confirmed" and got["check"]["flags"]


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


def test_confirm_all_endpoint_confirms_every_part_and_counts_the_warnings(api):
    job = ready_job(api)
    pipeline.JOBS[job["id"]]["clients"][0]["parts"][1]["text"] = "We improved site speed by 40%."      # one flagged part
    r = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all")
    assert r.status_code == 200
    body = r.json()
    assert body["confirmed"] == 3 and body["with_warnings"] == 1            # section, notes and trends; one carries a warning
    assert body["client"]["ready"] is True
    again = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all").json()
    assert again["confirmed"] == 0 and again["with_warnings"] == 0           # pressing it again changes nothing


def test_confirm_all_makes_a_clean_client_ready(api):
    job = ready_job(api)
    body = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all").json()
    assert body["with_warnings"] == 0 and body["client"]["ready"] is True


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


def test_parts_can_be_moved_up_and_down_and_the_email_text_follows(api):
    job = ready_job(api)
    notes = part(job, "notes")
    before = [p["kind"] for p in job["clients"][0]["parts"]]
    assert before == ["greeting", "section", "notes", "trends", "signoff"]
    r = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{notes['id']}/move", json={"direction": "up"})
    assert r.status_code == 200
    c = r.json()
    assert [p["kind"] for p in c["parts"]] == ["greeting", "notes", "section", "trends", "signoff"]
    assert c["body"].index("SEO team notes") < c["body"].index("Demo summary")


def test_moving_the_greeting_or_off_the_ends_is_refused(api):
    job = ready_job(api)
    g = part(job, "greeting")
    assert api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{g['id']}/move", json={"direction": "down"}).status_code == 400
    sec = part(job, "section")
    assert api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{sec['id']}/move", json={"direction": "up"}).status_code == 400
    assert api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{sec['id']}/move", json={"direction": "left"}).status_code == 400


def export_paragraphs(api, job):
    import io
    import docx
    r = api.post(f"/api/jobs/{job['id']}/export")
    assert r.status_code == 200
    return docx.Document(io.BytesIO(r.content)).paragraphs


def confirm_everything(api, job):
    assert api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all").status_code == 200


def test_headings_are_bold_in_the_word_file_and_text_is_not(api):
    job = ready_job(api)
    confirm_everything(api, job)
    paras = export_paragraphs(api, job)
    bold = {p.text for p in paras if p.text and all(r.bold for r in p.runs)}
    assert {"SEO team notes", "SEO trends / news"} <= bold                           # headings that the parts carry
    assert "Hi Sarah," not in bold and not any(t.startswith("Demo summary") for t in bold)


def test_the_word_file_has_no_empty_paragraphs_between_the_parts(api):
    job = ready_job(api)
    confirm_everything(api, job)
    paras = export_paragraphs(api, job)
    start = next(i for i, p in enumerate(paras) if p.text == "Hi Sarah,")
    assert all(p.text.strip() for p in paras[start:])                                  # greeting to sign-off: no blank lines


def test_the_word_file_follows_the_order_and_the_confirmed_trends_only(api):
    job = ready_job(api)
    for kind in ("section", "notes"):
        patch(api, job, part(job, kind), status="confirmed")
    texts = [p.text for p in export_paragraphs(api, job)]
    assert "SEO trends / news" not in texts                                            # optional and not confirmed
    api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{part(job, 'notes')['id']}/move", json={"direction": "up"})
    patch(api, job, part(job, "trends"), status="confirmed")
    texts = [p.text for p in export_paragraphs(api, job)]
    assert texts.index("SEO team notes") < texts.index(next(t for t in texts if t.startswith("Demo summary")))
    assert "SEO trends / news" in texts


def test_confirm_all_puts_the_confirmed_trends_into_the_email_text_everywhere(api):
    job = ready_job(api)
    trends = part(job, "trends")["text"]
    assert trends not in job["clients"][0]["body"]
    body = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/confirm-all").json()["client"]["body"]
    assert trends in body                                                       # the text shown on the card
    assert trends in api.get(f"/api/jobs/{job['id']}").json()["clients"][0]["body"]
    assert trends in pipeline.current_body(pipeline.JOBS[job["id"]]["clients"][0])   # what a Google Doc publish uses
    assert trends in [p.text for p in export_paragraphs(api, job)]                  # what the Word file uses


def test_regenerate_rebuilds_the_parts_and_resets_the_reviews(api):
    job = ready_job(api)
    patch(api, job, part(job, "section"), status="confirmed")
    patch(api, job, part(job, "section"), text="My own wording.")
    r = api.post(f"/api/jobs/{job['id']}/clients/Alpha/regenerate", json={"prompt": "shorter", "style_id": None})
    assert r.status_code == 200, r.text
    c = r.json()
    assert [p["kind"] for p in c["parts"]] == ["greeting", "section", "notes", "trends", "signoff"]
    assert "My own wording." not in c["body"] and "shorter" in c["body"]            # the demo text echoes the instruction
    assert [p["status"] for p in c["parts"]] == ["confirmed", "review", "review", "review", "confirmed"]
    assert c["parts_reviewed"] == 2 and not c["ready"]


def test_a_part_can_be_moved_to_a_typed_position(api):
    job = ready_job(api)
    trends = part(job, "trends")                                    # greeting, section, notes, trends, sign-off
    r = api.post(f"/api/jobs/{job['id']}/clients/Alpha/parts/{trends['id']}/move", json={"position": 2})
    assert r.status_code == 200
    assert [p["kind"] for p in r.json()["parts"]] == ["greeting", "trends", "section", "notes", "signoff"]


def test_a_bad_typed_position_or_an_unclear_request_is_refused(api):
    job = ready_job(api)
    sec = part(job, "section")
    url = f"/api/jobs/{job['id']}/clients/Alpha/parts/{sec['id']}/move"
    assert api.post(url, json={"position": 1}).status_code == 400            # the greeting's place
    assert api.post(url, json={"position": 5}).status_code == 400            # the sign-off's place
    assert api.post(url, json={}).status_code == 400                         # neither a direction nor a position
    assert api.post(url, json={"direction": "up", "position": 3}).status_code == 400   # both
