# The SEO team's notes (column B / C) and the SEO Trends/News cell are told as the situation, in friendly words, without adding facts.
import email_parts
import pipeline
import provenance
import report
import voice
import voice_store

STYLE = voice_store.get_style(None)
SERIES = {"totals": {"clicks": 10, "impressions": 100, "ctr": "10%", "position": 8}}
CELL = "Competitor Alert: Vingroup opens a new school (Hanoi, Aug 2027).\nGoogle's September spam update caused volatility."


def _prompt(**kw):
    return report.build_prompt("ABCIS", "School", SERIES, SERIES, kw.pop("this_week", "Published 3 blogs"), kw.pop("next_week", "Optimize old blogs"), **kw)


def test_the_notes_are_told_as_where_things_stand_not_summarised(monkeypatch):
    monkeypatch.setattr(voice, "STRUCTURE", "1. Title: Work\n   Content: the work")
    p = _prompt()
    assert "where things stand" in p and "Do not shorten" in p


def test_the_trends_cell_is_given_to_gemini_as_the_only_source_of_industry_context():
    p = _prompt(trends=CELL)
    assert "Vingroup opens a new school" in p and "Do not add facts" in p


def test_without_a_trends_cell_the_email_must_not_claim_industry_news():
    p = _prompt()
    assert "No industry or Google news was reported" in p


def test_trends_prompt_keeps_every_fact_and_forbids_new_ones():
    p = report.build_trends_prompt("ABCIS", CELL)
    assert CELL in p and "Keep every fact" in p and "Do not add" in p and "Start straight with the news" in p


def test_natural_trends_uses_gemini_and_falls_back_to_the_cell(monkeypatch):
    monkeypatch.setattr(pipeline, "DEMO", False)
    monkeypatch.setattr(pipeline, "_generate", lambda g, prompt, as_json=False: "  A friendly version.  ")
    assert pipeline._natural_trends(None, STYLE, "ABCIS", CELL) == "A friendly version."

    def boom(*a, **k):
        raise RuntimeError("quota")
    monkeypatch.setattr(pipeline, "_generate", boom)
    assert pipeline._natural_trends(None, STYLE, "ABCIS", CELL) == CELL
    monkeypatch.setattr(pipeline, "_generate", lambda *a, **k: "")
    assert pipeline._natural_trends(None, STYLE, "ABCIS", CELL) == CELL


def test_demo_mode_never_calls_gemini(monkeypatch):
    monkeypatch.setattr(pipeline, "DEMO", True)
    monkeypatch.setattr(pipeline, "_generate", lambda *a, **k: 1 / 0)
    assert pipeline._natural_trends(None, STYLE, "ABCIS", CELL) == CELL


def test_the_part_keeps_the_original_cell():
    ctx = {"trends": "A friendly version.", "trends_raw": CELL}
    parts = email_parts.build("Hi,", [{"title": "", "text": "x"}], ctx, True, "", [], "", "Mimi")
    t = next(p for p in parts if p["kind"] == "trends")
    assert t["text"] == "A friendly version." and t["source"] == CELL


def _trends_part(text, source=CELL):
    return {"kind": "trends", "text": text, "source": source, "edited": False}


def test_a_reworded_trend_is_tagged_sheet_and_ai():
    assert provenance.check_part(_trends_part("A friendly version of it."), {})["tags"] == ["sheet", "ai"]


def test_a_word_for_word_trend_is_tagged_sheet_only():
    assert provenance.check_part(_trends_part(CELL), {})["tags"] == ["sheet"]
    assert provenance.check_part({"kind": "trends", "text": CELL, "edited": False}, {})["tags"] == ["sheet"]


def test_a_number_that_is_not_in_the_cell_is_flagged():
    out = provenance.check_part(_trends_part("The new school will take 4,000 students and opens in Aug 2027."), {})
    assert out["numbers"]["unmatched"] == ["4,000"] and out["flags"]
    ok = provenance.check_part(_trends_part("Vingroup opens a new school in Hanoi in Aug 2027."), {})
    assert not ok["flags"]
