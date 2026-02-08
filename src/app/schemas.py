from __future__ import annotations

from pydantic import BaseModel


class StudentOut(BaseModel):
    id: int
    name: str
    max_credits: int


class ProfessorOut(BaseModel):
    id: int
    name: str
    department_id: int
    department_name: str


class ScheduleItem(BaseModel):
    day: str
    start: str
    end: str


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    credits: int
    department_id: int
    department_name: str
    professor_id: int
    professor_name: str
    semester_id: int
    capacity: int
    enrolled_count: int
    schedule: list[ScheduleItem]


class TimetableItem(BaseModel):
    enrollment_id: int
    course_id: int
    code: str
    name: str
    credits: int
    schedule: list[ScheduleItem]


class TimetableOut(BaseModel):
    student_id: int
    semester_id: int
    total_credits: int
    items: list[TimetableItem]
