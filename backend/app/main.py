from fastapi import BackgroundTasks, Request, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from fastapi import Request
import os

from .services.pdf_parser import extract_text_from_pdf_bytes
# from .services.llm import call_chat_model
from .services.resume_grader import grade_resume_against_job
from .services.analytics import log_event
from .middleware.rate_limiter import RateLimiter

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf'}

rate_limiter = RateLimiter(
    max_requests=10,      # 10 requests
    window_seconds=3600   # per hour
)

# Load env from backend/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# Enable CORS for all origins (for development)
app = FastAPI(
    title="Resume AI Service",
    version="1.0.0",
    description="Chat + Resume Grading + PDF Upload"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    background_tasks: BackgroundTasks,
    request: Request,
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(...)
):

    await rate_limiter.check_rate_limit(request)

    # Run analytics safely in the background
    background_tasks.add_task(
        log_event,
        "resume_analysis",
        request.client.host if request.client else None
    )

    if resume_pdf.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    pdf_bytes = await resume_pdf.read()
    resume_text = extract_text_from_pdf_bytes(pdf_bytes)

    evaluation = grade_resume_against_job(job_description, resume_text)

    return {
        "evaluation": evaluation,
        "resume_preview": resume_text[:800]
    }

# ---------------------------
# ---------------------------
# what i need to do for tommorow is mkae a rate limit for the api calls to openai
# ---------------------------
# next if make a check ofr if the pdf is too large then reject it
# ---------------------------
# next i can add a cash for the llm calls so if the same prompt is sent again it returns the cached response
# ---------------------------
