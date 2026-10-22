import report

TEXT = "Hi Sarah,\n\nPerformance Overview\nClicks rose.\n\nRecent Work Completed (Oct 6 - Oct 19)\n- Fixed titles\n\nBest regards,\nMimi"


def spans(headings):
    return [TEXT[a:b] for a, b in report.heading_ranges(TEXT, headings)]


def test_a_heading_is_found_where_it_sits_on_its_own_line():
    assert spans(["Performance Overview", "Recent Work Completed (Oct 6 - Oct 19)"]) == ["Performance Overview", "Recent Work Completed (Oct 6 - Oct 19)"]


def test_the_same_words_inside_a_sentence_are_not_a_heading():
    text = "We saw a Performance Overview in the report.\nPerformance Overview\nBody."
    (a, b), = report.heading_ranges(text, ["Performance Overview"])
    assert text[a:b] == "Performance Overview" and a == text.index("\nPerformance Overview") + 1


def test_missing_and_empty_headings_are_skipped():
    assert spans(["Not in the email", "", "  "]) == []


def test_two_parts_with_the_same_heading_are_both_marked_in_order():
    text = "Notes\none\n\nNotes\ntwo"
    marks = report.heading_ranges(text, ["Notes", "Notes"])
    assert [m[0] for m in marks] == [0, text.index("Notes", 5)]
