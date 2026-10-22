import io
import pytest
from fastapi.testclient import TestClient

import pipeline, server, sessions, voice_store


def style(structure):
    return {"id": "s1", "name": "Mimi", "persona": "Write as Mimi.", "style": [], "avoid": [], "examples": [], "structure": structure}


def clean(structure):
    return voice_store.validate({"styles": [style(structure)], "default_id": "s1"})["styles"][0]["structure"]


def test_source_tags_are_saved_with_each_section():
    s = clean([{"id": "a", "title": "Work completed", "instruction": "A list.", "enabled": True, "title_source": "email", "instruction_source": "you"}])[0]
    assert s["title_source"] == "email" and s["instruction_source"] == "you"


def test_unknown_or_missing_source_tags_become_empty():
    s = clean([{"id": "a", "title": "T", "instruction": "I", "enabled": True, "title_source": "the moon"}])[0]
    assert s["title_source"] == "" and s["instruction_source"] == ""


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WUT_DEMO", "1")                # passes the sign-in gate
    monkeypatch.setattr(pipeline, "DEMO", True)        # no Gemini calls (this flag is read once, at import)
    monkeypatch.setattr(sessions, "DATA_DIR", str(tmp_path))
    return TestClient(server.app)


EMAIL = "Hi Sarah, great week!\n\nClicks rose to 1,240 this period.\n\nNext we focus on service pages."


def test_structure_review_endpoint_returns_checked_sections(client):
    r = client.post("/api/voice/structure/analyze", json={"email": EMAIL})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == EMAIL and body["sections"]
    for s in body["sections"]:
        assert s["found"] and EMAIL[s["start"]:s["end"]] == s["excerpt"] and s["note_source"] == "ai"


def test_structure_review_endpoint_rejects_an_empty_email(client):
    assert client.post("/api/voice/structure/analyze", json={"email": "  "}).status_code == 400
