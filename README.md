# AI Resume Evaluator

A full-stack web app that scores a resume against a job description and returns structured feedback (skill match, gaps, and suggestions).

## Demo
- Live: (coming soon)
- Screenshots: (coming soon)

## Problem
Candidates don’t know why resumes get rejected and what to change.

## Solution
This app extracts text from resumes, compares it to a job description, calculates a match score, and generates actionable feedback.

## Features (MVP)
- Upload resume (PDF/DOCX) or paste text
- Paste job description
- Skill match score + missing skills
- Keyword overlap + recommendations
- Download feedback as JSON/text

## Tech Stack
- Backend: Python + FastAPI
- NLP: spaCy + sentence-transformers (similarity scoring)
- Frontend: HTML/CSS/JS (simple MVP UI)
- Storage: SQLite (later)
- Deployment: (later)

## Architecture
1. Resume parsing → clean text
2. Skill extraction + similarity scoring
3. (Optional) LLM to turn results into readable feedback

## Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
