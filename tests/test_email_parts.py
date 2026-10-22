import json
import pytest

import email_parts as ep

CTX = {"series": {"totals": {"clicks": 1240, "impressions": 38900, "ctr": "3.2%", "position": "6.8"}},
       "prev": {"totals": {"clicks": 1100, "impressions": 36000, "ctr": "3.1%", "position": "7.4"}},
       "this_week": "Published 3 blog posts", "next_week": "Refresh the services pages", "trend": "", "sources": []}


def gen(*pairs):
    return json.dumps({"sections": [{"title": t, "content": c} for t, c in pairs]})


def test_structured_output_becomes_one_section_per_entry():
    got = ep.from_generation(gen(("Performance", "Clicks rose to 1,240."), ("", "Thanks!")), structured=True)
    assert got == [{"title": "Performance", "text": "Clicks rose to 1,240."}, {"title": "", "text": "Thanks!"}]


def test_json_in_code_fences_and_extra_chatter_still_parses():
    raw = "Here you go:\n```json\n" + gen(("A", "text")) + "\n```"
    assert ep.from_generation(raw, structured=True) == [{"title": "A", "text": "text"}]


def test_garbage_output_falls_back_to_one_untitled_section():
    assert ep.from_generation("just some prose", structured=True) == [{"title": "", "text": "just some prose"}]
    assert ep.from_generation(json.dumps({"sections": []}), structured=True) == [{"title": "", "text": "{\"sections\": []}"}]


def test_unstructured_output_is_one_section():
    assert ep.from_generation("One paragraph.", structured=False) == [{"title": "", "text": "One paragraph."}]


def build(sections, structured=True, trend="", sources=()):
    return ep.build("Hi Sarah,", sections, CTX, structured=structured, trend=trend, sources=list(sources), category="Furniture", sender="Mimi Pham")


def test_parts_run_greeting_sections_trend_signoff_and_template_parts_start_confirmed():
    parts = build([{"title": "Performance", "text": "Clicks rose."}], trend="Local search is shifting.", sources=["https://x.test/a"])
    assert [p["kind"] for p in parts] == ["greeting", "section", "trend", "signoff"]
    assert [p["status"] for p in parts] == ["confirmed", "review", "review", "confirmed"]
    assert parts[2]["title"] == "Industry trend — Furniture" and "Source: https://x.test/a" in parts[2]["text"]
    assert parts[3]["text"] == "Best regards,\nMimi Pham\nSaigon Digital"
    assert len({p["id"] for p in parts}) == 4


def test_a_style_without_sections_gets_the_notes_as_their_own_part():
    parts = build([{"title": "", "text": "Summary."}], structured=False)
    assert [p["kind"] for p in parts] == ["greeting", "section", "notes", "signoff"]
    assert parts[2]["text"] == "Current 2 weeks: Published 3 blog posts\nNext 2 weeks: Refresh the services pages"


def test_body_is_the_same_text_the_old_single_box_held():
    parts = build([{"title": "Performance", "text": "Clicks rose."}, {"title": "", "text": "Thanks!"}])
    assert ep.compose_body(parts) == "Hi Sarah,\n\nPerformance\nClicks rose.\n\nThanks!\n\nBest regards,\nMimi Pham\nSaigon Digital"


def test_deleted_parts_leave_the_body():
    parts = build([{"title": "A", "text": "keep"}, {"title": "B", "text": "drop"}])
    ep.update_part(parts, parts[2]["id"], {"status": "deleted"}, CTX)
    assert "drop" not in ep.compose_body(parts) and "keep" in ep.compose_body(parts)


def test_editing_a_part_marks_it_edited_and_asks_for_a_new_confirmation():
    parts = build([{"title": "A", "text": "Clicks rose to 1,240."}])
    sec = parts[1]
    ep.update_part(parts, sec["id"], {"status": "confirmed"}, CTX)
    assert sec["status"] == "confirmed"
    ep.update_part(parts, sec["id"], {"text": "Clicks rose to 1,240 this period."}, CTX)
    assert sec["edited"] is True and sec["status"] == "review" and "this period" in ep.compose_body(parts)


def test_a_flagged_part_cannot_be_confirmed_until_the_person_edits_it():
    parts = build([{"title": "A", "text": "We improved site speed by 40%."}])
    sec = parts[1]
    with pytest.raises(ValueError, match="not in"):
        ep.update_part(parts, sec["id"], {"status": "confirmed"}, CTX)
    ep.update_part(parts, sec["id"], {"text": "We improved site speed by 40% (measured by our dev team)."}, CTX)
    ep.update_part(parts, sec["id"], {"status": "confirmed"}, CTX)           # their edit means they vouch for it
    assert sec["status"] == "confirmed"


def test_a_flagged_part_can_still_be_deleted_and_undo_returns_it_to_review():
    parts = build([{"title": "A", "text": "We improved site speed by 40%."}])
    sec = parts[1]
    ep.update_part(parts, sec["id"], {"status": "deleted"}, CTX)
    ep.update_part(parts, sec["id"], {"status": "review"}, CTX)
    assert sec["status"] == "review"


def test_unknown_part_and_bad_values_are_rejected():
    parts = build([{"title": "A", "text": "x"}])
    with pytest.raises(ValueError, match="part"):
        ep.update_part(parts, "nope", {"status": "confirmed"}, CTX)
    with pytest.raises(ValueError, match="status"):
        ep.update_part(parts, parts[1]["id"], {"status": "banana"}, CTX)
    with pytest.raises(ValueError, match="long"):
        ep.update_part(parts, parts[1]["id"], {"text": "x" * 20001}, CTX)


def test_ready_means_every_part_confirmed_or_deleted_and_at_least_one_confirmed():
    parts = build([{"title": "A", "text": "x"}])
    assert not ep.ready(parts)
    ep.update_part(parts, parts[1]["id"], {"status": "confirmed"}, CTX)
    assert ep.ready(parts) and ep.reviewed_count(parts) == (3, 3)
    ep.update_part(parts, parts[1]["id"], {"text": "y"}, CTX)
    assert not ep.ready(parts) and ep.reviewed_count(parts) == (2, 3)
