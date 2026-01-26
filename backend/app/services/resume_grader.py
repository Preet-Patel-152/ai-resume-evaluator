import json
from fastapi import HTTPException
from .llm import call_chat_model

SYSTEM_PROMPT = (
    "You are an expert recruiter and resume reviewer.\n"
    "Given a job description and a resume, evaluate how well they match.\n"
    "Respond ONLY in valid JSON with this exact schema:\n\n"
    "{\n"
    '  "match_score": number,            // 0-100\n'
    '  "summary": string,               // short summary\n'
    '  "strengths": [string, ...],      // 3-5 bullet points\n'
    '  "gaps": [string, ...],           // 3-5 bullet points\n'
    '  "improvements": [string, ...]    // concrete suggestions\n'
    "}\n"
)


def grade_resume_against_job(job_description: str, resume_text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"JOB DESCRIPTION:\n{job_description}\n\nRESUME:\n{resume_text}",
        },
    ]

    raw = call_chat_model(messages)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Model returned invalid JSON"
        )
