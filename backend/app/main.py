from app.services.scoring_engine import score_resume
from pydantic import BaseModel
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()


app = FastAPI(
    title="AI Resume Evaluator",
    description="API for scoring resumes against job descriptions",
    version="0.1.0"
)


class AnalyzeRequest(BaseModel):
    resume_text: str
    job_text: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest):
    return score_resume(payload.resume_text, payload.job_text)
