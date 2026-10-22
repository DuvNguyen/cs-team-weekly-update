import provenance as pv

NOW = {"totals": {"clicks": 1240, "impressions": 38900, "ctr": "3.2%", "position": "6.8"}}
PREV = {"totals": {"clicks": 1100, "impressions": 36000, "ctr": "3.1%", "position": "7.4"}}
NOTES = "Fixed missing titles on 12 pages\nPublished 3 blog posts: https://example.com/blog-1\nRefresh the services pages"


def ctx(notes=NOTES, trend="", sources=()):
    return {"series": NOW, "prev": PREV, "this_week": notes, "next_week": "", "trend": trend, "sources": list(sources)}


def part(text, kind="section", title="", edited=False):
    return {"id": "p", "kind": kind, "title": title, "text": text, "status": "review", "edited": edited}


def check(text, **kw):
    return pv.check_part(part(text, **{k: v for k, v in kw.items() if k in ("kind", "title", "edited")}), ctx(**{k: v for k, v in kw.items() if k in ("notes", "trend", "sources")}))


def test_numbers_that_match_search_console_are_matched():
    c = check("Clicks rose to 1,240 and impressions reached 38,900. Average position improved to 6.8, CTR 3.2%.")
    assert c["numbers"]["unmatched"] == [] and len(c["numbers"]["matched"]) == 4 and "gsc" in c["tags"]


def test_changes_between_the_two_periods_are_allowed_rounded_either_way():
    # 1240 vs 1100 is +140, +12.7%. Writers say "up 12.7%", "up 13%", "up 140 clicks".
    for text in ("Clicks are up 12.7%.", "Clicks are up 13%.", "That is 140 more clicks."):
        assert check(text)["numbers"]["unmatched"] == [], text


def test_a_number_that_is_not_in_the_data_or_the_notes_is_flagged():
    c = check("We improved site speed by 40%.")
    assert c["numbers"]["unmatched"] == ["40%"] and c["flags"] and "gsc" not in c["tags"]


def test_numbers_that_are_in_the_seo_notes_are_allowed():
    assert check("We published 3 blog posts and fixed 12 pages.")["numbers"]["unmatched"] == []


def test_dates_urls_and_list_numbers_are_not_numbers_to_check():
    c = check("1. Done by Oct 19 and 20 October.\nSee https://example.com/page-2024/x?id=557 for details.")
    assert c["numbers"]["unmatched"] == []


def test_bullet_lines_must_trace_to_the_notes_even_when_reworded():
    c = check("- Fixed 12 pages with missing titles\n- Published three blog posts: https://example.com/blog-1\n- Launched a brand new checkout flow")
    tags = [(l["text"][:12], l["tag"]) for l in c["lines"]]
    assert tags == [("- Fixed 12 p", "notes"), ("- Published ", "notes"), ("- Launched a", "flag")]
    assert any("Launched a brand new checkout flow" in f for f in c["flags"])


def test_prose_without_numbers_is_just_ai_wording_not_a_flag():
    c = check("Our focus stays on making the site easier to find for local customers.")
    assert c["flags"] == [] and c["tags"] == ["ai"]


def test_a_section_mixing_numbers_and_notes_lists_each_source_once():
    c = check("Clicks rose to 1,240.\n- Fixed 12 pages with missing titles")
    assert c["tags"] == ["gsc", "notes", "ai"] or c["tags"] == ["gsc", "notes"]
    assert "gsc" in c["tags"] and "notes" in c["tags"]


def test_greeting_signoff_notes_and_trend_parts_have_fixed_sources():
    assert check("Hi Sarah,", kind="greeting")["tags"] == ["template"]
    assert check("Best regards,\nMimi", kind="signoff")["tags"] == ["template"]
    assert check("Fixed missing titles on 12 pages", kind="notes")["tags"] == ["notes"]
    t = check("Local search is shifting.", kind="trend", trend="Local search is shifting.", sources=["https://x.test/a"])
    assert t["tags"] == ["trend"] and t["flags"] == []


def test_edited_parts_get_the_you_tag_and_keep_their_flags():
    c = check("We improved site speed by 40%.", edited=True)
    assert "you" in c["tags"] and c["flags"]


def test_empty_text_and_missing_data_do_not_crash():
    assert pv.check_part(part(""), {"series": {"totals": {}}, "prev": {"totals": {}}, "this_week": "", "next_week": "", "trend": "", "sources": []})["flags"] == []
    assert pv.check_part(part("Clicks 5"), {})["numbers"]["unmatched"] == ["5"]


def test_a_note_reworded_with_extra_wording_still_traces_to_the_notes():
    c = check("- Fixed missing title tags across 12 site pages to ensure better search visibility")
    assert [l["tag"] for l in c["lines"]] == ["notes"] and c["flags"] == []


def test_a_line_that_only_shares_one_word_with_a_note_is_still_flagged():
    c = check("- Fixed the checkout bug on mobile")
    assert [l["tag"] for l in c["lines"]] == ["flag"]


def test_word_forms_match_across_singular_plural_and_tense():
    assert pv.traces_to_notes("- Published the pages", "Publish page")
    assert pv.traces_to_notes("- Titles were rewritten", "Rewrite title")
