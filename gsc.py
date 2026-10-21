import datetime

def _fmt_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.month}/{d.day}/{d.strftime('%y')}"

def parse(rows: list) -> dict:
    dates, clicks, impressions = [], [], []
    for r in rows:
        dates.append(_fmt_date(r["keys"][0]))
        clicks.append(int(r["clicks"]))
        impressions.append(int(r["impressions"]))
    tot_c, tot_i = sum(clicks), sum(impressions)
    ctr = (tot_c / tot_i * 100) if tot_i else 0.0
    # impression-weighted average position
    if tot_i:
        pos = sum(r["position"] * r["impressions"] for r in rows) / tot_i
    else:
        pos = 0.0
    return {
        "dates": dates, "clicks": clicks, "impressions": impressions,
        "totals": {"clicks": tot_c, "impressions": tot_i,
                   "ctr": f"{ctr:.1f}%", "position": f"{pos:.1f}"},
    }

def fetch(service, property_url: str, start, end) -> dict:
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["date"],
        "type": "web",
        "rowLimit": 100,
    }
    resp = service.searchanalytics().query(siteUrl=property_url, body=body).execute()
    return parse(resp.get("rows", []))
