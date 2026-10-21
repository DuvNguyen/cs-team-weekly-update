# server.py — HTTP API for the Next.js UI.   Run:  .venv/bin/uvicorn server:app --port 8000
import threading
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
import auth_web, pipeline, settings_web, voice_store
from auth_web import require_user

app = FastAPI(title="Weekly update tool")
api = APIRouter(dependencies=[Depends(require_user)])      # every route here needs a valid session


@app.exception_handler(auth_web.NotSignedIn)
def _not_signed_in(request: Request, exc: auth_web.NotSignedIn):
    return JSONResponse({"detail": str(exc)}, status_code=401)


class ClientIn(BaseModel):
    name: str
    property: str
    category: str = ""


class JobIn(BaseModel):
    style_id: str | None = None
    tab: str = ""
    clients: list[str]
    start: str
    end: str


class ClientPatch(BaseModel):
    body: str | None = None
    include: bool | None = None


class Regen(BaseModel):
    prompt: str = ""
    style_id: str | None = None


def _job(job_id: str, user: dict) -> dict:
    job = pipeline.JOBS.get(job_id)
    if not job or job.get("_email") != (None if pipeline.DEMO else user["email"]):
        raise HTTPException(404, "Unknown job")
    return job


def _client(job: dict, name: str) -> dict:
    c = next((x for x in job["clients"] if x["name"] == name), None)
    if not c:
        raise HTTPException(404, "Unknown client")
    return c


@api.get("/api/config")
def get_config():
    return {**pipeline.public_config(), "period": pipeline.default_period()}


@api.put("/api/clients")
def put_clients(clients: list[ClientIn]):
    names = [c.name.strip() for c in clients]
    if any(not n for n in names) or len(set(names)) != len(names):
        raise HTTPException(400, "Client names must be unique and not empty")
    pipeline.save_clients([c.model_dump() for c in clients])
    return {"ok": True}


@api.get("/api/voice")
def get_voice():
    return voice_store.load()


@api.put("/api/voice")
def put_voice(body: dict):
    try:
        return voice_store.save(body)
    except ValueError as e:
        raise HTTPException(400, str(e))


class AnalyzeIn(BaseModel):
    email: str


@api.post("/api/voice/analyze")
def analyze_voice(body: AnalyzeIn):
    try:
        return pipeline.analyze_style(body.email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Could not analyse the email: {str(e).splitlines()[0][:150]}")


@api.post("/api/voice/reset")
def reset_voice():
    return voice_store.reset()


@api.get("/api/period")
def get_period(user: dict = Depends(require_user)):
    try:
        return {"end": pipeline.latest_data_date(None if pipeline.DEMO else user["email"])}
    except auth_web.NotSignedIn:
        raise
    except Exception as e:
        raise HTTPException(502, str(e).splitlines()[0][:200])


@api.get("/api/tabs")
def get_tabs(user: dict = Depends(require_user)):
    try:
        return {"tabs": pipeline.list_tabs(None if pipeline.DEMO else user["email"])}
    except auth_web.NotSignedIn:
        raise
    except Exception as e:
        raise HTTPException(502, f"Could not read the SEO sheet: {str(e).splitlines()[0][:150]}")


@api.post("/api/jobs")
def create_job(body: JobIn, user: dict = Depends(require_user)):
    known = {c["name"] for c in pipeline.load_config()["clients"]}
    if not body.clients or any(n not in known for n in body.clients):
        raise HTTPException(400, "Pick at least one known client")
    return pipeline.view(pipeline.new_job(body.tab, body.clients, body.start, body.end, None if pipeline.DEMO else user["email"], body.style_id))


@api.get("/api/jobs/{job_id}")
def get_job(job_id: str, user: dict = Depends(require_user)):
    return pipeline.view(_job(job_id, user))


@api.get("/api/jobs/{job_id}/chart/{name}")
def get_chart(job_id: str, name: str, user: dict = Depends(require_user)):
    job = _job(job_id, user)
    _client(job, name)
    return FileResponse(pipeline.chart_path(job, name), media_type="image/png")


@api.patch("/api/jobs/{job_id}/clients/{name}")
def patch_client(job_id: str, name: str, patch: ClientPatch, user: dict = Depends(require_user)):
    c = _client(_job(job_id, user), name)
    if patch.body is not None:
        c["body"] = patch.body
    if patch.include is not None:
        c["include"] = patch.include
    return c


@api.post("/api/jobs/{job_id}/clients/{name}/retry")
def retry(job_id: str, name: str, user: dict = Depends(require_user)):
    job = _job(job_id, user)
    c = _client(job, name)
    c["status"] = "running"
    threading.Thread(target=pipeline.retry_client, args=(job, name), daemon=True).start()
    return c


@api.post("/api/jobs/{job_id}/clients/{name}/regenerate")
def regenerate(job_id: str, name: str, body: Regen, user: dict = Depends(require_user)):
    job = _job(job_id, user)
    c = _client(job, name)
    try:
        pipeline.regenerate_client(job, name, body.prompt, body.style_id)
    except auth_web.NotSignedIn:
        raise
    except Exception as e:
        raise HTTPException(502, str(e).splitlines()[0][:200])
    return c


@api.post("/api/jobs/{job_id}/publish")
def publish(job_id: str, user: dict = Depends(require_user)):
    job = _job(job_id, user)
    if job["status"] not in ("ready", "done"):
        raise HTTPException(409, "Report is not ready to publish")
    try:
        return {"doc_url": pipeline.publish(job)}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except auth_web.NotSignedIn:
        raise
    except Exception as e:
        raise HTTPException(502, f"Publish failed: {str(e).splitlines()[0][:200]}")


@api.post("/api/jobs/{job_id}/export")
def export(job_id: str, user: dict = Depends(require_user)):
    job = _job(job_id, user)
    if job["status"] not in ("ready", "done"):
        raise HTTPException(409, "Report is not ready to export")
    try:
        data, filename = pipeline.export_docx(job)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


app.include_router(auth_web.router)
app.include_router(settings_web.router)
app.include_router(api)
