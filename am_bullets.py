# am_bullets.py — turns SD Friday task rows into the report's client bullets, blockers and roster matching.
# Status groups follow SD Friday's docs/account-manager-weekly-updates-spec.md. Pure functions, no I/O.
import datetime as dt
import unicodedata

from workload import day_of, monday_of

GROUPS = {"Task Definition": "Planned", "Ready for Execution": "Planned",
          "In Progress": "In Progress", "On Hold/Paused": "In Progress",
          "Peer Review": "QA", "Ready for Peer Review": "QA", "Testing": "QA", "Ready for QAQC": "QA", "Needs Revision": "QA",
          "DONE (published/Deployed)": "Completed"}
ORDER = ("Completed", "QA", "In Progress", "Planned")
LABELS = {"Completed": "completed", "QA": "in QA", "In Progress": "in progress", "Planned": "planned"}
SHOWN = 3
BLOCKED = ("Stuck", "On Hold/Paused")


def status_group(status: str) -> str:
    return GROUPS.get(status, "In Progress")          # Stuck, publishing and unknown statuses count as in progress


def _in_week(task: dict, monday: dt.date) -> bool:
    friday = monday + dt.timedelta(days=4)
    for phase in ("pic", "peer_review", "qa_qc", "publish"):
        start, due = day_of(task.get(f"{phase}_start_date")), day_of(task.get(f"{phase}_due_date"))
        start, end = start or due, due or start
        if start and end and start <= friday and end >= monday:
            return True
    return False


def _week_lines(tasks: list[dict], projects: dict[str, str], monday: dt.date) -> list[str]:
    by_project: dict[str, dict[str, list[str]]] = {}
    for t in tasks:
        if _in_week(t, monday):
            name = projects.get(str(t.get("project_id")), "Unknown project")
            by_project.setdefault(name, {g: [] for g in ORDER})[status_group(t.get("status") or "")].append(t.get("name") or "Untitled task")
    lines = []
    for project in sorted(by_project):
        groups = by_project[project]
        counts = ", ".join(f"{len(groups[g])} {LABELS[g]}" for g in ORDER if groups[g])
        names = [n for g in ORDER for n in groups[g]]
        shown = "; ".join(names[:SHOWN]) + (f"; +{len(names) - SHOWN} more" if len(names) > SHOWN else "")
        lines.append(f"{project}: {counts} ({shown})")
    return lines


def client_bullets(tasks: list[dict], projects: dict[str, str], week_start: dt.date) -> tuple[list[str], list[str]]:
    """(last week's lines, this week's lines): one line per project that had tasks that week."""
    monday = monday_of(week_start)
    return _week_lines(tasks, projects, monday - dt.timedelta(days=7)), _week_lines(tasks, projects, monday)


def blockers(tasks: list[dict], projects: dict[str, str]) -> list[str]:
    rows = [(projects.get(str(t.get("project_id")), "Unknown project"), t.get("name") or "Untitled task", t["status"])
            for t in tasks if t.get("status") in BLOCKED]
    return [f"{name} ({project}): {status}" for project, name, status in sorted(rows)]


def _norm(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    return " ".join("".join(c for c in plain if not unicodedata.combining(c)).casefold().split())


def match_roster(roster: list[str], people: list[dict]) -> tuple[list[dict], list[str]]:
    """People for the names in a roster (in roster order), plus the names nobody matched."""
    index = {_norm(p["name"]): p for p in people if p.get("name")}
    matched = [index[_norm(n)] for n in roster if _norm(n) in index]
    return matched, [n for n in roster if _norm(n) not in index]
