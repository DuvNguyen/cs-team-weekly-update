import pipeline

c = pipeline.clean_notes


def test_no_task_week_is_dropped():
    assert c("12/10 - 16/10\nNo task\n\n19/10-23/10") == ""


def test_empty_next_plan_is_dropped():
    assert c("12/10-16/10\n\n\n19/10-23/10") == ""


def test_real_work_keeps_its_week_header_and_links():
    raw = "12/10 - 16/10\nPublish/Schedule October blogs\n\n1 blog is published:\nEN: https://x.com/a/ \n\n19/10-23/10"
    assert c(raw) == "12/10 - 16/10\nPublish/Schedule October blogs\n1 blog is published:\nEN: https://x.com/a/"


def test_only_the_empty_week_is_dropped():
    assert c("12/10-16/10\nNo task\n\n19/10-23/10\nMonitor trends") == "19/10-23/10\nMonitor trends"


def test_whitespace_only_lines_and_status_text():
    assert c("12/10-16/10\nWrite blogs\n \n19/10-23/10\n ") == "12/10-16/10\nWrite blogs"
    assert c("Haven't signed yet") == ""
    assert c("") == "" and c(None) == ""


def test_text_without_headers_is_kept():
    assert c("Publish 3 blogs") == "Publish 3 blogs"
