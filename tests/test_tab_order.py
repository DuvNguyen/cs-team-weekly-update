import datetime as dt
import tab_order as to

TODAY = dt.date(2026, 10, 22)
YOURS = ["11/5-15/5", "17/8-21/8-New", "12/10-23/10-New", "28/9-9/10-Old", "14/9-25/9-Old", "7/9-11/9-Old"]


def test_the_real_sheets_tabs_come_out_newest_first():
    assert to.newest_first(YOURS, TODAY) == ["12/10-23/10-New", "28/9-9/10-Old", "14/9-25/9-Old", "7/9-11/9-Old", "17/8-21/8-New", "11/5-15/5"]


def test_the_new_year_is_worked_out_from_today_not_from_the_month_number():
    tabs = ["30/11-11/12", "14/12-25/12", "28/12-8/1", "7/12-18/12"]
    assert to.newest_first(tabs, dt.date(2026, 12, 20)) == ["28/12-8/1", "14/12-25/12", "7/12-18/12", "30/11-11/12"]
    # in early January the late-December tabs are last year's
    assert to.newest_first(["29/12-9/1", "15/12-26/12", "12/1-23/1"], dt.date(2027, 1, 5)) == ["12/1-23/1", "29/12-9/1", "15/12-26/12"]


def test_tabs_without_dates_go_last_in_their_sheet_order():
    tabs = ["Template", "12/10-23/10", "Notes", "28/9-9/10", "31/2-5/3"]
    assert to.newest_first(tabs, TODAY) == ["12/10-23/10", "28/9-9/10", "Template", "Notes", "31/2-5/3"]


def test_equal_dates_keep_the_sheets_order_and_nothing_is_lost():
    tabs = ["12/10-23/10-A", "12/10-23/10-B", "5/10-16/10"]
    got = to.newest_first(tabs, TODAY)
    assert got == ["12/10-23/10-A", "12/10-23/10-B", "5/10-16/10"] and sorted(got) == sorted(tabs)


def test_spaces_around_the_dash_and_an_empty_list_are_fine():
    assert to.newest_first(["1/9 - 12/9", "14/9 - 25/9"], TODAY) == ["14/9 - 25/9", "1/9 - 12/9"]
    assert to.newest_first([], TODAY) == []
