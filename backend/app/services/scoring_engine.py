import re


"""
Scoring Engine

Responsible for evaluating a resume against a job description.
This module is deterministic and explainable.
"""


def score_resume(resume_text: str, job_text: str):
    """
    Inputs:
        resume_text: Cleaned text extracted from resume
        job_text: Job description text

    Returns:
        {
            "overall_score": int,
            "skills_match": int,
            "missing_skills": list[str],
            "matched_skills": list[str],
            "notes": str
        }
    """
    pass

    # Step 1: Extract skills from resume
    # Step 2: Extract required skills from job description
    # Step 3: Compare overlap
    # Step 4: Calculate percentage match
    # Step 5: Return structured result
    # Example implementation (to be replaced with actual logic)
    # resume_skills = extract_skills(resume_text)


# Small starter skill list (we can expand later)
COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "sql", "html", "css",
    "react", "node", "fastapi", "flask", "django", "git", "github",
    "docker", "aws", "rest", "api", "postgresql", "mongodb",
    "pytest", "unit testing", "oop", "data structures", "algorithms"
}


def _normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9+\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_skills(text: str):
    """
    Very simple v1 extractor:
    - Finds skills based on a known skills list
    - Later we’ll replace/improve this with NLP + embeddings
    """
    normalized = _normalize(text)
    found = set()

    for skill in COMMON_SKILLS:
        # match whole words/phrases safely
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, normalized):
            found.add(skill)

    return found


def score_resume(resume_text, job_text):
    resume_skills = _extract_skills(resume_text)
    job_skills = _extract_skills(job_text)

    matched = sorted(resume_skills.intersection(job_skills))
    missing = sorted(job_skills.difference(resume_skills))

    # If job has no detected skills, avoid divide-by-zero
    if len(job_skills) == 0:
        skills_score = 0
    else:
        skills_score = int(round((len(matched) / len(job_skills)) * 100))

    # Overall score for v1 = skills_score (we’ll add other components later)
    overall_score = skills_score

    return {
        "overall_score": overall_score,
        "skills_match": skills_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "notes": "v1 keyword-based scoring (deterministic)."
    }
