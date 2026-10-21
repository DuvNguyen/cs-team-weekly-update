# sdf.py — read-only window onto SD Friday's database (Supabase Postgres).
# Connects as the `wut_readonly` role from SDF_READONLY_DB_URL (.env). Fixed SELECTs only, no user text in SQL.
import datetime as dt
import os
from dotenv import load_dotenv


class SdfNotConfigured(Exception):
    """SDF_READONLY_DB_URL is missing."""


def _connect():
    load_dotenv()
    url = os.environ.get("SDF_READONLY_DB_URL", "")
    if not url:
        raise SdfNotConfigured("SD Friday isn't connected. Add SDF_READONLY_DB_URL to .env.")
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(url, connect_timeout=10, row_factory=dict_row)


# Phase columns are the ones SD Friday's own workload route reads (app/api/workload/tasks/route.ts).
_TASK_COLS = ("id, name, status, project_id, assigned_to, reviewer_id, pic_id, peer_reviewer_id, qa_qc_id, publisher_id, "
              "estimations, pic_estimation, peer_review_estimation, qa_qc_estimation, publish_estimation, "
              "pic_time_tracked, peer_review_time_tracked, qa_qc_time_tracked, publish_time_tracked, "
              "timeline, due_date, pic_start_date, pic_due_date, peer_review_start_date, peer_review_due_date, "
              "qa_qc_start_date, qa_qc_due_date, publish_start_date, publish_due_date")
_PHASES = ("pic", "peer_review", "qa_qc", "publish")
_OVERLAP = " or ".join(f"({p}_start_date <= %(end)s and ({p}_due_date >= %(start)s or {p}_due_date is null))" for p in _PHASES)
_TASKS_SQL = (f"select {_TASK_COLS} from public.tasks where is_deleted = false and ({_OVERLAP} "
              "or (timeline <= %(end_s)s and (due_date >= %(start_s)s or due_date is null)))")   # legacy text columns


def _rows(sql: str, params: dict | None = None) -> list[dict]:
    with _connect() as conn:
        return list(conn.cursor().execute(sql, params).fetchall())


def fetch_tasks(start: dt.date, end: dt.date) -> list[dict]:
    """Tasks with any phase overlapping start..end (inclusive of the whole end day)."""
    end_ts = dt.datetime.combine(end, dt.time.max)
    return _rows(_TASKS_SQL, {"start": start, "end": end_ts, "start_s": start.isoformat(), "end_s": end_ts.isoformat()})


def fetch_people() -> list[dict]:
    rows = _rows("select id, full_name, sheet_name, department, role, expected_hours from public.profiles where is_active = true")
    return [{"id": str(r["id"]), "name": r["full_name"] or r["sheet_name"] or "", "department": r["department"],
             "role": r["role"], "expected_hours": r["expected_hours"] or 7} for r in rows]


def fetch_projects() -> dict[str, str]:
    return {str(r["id"]): r["name"] for r in _rows("select id, name from public.projects")}
