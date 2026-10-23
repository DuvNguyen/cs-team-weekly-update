import updates

HEADER = ["Project", "", "", "", "", "", "", "October", "November", "SEO Trends/NEws"]
ROWS = [
    ["", "", "", "", "", "", "", "", "", ""],
    HEADER,
    ["ABCIS", "", "", "", "", "", "", "Optimize blogs", "Monthly report", "Competitor and Vietnam international schools.\n\nVingroup founds VERTA International School   "],
    ["VALO", "", "", "", "", "", "", "20 new blogs", "Monthly report"],                      # row ends before column J
    ["TSS", "", "", "", "", "", "", "x", "y", "   "],
]


def test_the_trends_column_is_found_by_its_header_not_its_letter():
    assert updates.trends_column(ROWS) == 9
    moved = [["Project", "SEO trends / news", "October"], ["ABCIS", "Fresh news", "x"]]
    assert updates.trends_column(moved) == 1


def test_no_trends_column_means_no_trends():
    rows = [["Project", "October"], ["ABCIS", "x"]]
    assert updates.trends_column(rows) is None
    assert updates.match_trends(rows, "ABCIS") == ""


def test_a_clients_trends_come_back_as_written_with_only_the_clutter_removed():
    text = updates.match_trends(ROWS, "ABCIS")
    assert text == "Competitor and Vietnam international schools.\n\nVingroup founds VERTA International School"


def test_names_match_without_caring_about_case_and_missing_cells_are_empty():
    assert updates.match_trends(ROWS, "  abcis ").startswith("Competitor")
    assert updates.match_trends(ROWS, "VALO") == ""            # short row
    assert updates.match_trends(ROWS, "TSS") == ""             # blank cell
    assert updates.match_trends(ROWS, "Nobody") == ""
    assert updates.match_trends([], "ABCIS") == ""


def test_long_runs_of_blank_lines_are_collapsed():
    rows = [["Project", "SEO Trends/News"], ["ABCIS", "a\n\n\n\n\nb"]]
    assert updates.match_trends(rows, "ABCIS") == "a\n\nb"


def test_the_status_says_why_there_are_no_trends():
    assert updates.trends_status(ROWS, "ABCIS")[1] == "found" and updates.trends_status(ROWS, "ABCIS")[0].startswith("Competitor")
    assert updates.trends_status(ROWS, "TSS") == ("", "empty")             # the cell is blank
    assert updates.trends_status(ROWS, "VALO") == ("", "empty")            # the row ends before the column
    assert updates.trends_status(ROWS, "Nobody") == ("", "no_row")
    assert updates.trends_status([["Project", "October"], ["ABCIS", "x"]], "ABCIS") == ("", "no_column")
    assert updates.trends_status([], "ABCIS") == ("", "no_column")


def test_a_task_cell_that_mentions_trends_is_not_taken_for_the_header():
    """Old tabs have no Trends column, but a client's task text can say "trends" in the first rows."""
    rows = [["Project", "Current 2 Weeks", "Next 2 Weeks"], [],
            ["ABCIS", "14/9-18/9 Monitor trends and website performance and write the monthly report for the school", "Monthly report"]]
    assert updates.trends_column(rows) is None
    assert updates.trends_status(rows, "ABCIS") == ("", "no_column")
