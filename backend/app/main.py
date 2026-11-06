import json
import re
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import jobs, reviews
from app.agent.llm import MODEL_NAME
from app.agent.tools import DOCS_DIR
from app.db.database import SessionLocal, init_db
from app.db.models import Review, Run
from app.review_routes import router as review_router
from app.service import MODEL_DISPLAY_NAME, verify_answer, verify_question

MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2 MB per document
MAX_CONTENT_CHARS = 200_000


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # create the tables if they do not exist yet
    yield


app = FastAPI(title="TruthGuard API", lifespan=lifespan)

# Allow the React dev page (localhost:5173) to call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(review_router)


def _iso(dt) -> str:
    return dt.isoformat() + "Z" if dt else ""


def _ollama_status() -> dict:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        r.raise_for_status()
        names = [m["name"] for m in r.json().get("models", [])]
        installed = any(n.startswith(MODEL_NAME) for n in names)
        return {"up": True, "model": MODEL_DISPLAY_NAME, "model_installed": installed}
    except Exception:
        return {"up": False, "model": MODEL_DISPLAY_NAME, "model_installed": False}


def _source_files() -> list:
    return sorted(DOCS_DIR.glob("*.txt")) if DOCS_DIR.exists() else []


def _source_info(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    stat = path.stat()
    return {
        "id": path.name,
        "name": path.name,
        "type": "TXT",
        "size": stat.st_size,
        "chunks": len([b for b in text.split("\n\n") if b.strip()]),   # paragraphs
        "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
        "status": "Indexed",
    }


def _source_path(name: str) -> Path:
    clean = Path(name).name
    path = DOCS_DIR / clean
    if clean != name or not path.is_file():
        raise HTTPException(status_code=404, detail="Source not found")
    return path


class VerifyAnswerRequest(BaseModel):
    question: str = Field(default="", max_length=1000)
    answer: str = Field(min_length=1, max_length=5000)


class VerifyQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


# ---------- Status ----------
@app.get("/api/status")
def status():
    with SessionLocal() as session:
        runs = session.query(Run).count()
    return {"api": "ok", "ollama": _ollama_status(), "documents": len(_source_files()), "runs": runs}


# ---------- Knowledge sources (documents) ----------
@app.get("/api/sources")
def list_sources():
    return [_source_info(p) for p in _source_files()]


@app.post("/api/sources")
async def upload_source(file: UploadFile = File(...)):
    raw_name = Path(file.filename or "").name            # drop any folder part
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", raw_name)
    if not safe.lower().endswith(".txt") or len(safe) <= 4 or safe.startswith("."):
        raise HTTPException(status_code=400, detail="Only .txt files are accepted")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 2 MB")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")
    if not text.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / safe                                # a file with the same name is replaced
    path.write_text(text, encoding="utf-8")
    return _source_info(path)


@app.get("/api/sources/{name}/content")
def source_content(name: str):
    path = _source_path(name)
    text = path.read_text(encoding="utf-8", errors="replace")
    return {"name": path.name, "text": text[:MAX_CONTENT_CHARS], "truncated": len(text) > MAX_CONTENT_CHARS}


@app.delete("/api/sources/{name}")
def delete_source(name: str):
    path = _source_path(name)
    path.unlink()
    return {"deleted": name}


# ---------- Verification ----------
@app.post("/api/verify/answer")
def api_verify_answer(req: VerifyAnswerRequest):
    try:
        return verify_answer(req.question, req.answer)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/verify/question")
def api_verify_question(req: VerifyQuestionRequest):
    try:
        return {"job_id": jobs.start_job(verify_question, req.question)}
    except jobs.JobBusy:
        raise HTTPException(status_code=409,
                            detail="Another verification is still running. Please wait for it to finish.")


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str):
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ---------- Runs ----------
@app.get("/api/runs")
def list_runs(limit: int = 100):
    limit = max(1, min(limit, 500))
    with SessionLocal() as session:
        rows = session.query(Run).order_by(Run.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "question": r.question,
                "answer": (r.answer or "")[:200],
                "mode": r.mode,
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "verification_score": r.verification_score,
                "created_at": _iso(r.created_at),
            }
            for r in rows
        ]


@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    with SessionLocal() as session:
        run = session.get(Run, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")
        data = json.loads(run.analysis_json) if run.analysis_json else {}
        run_reviews = (
            session.query(Review).filter(Review.run_id == run.id).order_by(Review.id).all()
        )
        release, final_answer = reviews.release_state(run, run_reviews)
        data.update({
            "id": run.id,
            "run_id": run.id,
            "created_at": _iso(run.created_at),
            "mode": run.mode,
            "model": run.model or MODEL_DISPLAY_NAME,
            "release": release,
            "final_answer": final_answer,
            "reviews": [reviews.review_json(r, run) for r in run_reviews],
        })
        return data


# ---------- Dashboard numbers ----------
@app.get("/api/stats")
def stats():
    levels = {"Safe": 0, "Warning": 0, "Critical": 0}
    claims = {"Supported": 0, "Contradicted": 0, "Insufficient evidence": 0}
    scores = []
    with SessionLocal() as session:
        total = session.query(Run).count()
        rows = session.query(Run).order_by(Run.id.desc()).limit(1000).all()
        for r in rows:
            if r.risk_level in levels:
                levels[r.risk_level] += 1
            if r.verification_score is not None:
                scores.append(r.verification_score)
            if r.analysis_json:
                try:
                    analysis = json.loads(r.analysis_json)
                except ValueError:
                    analysis = {}
                for c in analysis.get("detectors", {}).get("hallucination", {}).get("claims", []):
                    if c.get("status") in claims:
                        claims[c["status"]] += 1
        recent = [
            {"id": r.id, "question": r.question, "risk_level": r.risk_level,
             "risk_score": r.risk_score, "created_at": _iso(r.created_at)}
            for r in rows[:5]
        ]
    checkable = sum(claims.values())
    return {
        "total_checked": total,
        "by_level": levels,
        "claims": claims,
        "supported_rate": round(100 * claims["Supported"] / checkable, 1) if checkable else None,
        "avg_verification_score": round(sum(scores) / len(scores), 1) if scores else None,
        "sources": len(_source_files()),
        "pending_reviews": reviews.count_pending(),
        "recent": recent,
    }