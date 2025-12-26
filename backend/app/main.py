from fastapi import FastAPI

app = FastAPI(
    title="AI Resume Evaluator",
    description="API for scoring resumes against job descriptions",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
