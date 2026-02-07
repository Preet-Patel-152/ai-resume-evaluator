from fastapi import BackgroundTasks, Request, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os

from .services.pdf_parser import extract_text_from_pdf_bytes
# from .services.llm import call_chat_model
from .services.resume_grader import grade_resume_against_job
from .services.analytics import log_event
from .middleware.rate_limiter import RateLimiter


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf'}
MAX_RESUME_TEXT_LENGTH = 50_000  # ~10 pages

rate_limiter = RateLimiter(
    max_requests=10,      # 10 requests
    window_seconds=3600   # per hour
)

# Load env from backend/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "development":
    allowed_origins = [
        "http://localhost:5500",   # VS Code Live Server
        "http://127.0.0.1:5500",
        "http://localhost:3000",   # React (future)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5501"
    ]
else:
    allowed_origins = [
        "https://your-frontend-domain.com",
        "https://www.your-frontend-domain.com"
    ]

# Enable CORS for all origins (for development)
app = FastAPI(
    title="Resume AI Service",
    version="1.0.0",
    description="Chat + Resume Grading + PDF Upload"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------
# Pydantic Models
# ---------------------------


class ChatRequest(BaseModel):
    message: str


class MatchRequest(BaseModel):
    job_description: str
    resume_text: str


@app.post("/grade_resume/")
def grade_resume(request: MatchRequest):
    evaluation = grade_resume_against_job(
        job_description=request.job_description,
        resume_text=request.resume_text,
    )
    return {"evaluation": evaluation}


# ---------------------------
# PDF Upload Endpoint
# ---------------------------
@app.post("/grade_resume_pdf/")
async def grade_resume_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(...)
):
    # ---------------------------
    # Rate limiting
    # ---------------------------
    await rate_limiter.check_rate_limit(request)

    # ------------------------------------------------------------------------------------------------------------
    # Analytics (non-blocking)
    # ------------------------------------------------------------------------------------------------------------
    # background_tasks.add_task(
    #     log_event,
    #     "resume_analysis",
    #     request.client.host if request.client else None
    # )

    # ---------------------------
    # File extension validation
    # ---------------------------
    if not resume_pdf.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(resume_pdf.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # ---------------------------
    # Streamed file-size check
    # ---------------------------
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    chunks: list[bytes] = []

    while True:
        chunk = await resume_pdf.read(chunk_size)
        if not chunk:
            break

        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB."
            )

        chunks.append(chunk)

    pdf_bytes = b"".join(chunks)

    # ---------------------------
    # Magic-byte validation
    # ---------------------------
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid PDF."
        )

    # ---------------------------
    # PDF text extraction
    # ---------------------------
    resume_text = extract_text_from_pdf_bytes(pdf_bytes)

    if len(resume_text) > MAX_RESUME_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Resume text too long. Please submit a concise resume."
        )

    # ---------------------------
    # Resume grading
    # ---------------------------
    evaluation = grade_resume_against_job(
        job_description,
        resume_text
    )

    return {
        "evaluation": evaluation,
        "resume_preview": resume_text[:800]
    }


# ---------------------------
# ---------------------------
# next i can add a cash for the llm calls so if the same prompt is sent again it returns the cached response
# ---------------------------
