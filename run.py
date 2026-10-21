# run.py
import datetime, json, os, sys, time, webbrowser
import dates, gsc, chart, updates, report, auth, trends

def log(msg="", end="\n"):
    print(msg, end=end, flush=True)   # flush so progress shows live, not buffered to the end

def main():
    t0 = time.time()
    with open("config.json") as f:
        config = json.load(f)

    log("Starting bi-weekly SEO report…")
    log("(first run only: a browser opens — log in as developers@ and click Allow)")
    svc = auth.get_services(config)

    start, fri = dates.report_period(datetime.date.today())
    pstart, pfri = dates.prev_period(start)
    title = f"Bi-weekly SEO Report — {start.isoformat()} to {fri.isoformat()}"
    os.makedirs("out", exist_ok=True)

    clients = config["clients"]
    n = len(clients)
    log(f"\n{title}")
    log(f"{n} clients · comparing vs {pstart.isoformat()} to {pfri.isoformat()}")

    # The SEO sheet has one tab per 2-week period. The PM sets the current tab
    # name in config.json ("seo_sheet_tab"). Blank/missing -> run chart-only.
    sheet_rows = []
    sheet_id = config.get("seo_sheet_id", "")
    tab = config.get("seo_sheet_tab", "").strip()
    if sheet_id and not sheet_id.startswith("PASTE") and tab:
        try:
            sheet_rows = updates.fetch_rows(svc["sheets"], sheet_id, f"'{tab}'!A1:C300")
            log(f"SEO sheet: tab '{tab}' — {len(sheet_rows)} rows")
        except Exception as e:
            log(f"SEO sheet: tab '{tab}' not found — running chart-only. ({str(e).splitlines()[0][:80]})")
    else:
        log("SEO sheet: no tab set ('seo_sheet_tab' in config.json) — running chart-only.")
    log("")

    # One trend note per unique category (clients sharing a category share the note).
    # A note written by hand in config "category_trends" wins; otherwise ask Gemini with
    # Google Search grounding (needs a key with grounding quota — silently skipped if not).
    trend_cache = {}
    if config.get("include_industry_trends", True):
        manual = config.get("category_trends", {})
        cats = sorted({c["category"] for c in clients if c.get("category")})
        if cats:
            log(f"Industry trends for {len(cats)} categories…")
            for cat in cats:
                if manual.get(cat):
                    trend_cache[cat] = (manual[cat], [])
                    log(f"  ✓ {cat} (from config)")
                else:
                    trend_cache[cat] = trends.for_category(svc["gemini"], cat, report.MODEL)
                    log(f"  {'✓' if trend_cache[cat][0] else '— (no trend)'} {cat}")
            log("")

    log("Creating the Google Doc…")
    doc_id = report.create_doc(svc["docs"], svc["drive"], title, config["drive_folder_id"])

    done, skipped = 0, []
    for i, c in enumerate(clients, 1):
        name, prop = c["name"], c["property"]
        category = c.get("category", "")
        key = c.get("sheet_key", name)                 # match the sheet by sheet_key if given, else by name
        log(f"[{i:>2}/{n}] {name} … ", end="")
        try:
            series = gsc.fetch(svc["webmasters"], prop, start, fri)
            prev = gsc.fetch(svc["webmasters"], prop, pstart, pfri)
            png = chart.render(series, f"{name} — {prop}", f"out/{name}.png")
            this_week, next_week = updates.match(sheet_rows, key)
            # PM's wording in config wins over the sheet (sheet often says "No task")
            this_week = c.get("this_week", this_week)
            next_week = c.get("next_week", next_week)
            summary = report.summarize(svc["gemini"], name, category, series, prev, this_week, next_week)
            trend, trend_sources = trend_cache.get(category, ("", []))
            body = report.compose_body(summary, this_week, next_week, category, trend, trend_sources)
            report.append_client(svc["docs"], svc["drive"], doc_id, name, png, body,
                                 config["drive_folder_id"], category)
            done += 1
            t = series["totals"]
            tag = "  +update" if (this_week or next_week) else ""
            log(f"✓ {t['clicks']:,} clicks, {t['impressions']:,} impressions{tag}")
        except Exception as e:
            short = str(e).splitlines()[0][:90]
            skipped.append((name, str(e)))
            try:
                report.append_client(svc["docs"], svc["drive"], doc_id, name,
                                     chart.render({"dates": [], "clicks": [], "impressions": [],
                                                   "totals": {"clicks": 0, "impressions": 0,
                                                              "ctr": "0.0%", "position": "0"}},
                                                  f"{name} — {prop}", f"out/{name}.png"),
                                     f"⚠ Data unavailable this period ({e}).", config["drive_folder_id"], category)
                log(f"⚠ skipped ({short})")
            except Exception:
                log(f"⚠ skipped, could not annotate ({short})")

    url = report.doc_url(doc_id)
    secs = int(time.time() - t0)
    log(f"\nDone in {secs // 60}m {secs % 60}s — {done} built, {len(skipped)} skipped.")
    if skipped:
        log("Skipped: " + ", ".join(name for name, _ in skipped))
        if any("403" in e for _, e in skipped):
            log("Tip: 403 = wrong property string. Run  ./venv/bin/python list_sites.py  for the exact values.")
    log(f"\nReport: {url}")
    log("(opening it in your browser…)")
    webbrowser.open(url)

if __name__ == "__main__":
    sys.exit(main())
