import datetime as dt
import workload as w

MON = dt.date(2026, 10, 19)


def task(**kw):
    base = {"id": "t1", "name": "T", "status": "In Progress", "project_id": "p1", "pic_id": "A",
            "peer_reviewer_id": None, "reviewer_id": None, "qa_qc_id": None, "publisher_id": None,
            "estimations": None, "pic_estimation": None, "peer_review_estimation": None,
            "qa_qc_estimation": None, "publish_estimation": None,
            "pic_time_tracked": None, "peer_review_time_tracked": None, "qa_qc_time_tracked": None, "publish_time_tracked": None,
            "pic_start_date": None, "pic_due_date": None, "peer_review_start_date": None, "peer_review_due_date": None,
            "qa_qc_start_date": None, "qa_qc_due_date": None, "publish_start_date": None, "publish_due_date": None}
    base.update(kw)
    return base


def week(person, tasks):
    return w.daily_hours(tasks, MON).get(person, {})


def test_monday_of_wednesday():
    assert w.monday_of(dt.date(2026, 10, 21)) == MON
    assert w.monday_of(MON) == MON


def test_task_spreads_evenly_over_weekdays():
    t = task(pic_estimation=10, pic_start_date="2026-10-19", pic_due_date="2026-10-23")
    assert list(week("A", [t]).values()) == [2.0] * 5


def test_weekend_days_get_nothing_and_task_spanning_a_weekend_counts_weekdays_only():
    t = task(pic_estimation=6, pic_start_date="2026-10-22", pic_due_date="2026-10-27")   # Thu Fri Sat Sun Mon Tue
    h = week("A", [t])
    assert h[dt.date(2026, 10, 22)] == 1.5 and h[dt.date(2026, 10, 23)] == 1.5      # 4 weekdays share 6h
    assert h[dt.date(2026, 10, 19)] == 0 and len(h) == 5


def test_remaining_hours_subtract_tracked():
    t = task(pic_estimation=8, pic_time_tracked=2, pic_start_date="2026-10-19", pic_due_date="2026-10-19")
    assert week("A", [t])[MON] == 6.0


def test_estimate_falls_back_to_legacy_then_seven():
    legacy = task(estimations=3, pic_start_date="2026-10-19", pic_due_date="2026-10-19")
    none = task(pic_start_date="2026-10-19", pic_due_date="2026-10-19")
    assert week("A", [legacy])[MON] == 3.0 and week("A", [none])[MON] == 7.0


def test_active_phase_follows_status():
    t = task(status="Peer Review", pic_estimation=10, peer_reviewer_id="B",
             pic_start_date="2026-10-19", pic_due_date="2026-10-19",
             peer_review_start_date="2026-10-20", peer_review_due_date="2026-10-20")
    out = w.daily_hours([t], MON)
    assert "A" not in out                              # PIC phase is over: status moved past it
    assert out["B"][dt.date(2026, 10, 20)] == 2.0     # peer review defaults to 20% of the PIC estimate


def test_future_phases_are_loaded_while_pic_works():
    t = task(status="In Progress", pic_estimation=10, qa_qc_id="Q", publisher_id="P",
             pic_start_date="2026-10-19", pic_due_date="2026-10-19",
             qa_qc_start_date="2026-10-21", qa_qc_due_date="2026-10-21",
             publish_start_date="2026-10-22", publish_due_date="2026-10-22")
    out = w.daily_hours([t], MON)
    assert out["Q"][dt.date(2026, 10, 21)] == 2.0
    assert out["P"][dt.date(2026, 10, 22)] == 0.25    # publish defaults to min(10% of estimate, 0.25h)


def test_done_tasks_are_ignored():
    t = task(status="DONE (published/Deployed)", pic_estimation=8, pic_start_date="2026-10-19", pic_due_date="2026-10-19")
    assert w.daily_hours([t], MON) == {}


def test_task_without_estimate_dates_or_with_all_time_tracked_is_skipped():
    assert w.daily_hours([task(pic_estimation=8)], MON) == {}                       # no dates
    done = task(pic_estimation=4, pic_time_tracked=5, pic_start_date="2026-10-19", pic_due_date="2026-10-19")
    assert w.daily_hours([done], MON) == {}                                          # nothing left
    weekend = task(pic_estimation=4, pic_start_date="2026-10-24", pic_due_date="2026-10-25")
    assert w.daily_hours([weekend], MON) == {}


def test_single_date_is_used_for_both_ends():
    t = task(pic_estimation=4, pic_due_date="2026-10-21")
    assert week("A", [t])[dt.date(2026, 10, 21)] == 4.0


def test_timestamps_are_read_in_vietnam_time():
    # 18:00 UTC on Mon is already Tuesday morning in Ho Chi Minh City (UTC+7)
    t = task(pic_estimation=4, pic_start_date=dt.datetime(2026, 10, 19, 18, 0, tzinfo=dt.timezone.utc),
             pic_due_date=dt.datetime(2026, 10, 19, 18, 0, tzinfo=dt.timezone.utc))
    assert week("A", [t])[dt.date(2026, 10, 20)] == 4.0


def test_bubble_status_thresholds():
    assert w.bubble_status(0, 7) == "none"
    assert w.bubble_status(6.9, 7) == "under"
    assert w.bubble_status(7, 7) == "optimal"
    assert w.bubble_status(7.5, 7) == "over"
    assert w.bubble_status(5, 4) == "over"
    assert w.bubble_status(7, 0) == "optimal" and w.bubble_status(7, None) == "optimal"   # no expectation: default 7h
