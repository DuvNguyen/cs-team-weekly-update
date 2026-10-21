import datetime as dt
import glob, hashlib, json, re
import docx
from docx.enum.text import WD_COLOR_INDEX
import pytest

import am_docx, workload_pic

SAMPLE = [p for p in glob.glob("docs/*Account Manager Report*.docx") if "/.~" not in p][0]
MON = dt.date(2026, 10, 19)


def paragraphs_text(d):
    return [p.text.strip() for p in d.paragraphs]


def all_text(d):
    cells = [c.text for t in d.tables for r in t.rows for c in r.cells]
    return "\n".join(paragraphs_text(d) + cells)


@pytest.fixture
def pics(tmp_path):
    week = {MON + dt.timedelta(days=i): 5.0 for i in range(5)}
    return [workload_pic.render_row(n, 7, week, str(tmp_path / f"{i}.png")) for i, n in enumerate("ABCDE")]


@pytest.fixture
def full(pics):
    return {"submitter": "Nguyen", "reviewer": "Jonas (COO)", "date_text": "23/10/26",
            "dev_pictures": pics[:2], "seo_pictures": pics[2:],
            "last_week": ["Kenno: Feedback received"], "this_week": ["AIP Foundation: Handover sent", "SIT: staging"],
            "blockers": ["Fix header (Kenno): Stuck"]}


def build(tmp_path, data):
    out = str(tmp_path / "report.docx")
    blanks = am_docx.build(out, data)
    return docx.Document(out), blanks


def test_every_sample_prompt_is_present_in_order(tmp_path, full):
    sample = docx.Document(SAMPLE).paragraphs
    keep = [0, 5, 6, 7, 8, 11, 13, 14, 15, 16, 17, 23, 33, 35, 40, 41, 42, 47, 48, 49, 50, 51, 52, 53]
    expected = [sample[i].text.strip() for i in keep]
    out = iter(paragraphs_text(build(tmp_path, full)[0]))
    for want in expected:
        assert any(line == want for line in out), f"missing or out of order: {want[:60]}"


def test_sample_answers_are_not_copied(tmp_path):
    text = all_text(build(tmp_path, {})[0])
    for stale in ("Nein.", "CRCC Asia", "Kenno feedback", "Ventia Dashboard", "Silblox"):
        assert stale not in text


def test_header_filled(tmp_path, full):
    text = all_text(build(tmp_path, full)[0])
    for want in ("Submitted by:", "Nguyen", "Date of Submission:", "23/10/26", "Reviewer:", "Jonas (COO)", "(Due every Friday by 4:00 PM)"):
        assert want in text


def test_bullets_under_last_and_this_week(tmp_path, full):
    d, _ = build(tmp_path, full)
    ps = d.paragraphs
    texts = [p.text.strip() for p in ps]
    last, this = texts.index("Last week:"), texts.index("This week:")
    between_last = [p for p in ps[last + 1:this] if p.text.strip()]
    after_this = [p for p in ps[this + 1:this + 3]]
    assert [p.text for p in between_last] == ["Kenno: Feedback received"]
    assert [p.text for p in after_this] == ["AIP Foundation: Handover sent", "SIT: staging"]
    assert all(p.style.name.startswith("List Bullet") for p in between_last + after_this)    # real list paragraphs


def body_order(d):
    """Body children as ('p', text, has_picture) in document order."""
    out = []
    for el in d.element.body.iterchildren():
        if el.tag.endswith("}p"):
            out.append((el.xpath("string(.)").strip(), bool(el.xpath(".//pic:pic"))))
    return out


def test_pictures_sit_under_their_sections(tmp_path, full):
    d, _ = build(tmp_path, full)
    assert len(d.inline_shapes) == 5
    order = body_order(d)
    idx = lambda start: next(i for i, (t, _) in enumerate(order) if t.startswith(start))
    dev = [i for i, (_, pic) in enumerate(order) if pic and idx("Developer Task Lock-In") < i < idx("Scope Creep")]
    seo = [i for i, (_, pic) in enumerate(order) if pic and idx("Task Delegation Audit") < i < idx("Tooling")]
    assert len(dev) == 2 and len(seo) == 3


def yellow_blank_runs(d):
    return [r for p in d.paragraphs for r in p.runs if r.font.highlight_color == WD_COLOR_INDEX.YELLOW and not r.text.strip()]


def test_unfilled_prompts_are_highlighted_and_returned(tmp_path, full):
    d, blanks = build(tmp_path, full)
    assert "Scope Creep & Upsell Tracking" in blanks and "Weekly WFH/In-Office Roster" in blanks
    assert not any(b in blanks for b in ("Developer Task Lock-In", "Task Delegation Audit", "Client Deliverable Alignment", "Blocker Resolution"))
    assert len(yellow_blank_runs(d)) == len(blanks)
    _, empty = build(tmp_path, {})
    assert len(empty) == 12                                    # nothing supplied: every prompt blank


def test_sample_file_is_unchanged(tmp_path, full):
    before = hashlib.sha256(open(SAMPLE, "rb").read()).hexdigest()
    build(tmp_path, full)
    assert hashlib.sha256(open(SAMPLE, "rb").read()).hexdigest() == before


def test_odd_and_long_text_is_safe(tmp_path, full):
    full["this_week"] = ["Brand & <b>Co</b> \"quotes\" 🚀 " + "x" * 500, "bad\x00char\x0b"]
    full["submitter"] = "Nguyễn & <Co>"
    d, _ = build(tmp_path, full)
    assert "x" * 500 in all_text(d) and "\x00" not in all_text(d)


@pytest.mark.parametrize("bad", ["\ud800", "\ufffe", "\uffff", "ok\ud800\udc00x"])
def test_characters_that_are_not_valid_xml_are_dropped_not_fatal(tmp_path, full, bad):
    full["this_week"] = [f"a{bad}b"]
    full["answers"] = {"scope_creep": f"x{bad}y"}
    d, _ = build(tmp_path, full)                         # must not raise
    assert "ab" in paragraphs_text(d) or "ok" in "".join(paragraphs_text(d))


def test_typed_answer_is_written_and_is_not_blank(tmp_path):
    data = {"answers": {"scope_creep": "CRCC banner is out of scope.\nPIC to confirm.", "blockers": "None"}}
    d, blanks = build(tmp_path, data)
    text = paragraphs_text(d)
    assert "CRCC banner is out of scope." in text and "PIC to confirm." in text and "None" in text
    assert "Scope Creep & Upsell Tracking" not in blanks and "Blocker Resolution" not in blanks
    assert "Cross-Department Handovers" in blanks


def test_typed_answer_sits_under_its_own_prompt(tmp_path):
    d, _ = build(tmp_path, {"answers": {"handovers": "All delivered."}})
    order = [t for t, _ in body_order(d)]
    assert order.index("All delivered.") == next(i for i, t in enumerate(order) if t.startswith("Cross-Department Handovers")) + 1


def test_typed_answer_works_beside_automatic_content(tmp_path, full):
    full["answers"] = {"task_delegation": "Everyone has 3 days mapped."}
    d, blanks = build(tmp_path, full)
    assert "Everyone has 3 days mapped." in paragraphs_text(d) and "Task Delegation Audit" not in blanks


def test_whitespace_only_or_unknown_answers_do_not_count(tmp_path):
    d, blanks = build(tmp_path, {"answers": {"scope_creep": "  \n ", "no_such_prompt": "x"}})
    assert "Scope Creep & Upsell Tracking" in blanks and "x" not in paragraphs_text(d)
