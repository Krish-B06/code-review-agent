from fastapi import FastAPI

from app.api.student_api import router


app = FastAPI(
    title="Student Result API",
    description="API for managing students and calculating results.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def health_check():
    return {
        "message": "Student Result API is running",
    }