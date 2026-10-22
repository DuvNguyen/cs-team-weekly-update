import datetime as dt
import json
import pytest
from fastapi.testclient import TestClient

import pipeline, seen_tabs, server, sessions, tab_order


@pytest.fixture(autouse=True)
def data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(sessions, "DATA_DIR", str(tmp_path))


def test_the_first_time_a_sheet_is_listed_nothing_is_new():
    assert seen_tabs.new_tabs("sheet1", ["11/5-15/5", "12/10-23/10"]) == []


def test_a_tab_that_appears_later_is_new_until_it_is_picked():
    seen_tabs.new_tabs("sheet1", ["11/5-15/5", "12/10-23/10"])                   # the baseline
    tabs = ["26/10-6/11", "11/5-15/5", "12/10-23/10"]
    assert seen_tabs.new_tabs("sheet1", tabs) == ["26/10-6/11"]
    assert seen_tabs.new_tabs("sheet1", tabs) == ["26/10-6/11"]                   # still new: listing it does not make it seen
    seen_tabs.mark_seen("sheet1", "26/10-6/11")
    assert seen_tabs.new_tabs("sheet1", tabs) == []


def test_each_sheet_has_its_own_memory_and_it_survives_a_restart(tmp_path):
    seen_tabs.new_tabs("A", ["x"])
    assert seen_tabs.new_tabs("B", ["y"]) == []                                   # B's own baseline
    assert seen_tabs.new_tabs("A", ["x", "z"]) == ["z"]
    assert json.loads((tmp_path / "seen_tabs.json").read_text())["A"] == ["x"]     # saved to disk


def test_marking_works_even_before_the_baseline_and_ignores_junk():
    seen_tabs.mark_seen("S", "t1")
    assert seen_tabs.new_tabs("S", ["t1", "t2"]) == ["t2"]
    seen_tabs.mark_seen("S", "")
    seen_tabs.mark_seen("S", "x" * 500)
    assert seen_tabs.new_tabs("S", ["t1", "t2"]) == ["t2"]


def test_a_damaged_file_is_treated_as_empty(tmp_path):
    (tmp_path / "seen_tabs.json").write_text("{nope")
    assert seen_tabs.new_tabs("S", ["a"]) == []


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setenv("WUT_DEMO", "1")
    monkeypatch.setattr(pipeline, "DEMO", True)
    state = {"tabs": ["12/10-23/10", "28/9-9/10"]}
    monkeypatch.setattr(pipeline, "list_tabs", lambda email=None: state["tabs"])
    monkeypatch.setattr(pipeline, "load_config", lambda: {"seo_sheet_id": "sheet-1", "clients": []})
    monkeypatch.setattr(tab_order, "_today", lambda: dt.date(2026, 10, 22))
    return TestClient(server.app), state


def test_the_tabs_endpoint_says_which_tabs_are_new_and_picking_one_clears_it(api):
    c, state = api
    assert c.get("/api/tabs").json() == {"tabs": ["12/10-23/10", "28/9-9/10"], "new": []}
    state["tabs"] = ["26/10-6/11"] + state["tabs"]
    assert c.get("/api/tabs").json()["new"] == ["26/10-6/11"]
    assert c.post("/api/tabs/seen", json={"tab": "26/10-6/11"}).status_code == 200
    assert c.get("/api/tabs").json()["new"] == []


def test_the_tabs_endpoint_lists_the_newest_tab_first(api):
    c, state = api
    state["tabs"] = ["11/5-15/5", "12/10-23/10", "28/9-9/10"]
    assert c.get("/api/tabs").json()["tabs"] == ["12/10-23/10", "28/9-9/10", "11/5-15/5"]
