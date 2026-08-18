from app.models.student import Student


class StudentService:
    def __init__(self):
        self.students = {}

    def add_student(self, student_id, name, marks):
        student = Student(student_id, name, marks)
        self.students[student_id] = student
        return student

    def get_student(self, student_id):
        return self.students.get(student_id)

    def update_marks(self, student_id, marks):
        student = self.students.get(student_id)

        if student is None:
            return None

        student.marks = marks
        return student

    def calculate_grade(self, student_id):
        student = self.students.get(student_id)

        if student is None:
            return None

        return student.calculate_grade()

    def list_students(self):
        return list(self.students.values())