import datetime as dt
import pytest

import sdf


class FakeCursor:
    def __init__(self, conn, rows):
        self.conn, self.rows = conn, rows

    def execute(self, sql, params=None):
        self.conn.statements.append(sql)
        self.conn.params.append(params)
        return self

    def fetchall(self):
        return self.rows


class FakeConn:
    def __init__(self, rows):
        self.rows, self.statements, self.params = rows, [], []

    def cursor(self, **kw):
        return FakeCursor(self, self.rows)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def conn(monkeypatch):
    holder = {}
    def make(rows):
        holder["c"] = FakeConn(rows)
        monkeypatch.setattr(sdf, "_connect", lambda: holder["c"])
        return holder["c"]
    return make


def test_missing_url_raises_not_configured(monkeypatch):
    monkeypatch.delenv("SDF_READONLY_DB_URL", raising=False)
    monkeypatch.setattr(sdf, "load_dotenv", lambda *a, **k: None)
    with pytest.raises(sdf.SdfNotConfigured):
        sdf._connect()


def test_queries_are_selects_only(conn):
    c = conn([])
    sdf.fetch_tasks(dt.date(2026, 10, 19), dt.date(2026, 10, 23))
    sdf.fetch_people()
    sdf.fetch_projects()
    assert c.statements and all(s.lstrip().lower().startswith("select") for s in c.statements)


def test_person_name_prefers_full_name_then_sheet_name(conn):
    conn([
        {"id": "1", "full_name": "Le Minh Tri", "sheet_name": "Tri", "department": "DEV", "role": "employee", "expected_hours": 4},
        {"id": "2", "full_name": None, "sheet_name": "Vi", "department": None, "role": "employee", "expected_hours": None},
    ])
    people = sdf.fetch_people()
    assert [p["name"] for p in people] == ["Le Minh Tri", "Vi"]
    assert people[1]["expected_hours"] == 7           # null falls back to SD Friday's default


def test_people_never_include_email(conn):
    conn([{"id": "1", "full_name": "A", "sheet_name": None, "department": "SEO", "role": "x", "expected_hours": 7, "email": "a@b.c"}])
    assert all("email" not in p for p in sdf.fetch_people())


def test_projects_maps_id_to_name(conn):
    conn([{"id": "p1", "name": "Kenno"}])
    assert sdf.fetch_projects() == {"p1": "Kenno"}


def test_legacy_text_columns_get_text_params(conn):
    # `timeline` / `due_date` are text columns in SD Friday, so they must be compared with ISO strings.
    c = conn([])
    sdf.fetch_tasks(dt.date(2026, 10, 19), dt.date(2026, 10, 23))
    p = c.params[0]
    assert isinstance(p["start_s"], str) and isinstance(p["end_s"], str)
    assert p["end_s"].startswith("2026-10-23T23:59")
    assert "timeline <= %(end_s)s" in c.statements[0]


def test_expected_hours_are_floats_even_when_postgres_returns_decimals(conn):
    from decimal import Decimal
    conn([{"id": "1", "full_name": "A", "sheet_name": None, "department": None, "role": "x", "expected_hours": Decimal("4.5")}])
    assert isinstance(sdf.fetch_people()[0]["expected_hours"], float)
