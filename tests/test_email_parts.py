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


def test_confirm_all_confirms_clean_parts_and_skips_the_flagged_ones():
    parts = build([{"title": "A", "text": "Clicks rose to 1,240."}, {"title": "B", "text": "We improved site speed by 40%."}, {"title": "C", "text": "Our focus continues."}])
    done, skipped = ep.confirm_all(parts, CTX)
    assert len(done) == 2 and len(skipped) == 1
    status = {p["title"]: p["status"] for p in parts if p["kind"] == "section"}
    assert status == {"A": "confirmed", "B": "review", "C": "confirmed"}
    assert not ep.ready(parts)                                # the flagged part still needs the person


def test_confirm_all_confirms_a_flagged_part_the_person_has_edited_and_leaves_deleted_ones_alone():
    parts = build([{"title": "A", "text": "We improved site speed by 40%."}, {"title": "B", "text": "x"}])
    a, b = parts[1], parts[2]
    ep.update_part(parts, a["id"], {"text": "We improved site speed by 40% (checked by dev)."}, CTX)
    ep.update_part(parts, b["id"], {"status": "deleted"}, CTX)
    done, skipped = ep.confirm_all(parts, CTX)
    assert done == [a["id"]] and skipped == [] and b["status"] == "deleted"
    assert ep.ready(parts)


def test_confirm_all_with_nothing_to_confirm_is_harmless():
    parts = build([{"title": "A", "text": "x"}])
    ep.confirm_all(parts, CTX)
    assert ep.confirm_all(parts, CTX) == ([], [])


TRENDS_CTX = {**CTX, "trends": "Competitor launched a new school.\nMOET directive (18 Oct)."}


def build_t(sections=None, **kw):
    return ep.build("Hi Sarah,", sections or [{"title": "A", "text": "x"}], TRENDS_CTX, structured=kw.get("structured", True),
                    trend=kw.get("trend", ""), sources=[], category="Furniture", sender="Mimi Pham")


def test_the_sheets_trends_become_an_optional_part_after_the_sections():
    parts = build_t(trend="Local search is shifting.")
    assert [p["kind"] for p in parts] == ["greeting", "section", "trends", "trend", "signoff"]
    t = parts[2]
    assert t["title"] == "SEO trends / news" and t["text"].startswith("Competitor launched") and t["optional"] is True and t["status"] == "review"
    assert not any(p["optional"] for p in parts if p["kind"] != "trends")


def test_no_trends_in_the_sheet_means_no_part():
    parts = ep.build("Hi", [{"title": "A", "text": "x"}], CTX, structured=True, trend="", sources=[], category="", sender="M")
    assert "trends" not in [p["kind"] for p in parts]


def test_the_trends_reach_the_email_only_once_confirmed():
    parts = build_t()
    assert "Competitor launched" not in ep.compose_body(parts)
    ep.update_part(parts, parts[2]["id"], {"status": "confirmed"}, TRENDS_CTX)
    body = ep.compose_body(parts)
    assert "SEO trends / news\nCompetitor launched a new school." in body and body.index("A\nx") < body.index("SEO trends / news")
    ep.update_part(parts, parts[2]["id"], {"status": "deleted"}, TRENDS_CTX)
    assert "Competitor launched" not in ep.compose_body(parts)


def test_an_unconfirmed_optional_part_does_not_block_the_client_or_the_count():
    parts = build_t()
    ep.update_part(parts, parts[1]["id"], {"status": "confirmed"}, TRENDS_CTX)
    assert ep.ready(parts) and ep.reviewed_count(parts) == (3, 3)           # greeting, section, sign-off; trends not counted
    ep.update_part(parts, parts[2]["id"], {"text": "Edited trend."}, TRENDS_CTX)
    assert ep.ready(parts) and "Edited trend." not in ep.compose_body(parts)    # edited, back in review: still left out


def test_confirm_all_also_confirms_the_trends_part():
    parts = build_t()
    done, skipped = ep.confirm_all(parts, TRENDS_CTX)
    assert parts[2]["id"] in done and "SEO trends / news" in ep.compose_body(parts)


def kinds_titles(parts):
    return [p["title"] or p["kind"] for p in parts]


def three_sections():
    return build([{"title": "A", "text": "a"}, {"title": "B", "text": "b"}, {"title": "C", "text": "c"}])


def test_moving_a_part_down_and_up_swaps_it_with_its_neighbour_and_the_email_follows():
    parts = three_sections()
    a, b = parts[1], parts[2]
    ep.move_part(parts, a["id"], "down")
    assert kinds_titles(parts) == ["greeting", "B", "A", "C", "signoff"]
    assert ep.compose_body(parts).index("B\nb") < ep.compose_body(parts).index("A\na")
    ep.move_part(parts, a["id"], "up")
    assert kinds_titles(parts) == ["greeting", "A", "B", "C", "signoff"]


def test_the_greeting_and_sign_off_never_move_and_nothing_moves_past_them():
    parts = three_sections()
    for fixed in (parts[0], parts[-1]):
        with pytest.raises(ValueError, match="fixed"):
            ep.move_part(parts, fixed["id"], "down" if fixed is parts[0] else "up")
    with pytest.raises(ValueError, match="first"):
        ep.move_part(parts, parts[1]["id"], "up")                  # would go above the greeting
    with pytest.raises(ValueError, match="last"):
        ep.move_part(parts, parts[3]["id"], "down")                # would go below the sign-off
    assert kinds_titles(parts) == ["greeting", "A", "B", "C", "signoff"]


def test_moving_keeps_status_and_edits_and_works_past_deleted_parts():
    parts = three_sections()
    a, b = parts[1], parts[2]
    ep.update_part(parts, a["id"], {"status": "confirmed"}, CTX)
    ep.update_part(parts, b["id"], {"status": "deleted"}, CTX)
    ep.move_part(parts, a["id"], "down")                           # swaps with the deleted B
    assert kinds_titles(parts)[1:3] == ["B", "A"] and a["status"] == "confirmed" and a["edited"] is False


def test_bad_direction_and_unknown_part_are_rejected():
    parts = three_sections()
    with pytest.raises(ValueError, match="direction"):
        ep.move_part(parts, parts[1]["id"], "sideways")
    with pytest.raises(ValueError, match="part"):
        ep.move_part(parts, "nope", "up")
