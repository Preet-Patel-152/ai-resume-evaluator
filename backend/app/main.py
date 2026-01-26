from .services.resume_grader import grade_resume_against_job
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from .services.pdf_parser import extract_text_from_pdf_bytes
from .services.llm import call_chat_model

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


# ---------------------------
# Chatbot Logic
# ---------------------------
def get_bot_reply(user_message: str) -> str:
    lower_msg = user_message.lower()

    if any(greeting in lower_msg for greeting in ["hello", "hi", "hey"]):
        return "Hello! How can I assist you today?"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a top-level advisor. "
                "Give clear, helpful, and concise answers."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]
    return call_chat_model(messages)


@app.post("/chat/")
def chat(request: ChatRequest):
    reply = get_bot_reply(request.message)
    return {"reply": reply}


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
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(...),
):
    if resume_pdf.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {resume_pdf.content_type}. Upload a PDF."
        )

    pdf_bytes = await resume_pdf.read()
    resume_text = extract_text_from_pdf_bytes(pdf_bytes)

    evaluation = grade_resume_against_job(job_description, resume_text)

    return {
        "evaluation": evaluation,
        "resume_preview": resume_text[:800],  # helpful for debugging
    }
