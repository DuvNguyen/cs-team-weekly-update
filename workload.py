# workload.py — per-person daily hours for one week, ported from SD Friday so our pictures match its grid.
# Source: digital-timesheet app/api/workload/tasks/route.ts (which role's phase is "on the board" for a task)
# and components/workload/WorkloadChart.tsx (hours left spread evenly over a phase's weekdays), lib/utils/workload-filter.ts.
import datetime as dt
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")          # SD Friday is used in Vietnam; timestamps are read in this zone
DONE = "DONE (published/Deployed)"
PEER_STATUSES = ("Ready for Peer Review", "Peer Review")
QA_STATUSES = ("Ready for QAQC", "Testing")
PUBLISH_STATUSES = ("Ready to Publish/Deploy", "Publishing/Deployment")


def monday_of(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def day_of(v) -> dt.date | None:
    if v is None or v == "":
        return None
    if isinstance(v, str):
        v = dt.datetime.fromisoformat(v.replace("Z", "+00:00")) if "T" in v or " " in v else dt.date.fromisoformat(v)
    if isinstance(v, dt.datetime):
        return (v.astimezone(VN) if v.tzinfo else v).date()
    return v


def _active(status: str, names) -> bool:
    s = status.lower()
    return any(n.lower() in s for n in names)


def _instances(t: dict):
    """The (person, start, end, hours left) rows SD Friday's workload grid builds from one task."""
    status = t.get("status") or ""
    if status == DONE:
        return
    peer, qa, pub = _active(status, PEER_STATUSES), _active(status, QA_STATUSES), _active(status, PUBLISH_STATUSES)
    num = lambda k: float(t.get(k) or 0)                 # Postgres numerics arrive as Decimal
    est = num("pic_estimation") or num("estimations") or 7
    tracked = num
    rows = []
    if t.get("pic_id") and not (peer or qa or pub):
        rows.append((t["pic_id"], "pic", est, tracked("pic_time_tracked")))
    if t.get("peer_reviewer_id") and not (qa or pub):
        rows.append((t["peer_reviewer_id"], "peer_review", num("peer_review_estimation") or est * 0.2, tracked("peer_review_time_tracked")))
    if t.get("qa_qc_id") and not pub:
        rows.append((t["qa_qc_id"], "qa_qc", num("qa_qc_estimation") or est * 0.2, tracked("qa_qc_time_tracked")))
    if t.get("publisher_id"):
        rows.append((t["publisher_id"], "publish", num("publish_estimation") or min(est * 0.1, 0.25), tracked("publish_time_tracked")))
    for person, phase, estimate, done in rows:
        start, due = day_of(t.get(f"{phase}_start_date")), day_of(t.get(f"{phase}_due_date"))
        start, end = start or due, due or start
        if start and end:
            yield str(person), start, end, max(0, estimate - done)


def daily_hours(tasks: list[dict], week_start: dt.date) -> dict[str, dict[dt.date, float]]:
    """person id -> {Mon..Fri date: hours}. People with no hours that week are left out."""
    week_start = monday_of(week_start)
    days = [week_start + dt.timedelta(days=i) for i in range(5)]
    out: dict[str, dict[dt.date, float]] = {}
    for t in tasks:
        for person, start, end, left in _instances(t):
            span = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
            weekdays = [d for d in span if d.weekday() < 5]
            if left <= 0 or not weekdays:
                continue
            per_day = left / len(weekdays)
            for d in days:
                if start <= d <= end:
                    out.setdefault(person, {k: 0.0 for k in days})[d] += per_day
    return out


def bubble_status(hours: float, expected: float | None) -> str:
    """none (grey) / under (blue) / optimal (green) / over (red), as in SD Friday's grid."""
    if not hours:
        return "none"
    h, e = round(float(hours), 6), round(float(expected or 7), 6)
    return "under" if h < e else "optimal" if h == e else "over"
