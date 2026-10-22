import datetime
import report, voice, voice_store

D = datetime.date
SECTIONS = [
    {"id": "a", "title": "", "instruction": "A warm opening line.", "enabled": True},
    {"id": "b", "title": "Recent Work Completed ({period})", "instruction": "Bulleted list.", "enabled": True},
    {"id": "c", "title": "Next Steps ({next_period})", "instruction": "The plan.", "enabled": True},
    {"id": "d", "title": "Off", "instruction": "Hidden.", "enabled": False},
]


def _style(structure):
    s = voice_store.default_style()
    s["structure"] = structure
    return s


def test_render_structure_fills_dates_and_skips_disabled():
    text = voice_store.render_structure(_style(SECTIONS), D(2026, 10, 6), D(2026, 10, 19))
    assert "Recent Work Completed (Oct 6 - Oct 19)" in text
    assert "Next Steps (Oct 20 - Nov 2)" in text
    assert "Title: (none" in text and "Off" not in text


def test_old_styles_without_structure_still_validate():
    s = voice_store.default_style()
    assert voice_store.validate({"styles": [s]})["styles"][0]["structure"] == []
    assert not voice_store.has_structure(s)


def test_structure_is_validated_and_kept():
    v = voice_store.validate({"styles": [_style(SECTIONS + [{"title": "", "instruction": ""}])]})
    assert len(v["styles"][0]["structure"]) == 4          # the empty row is dropped
    assert voice_store.has_structure(v["styles"][0])


def _prompt(structure):
    voice.STRUCTURE = structure
    series = {"totals": {"clicks": 10, "impressions": 100, "ctr": "10%", "position": 8}}
    try:
        return report.build_prompt("LPE", "", series, series, "Wrote posts", "Publish posts")
    finally:
        voice.STRUCTURE = ""


def test_prompt_uses_sections_or_one_paragraph():
    assert "ONE paragraph" in _prompt("")
    p = _prompt("1. Title: Next Steps\n   Content: plan")
    assert "ONE paragraph" not in p and "Title: Next Steps" in p


def test_structured_email_leaves_out_raw_notes():
    assert "SEO team notes" in report.compose_body("Body", "did x", "will y")
    assert "SEO team notes" not in report.compose_body("Body", "did x", "will y", notes=False)


def test_analyze_prompt_with_braces_reads_the_email():
    class Resp:
        text = '{"name": "X", "persona": "Write as a manager.", "style": ["Be warm."], "avoid": ["jargon"], "structure": [{"title": "Next ({next_period})", "instruction": "plan"}]}'

    class Models:
        def generate_content(self, model, contents, config):
            assert "Hi Chloé" in contents and "{email}" not in contents
            return Resp()

    class Gemini:
        models = Models()

    s = voice_store.analyze(Gemini(), "m", "Hi Chloé, hello")
    assert s["structure"][0]["title"] == "Next ({next_period})"
