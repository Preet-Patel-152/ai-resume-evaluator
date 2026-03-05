from fastapi import BackgroundTasks, Request, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import hashlib
import json
import os

# Load env from backend/.env FIRST, before any service that reads env vars
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .services.pdf_parser import extract_text_from_pdf_bytes
from .services.resume_grader import grade_resume_against_job
from .services.scoring_engine import score_resume
from .services.analytics import log_event
from .middleware.redis_rate_limiter import RedisRateLimiter
from .services.redis_client import get_redis


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf'}
MAX_RESUME_TEXT_LENGTH = 50_000   # ~10 pages
MAX_JOB_DESC_LENGTH = 20_000

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

redis = get_redis()

rate_limiter = RedisRateLimiter(
    redis=redis,
    max_requests=int(os.getenv("RATE_LIMIT_MAX", "10")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "3600")),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    yield


ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "development":
    allowed_origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5501",
    ]
else:
    origin = os.getenv("ALLOWED_ORIGIN", "")
    allowed_origins = [origin] if origin else []

app = FastAPI(
    title="Resume AI Service",
    version="1.0.0",
    description="Resume Grading + PDF Upload",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------
# Frontend
# ---------------------------

@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "resume_front.html")


# ---------------------------
# Health + Stats
# ---------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
async def get_stats():
    try:
        total = await redis.get("stats:total_requests")
        unique = await redis.pfcount("stats:unique_ips")
        per_ip = await redis.hgetall("stats:per_ip")
    except Exception:
        raise HTTPException(status_code=503, detail="Stats unavailable")

    top_users = sorted(per_ip.items(), key=lambda x: int(x[1]), reverse=True)

    return {
        "total_requests": int(total) if total else 0,
        "unique_visitors": unique,
        "top_users": [{"id": k, "uses": int(v)} for k, v in top_users],
    }


# ---------------------------
# Pydantic Models
# ---------------------------

class MatchRequest(BaseModel):
    job_description: str
    resume_text: str


@app.post("/grade_resume/")
async def grade_resume(http_request: Request, request: MatchRequest):
    await rate_limiter.check_rate_limit(http_request)

    if len(request.job_description) > MAX_JOB_DESC_LENGTH:
        raise HTTPException(status_code=400, detail="Job description too long.")

    cache_key = "llm_cache:" + hashlib.md5(
        (request.job_description + "||" + request.resume_text).encode()
    ).hexdigest()

    evaluation = None
    try:
        cached = await redis.get(cache_key)
        if cached:
            evaluation = json.loads(cached)
    except Exception:
        pass

    if evaluation is None:
        evaluation = grade_resume_against_job(
            job_description=request.job_description,
            resume_text=request.resume_text,
        )
        try:
            await redis.set(cache_key, json.dumps(evaluation), ex=86400)
        except Exception:
            pass

    keyword_score = score_resume(request.resume_text, request.job_description)
    return {"evaluation": evaluation, "keyword_score": keyword_score}


# ---------------------------
# PDF Upload Endpoint
# ---------------------------

@app.post("/grade_resume_pdf/")
async def grade_resume_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(...),
):
    await rate_limiter.check_rate_limit(request)

    background_tasks.add_task(
        log_event,
        "resume_analysis",
        request.client.host if request.client else None,
        redis,
    )

    if len(job_description) > MAX_JOB_DESC_LENGTH:
        raise HTTPException(status_code=400, detail="Job description too long.")

    if not resume_pdf.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(resume_pdf.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    chunks: list[bytes] = []

    while True:
        chunk = await resume_pdf.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        chunks.append(chunk)

    pdf_bytes = b"".join(chunks)

    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF.")

    resume_text = extract_text_from_pdf_bytes(pdf_bytes)

    if len(resume_text) > MAX_RESUME_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Resume text too long. Please submit a concise resume.")

    cache_key = "llm_cache:" + hashlib.md5(
        (job_description + "||" + resume_text).encode()
    ).hexdigest()

    evaluation = None
    try:
        cached = await redis.get(cache_key)
        if cached:
            evaluation = json.loads(cached)
    except Exception:
        pass

    if evaluation is None:
        evaluation = grade_resume_against_job(job_description, resume_text)
        try:
            await redis.set(cache_key, json.dumps(evaluation), ex=86400)
        except Exception:
            pass

    keyword_score = score_resume(resume_text, job_description)

    return {
        "evaluation": evaluation,
        "keyword_score": keyword_score,
        "resume_preview": resume_text[:800],
    }


# ---------------------------
# Static files (must be last)
# ---------------------------

app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
