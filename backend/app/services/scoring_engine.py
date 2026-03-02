import re


"""
Scoring Engine

Responsible for evaluating a resume against a job description.
This module is deterministic and explainable.
"""


COMMON_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "bash",

    # Web frontend
    "html", "css", "react", "angular", "vue", "tailwind", "bootstrap", "sass",

    # Web backend
    "node", "express", "fastapi", "flask", "django", "spring", "rails", "laravel",

    # Databases
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "redis",
    "elasticsearch", "cassandra", "dynamodb",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "linux", "git", "github", "gitlab",

    # Data & ML
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "pandas", "numpy", "scikit", "computer vision", "data science",
    "data analysis", "tableau", "power bi",

    # Practices & concepts
    "rest", "api", "graphql", "microservices", "agile", "scrum",
    "oop", "data structures", "algorithms", "unit testing",
    "pytest", "tdd", "devops", "security",
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
