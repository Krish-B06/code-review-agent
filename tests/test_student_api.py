from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_add_student():
    response = client.post(
        "/students/",
        json={
            "student_id": 1,
            "name": "Alice",
            "marks": 92,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["student_id"] == 1
    assert data["name"] == "Alice"
    assert data["marks"] == 92
    assert data["grade"] == "A"


def test_get_student():
    client.post(
        "/students/",
        json={
            "student_id": 2,
            "name": "Bob",
            "marks": 78,
        },
    )

    response = client.get("/students/2")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Bob"
    assert data["grade"] == "B"


def test_get_missing_student():
    response = client.get("/students/999")

    assert response.status_code == 404


def test_update_marks():
    client.post(
        "/students/",
        json={
            "student_id": 3,
            "name": "Charlie",
            "marks": 50,
        },
    )

    response = client.put(
        "/students/3/marks",
        json={
            "marks": 85,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["marks"] == 85
    assert data["grade"] == "B"


def test_calculate_grade():
    client.post(
        "/students/",
        json={
            "student_id": 4,
            "name": "David",
            "marks": 95,
        },
    )

    response = client.get("/students/4/grade")

    assert response.status_code == 200
    assert response.json()["grade"] == "A"


def test_list_students():
    client.post(
        "/students/",
        json={
            "student_id": 5,
            "name": "Emma",
            "marks": 68,
        },
    )

    response = client.get("/students/")

    assert response.status_code == 200

    students = response.json()

    assert len(students) >= 1


def test_add_student_with_invalid_marks():
    response = client.post(
        "/students/",
        json={
            "student_id": 6,
            "name": "Frank",
            "marks": 120,
        },
    )

    assert response.status_code == 400