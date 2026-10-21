# am_web.py — API behind the "AM report" page: settings, generate (data + workload pictures), export (.docx).
# Reads SD Friday through sdf.py (read-only). Nothing here writes to SD Friday, and no error detail from the
# database is ever sent to the browser (it could contain the host or login).
import datetime as dt
import glob
import logging
import os
import re
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import am_bullets, am_docx, am_settings, sdf, workload, workload_pic
from auth_web import require_user

OUT_DIR = os.path.join("out", "am-report")
MAX_ANSWER = 5000
NAME_RE = re.compile(r"^[a-z0-9-]+\.png$")
log = logging.getLogger("am_web")

router = APIRouter(prefix="/api/am-report", dependencies=[Depends(require_user)])


class ReportData(BaseModel):
    submitter: str = ""
    reviewer: str = ""
    date_text: str = ""
    dev_pictures: list[str] = []
    seo_pictures: list[str] = []
    last_week: list[str] = []
    this_week: list[str] = []
    blockers: list[str] = []
    answers: dict[str, str] = {}           # typed answers by prompt key (see am_template.json)


class GenerateIn(BaseModel):
    week: str


class ExportIn(BaseModel):
    week_start: str
    data: ReportData


def _monday(value: str) -> dt.date:
    try:
        return workload.monday_of(dt.date.fromisoformat(value))
    except ValueError:
        raise HTTPException(400, "Week must be a date like 2026-10-19")


def _folder(monday: dt.date) -> str:
    return os.path.join(OUT_DIR, monday.isoformat())


@router.get("/template")
def get_template():
    return am_docx.load_template()


@router.get("/settings")
def get_settings():
    return am_settings.load()


@router.put("/settings")
def put_settings(body: dict):
    try:
        return am_settings.save(body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/generate")
def generate(body: GenerateIn):
    monday = _monday(body.week)
    try:
        people, projects = sdf.fetch_people(), sdf.fetch_projects()
        tasks = sdf.fetch_tasks(monday - dt.timedelta(days=7), monday + dt.timedelta(days=11))
    except sdf.SdfNotConfigured as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        log.error("SD Friday read failed: %s", type(e).__name__)      # type only: the message may name the host
        raise HTTPException(502, "Could not read SD Friday. Check the connection and try again.")

    settings = am_settings.load()
    folder = _folder(monday)
    os.makedirs(folder, exist_ok=True)
    for stale in glob.glob(os.path.join(folder, "*.png")):
        os.remove(stale)
    version = time.time_ns()                  # new picture URLs on every run, so the browser never shows a stale PNG
    weeks = {"this": monday, "next": monday + dt.timedelta(days=7)}
    hours = {k: workload.daily_hours(tasks, d) for k, d in weeks.items()}
    names = {"dev_pictures": [], "seo_pictures": []}
    pictures, warnings, idle = [], [], []
    for section, key, roster in (("dev", "dev_pictures", settings["dev_roster"]), ("seo", "seo_pictures", settings["seo_roster"])):
        matched, missing = am_bullets.match_roster(roster, people)
        warnings += [f"{n} was not found in SD Friday, so there is no picture for them." for n in missing]
        for i, person in enumerate(matched, 1):
            for which, label in (("this", "this week"), ("next", "next week")):
                days = hours[which].get(person["id"]) or {weeks[which] + dt.timedelta(days=n): 0.0 for n in range(5)}
                fname = f"{section}-{i}-{which}.png"
                workload_pic.render_row(person["name"], person["expected_hours"], days, os.path.join(folder, fname), caption=label)
                names[key].append(fname)
                pictures.append({"section": section, "person": person["name"], "week": which, "name": fname,
                                 "url": f"/api/am-report/pictures/{monday.isoformat()}/{fname}?v={version}"})
            if not hours["next"].get(person["id"]):
                idle.append(person["name"])
    last_week, this_week = am_bullets.client_bullets(tasks, projects, monday)
    data = {"submitter": settings["submitter"], "reviewer": settings["reviewer"],
            "date_text": (monday + dt.timedelta(days=4)).strftime("%d/%m/%y"), **names,
            "last_week": last_week, "this_week": this_week, "blockers": am_bullets.blockers(tasks, projects)}
    return {"week_start": monday.isoformat(), "data": data, "pictures": pictures,
            "blank": am_docx.blank_prompts(data), "warnings": warnings, "idle": idle}


@router.get("/pictures/{week}/{name}")
def get_picture(week: str, name: str):
    try:
        monday = dt.date.fromisoformat(week)
    except ValueError:
        raise HTTPException(404, "Unknown picture")
    path = os.path.join(_folder(monday), name)
    if monday.isoformat() != week or not NAME_RE.match(name) or not os.path.isfile(path):
        raise HTTPException(404, "Unknown picture")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/export")
def export(body: ExportIn):
    monday = _monday(body.week_start)
    data = body.data.model_dump()
    keys = {i["key"] for sec in am_docx.load_template()["sections"] for sub in sec["subsections"] for i in sub["items"]}
    if any(k not in keys or len(v) > MAX_ANSWER for k, v in data["answers"].items()):
        raise HTTPException(400, f"Answers must belong to a report question and be under {MAX_ANSWER} characters.")
    for key in ("dev_pictures", "seo_pictures"):
        paths = []
        for name in data[key]:
            path = os.path.join(_folder(monday), name)
            if not NAME_RE.match(name) or not os.path.isfile(path):
                raise HTTPException(400, "Unknown picture. Generate the report again.")
            paths.append(path)
        data[key] = paths
    out = os.path.join(OUT_DIR, f"Account Manager Report {(monday + dt.timedelta(days=4)).strftime('%d.%m')}.docx")
    am_docx.build(out, data)
    return FileResponse(out, filename=os.path.basename(out),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
