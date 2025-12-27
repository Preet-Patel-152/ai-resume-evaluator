import re

"""
Scoring Engine

Responsible for evaluating a resume against a job description.
This module is deterministic and explainable.
"""


def score_resume(resume_text: str, job_text: str) -> dict:
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
