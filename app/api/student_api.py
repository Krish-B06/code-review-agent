from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.student_service import StudentService


router = APIRouter(prefix="/students", tags=["Students"])

student_service = StudentService()


class StudentRequest(BaseModel):
    student_id: int
    name: str
    marks: float


class MarksUpdateRequest(BaseModel):
    marks: float


def student_to_dict(student):
    return {
        "student_id": student.student_id,
        "name": student.name,
        "marks": student.marks,
        "grade": student.calculate_grade(),
    }


@router.post("/")
def add_student(request: StudentRequest):
    try:
        student = student_service.add_student(
            request.student_id,
            request.name,
            request.marks,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return student_to_dict(student)


@router.get("/{student_id}")
def get_student(student_id: int):
    student = student_service.get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    return student_to_dict(student)


@router.put("/{student_id}/marks")
def update_marks(
    student_id: int,
    request: MarksUpdateRequest,
):
    try:
        student = student_service.update_marks(
            student_id,
            request.marks,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    return student_to_dict(student)


@router.get("/{student_id}/grade")
def calculate_grade(student_id: int):
    grade = student_service.calculate_grade(student_id)

    if grade is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    return {
        "student_id": student_id,
        "grade": grade,
    }


@router.get("/")
def list_students():
    students = student_service.list_students()

    return [
        student_to_dict(student)
        for student in students
    ]