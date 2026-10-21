import datetime as dt
import am_bullets as b

MON = dt.date(2026, 10, 19)
PROJECTS = {"p1": "Kenno", "p2": "AIP Foundation"}


def t(name, status, project="p1", start="2026-10-20", due="2026-10-21", **kw):
    return {"id": name, "name": name, "status": status, "project_id": project, "pic_start_date": start, "pic_due_date": due, **kw}


def test_status_groups():
    assert b.status_group("Task Definition") == "Planned" and b.status_group("Ready for Execution") == "Planned"
    assert b.status_group("In Progress") == "In Progress" and b.status_group("On Hold/Paused") == "In Progress"
    for s in ("Peer Review", "Ready for Peer Review", "Testing", "Ready for QAQC", "Needs Revision"):
        assert b.status_group(s) == "QA"
    assert b.status_group("DONE (published/Deployed)") == "Completed"
    for s in ("Stuck", "Ready to Publish/Deploy", "Publishing/Deployment", "Something new"):
        assert b.status_group(s) == "In Progress"


def test_bullets_group_by_project_and_week():
    tasks = [t("Fix header", "DONE (published/Deployed)"), t("Add banner", "Testing"), t("Write FAQ", "In Progress"),
             t("Audit", "In Progress", project="p2"),
             t("Old job", "DONE (published/Deployed)", start="2026-10-12", due="2026-10-14")]      # last week
    last, this = b.client_bullets(tasks, PROJECTS, MON)
    assert this == ["AIP Foundation: 1 in progress (Audit)",
                    "Kenno: 1 completed, 1 in QA, 1 in progress (Fix header; Add banner; Write FAQ)"]
    assert last == ["Kenno: 1 completed (Old job)"]


def test_long_task_lists_are_shortened():
    tasks = [t(f"Task {i}", "In Progress") for i in range(6)]
    _, this = b.client_bullets(tasks, PROJECTS, MON)
    assert this == ["Kenno: 6 in progress (Task 0; Task 1; Task 2; +3 more)"]


def test_unknown_project_and_empty_week():
    assert b.client_bullets([], PROJECTS, MON) == ([], [])
    _, this = b.client_bullets([t("X", "In Progress", project="zzz")], PROJECTS, MON)
    assert this == ["Unknown project: 1 in progress (X)"]


def test_blockers_only_stuck_and_on_hold_and_not_done():
    tasks = [t("A", "Stuck"), t("B", "On Hold/Paused", project="p2"), t("C", "In Progress"), t("D", "DONE (published/Deployed)")]
    assert b.blockers(tasks, PROJECTS) == ["B (AIP Foundation): On Hold/Paused", "A (Kenno): Stuck"]


def test_unmatched_roster_name_is_reported_not_fatal():
    people = [{"id": "1", "name": "Le Minh Tri"}, {"id": "2", "name": "Nguyễn Thị My"}]
    matched, missing = b.match_roster(["le minh  tri", "Nguyen Thi My", "Nobody"], people)
    assert [p["id"] for p in matched] == ["1", "2"] and missing == ["Nobody"]
