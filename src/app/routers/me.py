from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query

from ..db import get_db
from ..errors import parse_student_id, raise_error
from ..schemas import ScheduleItem, TimetableItem, TimetableOut

router = APIRouter(prefix="/me", tags=["me"])


def _ensure_student(db: sqlite3.Connection, student_id: int) -> None:
    row = db.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        raise_error("STUDENT_NOT_FOUND", "Student not found", 404)


def _resolve_semester_id(db: sqlite3.Connection, semester_id: Optional[int]) -> int:
    if semester_id is not None:
        row = db.execute("SELECT id FROM semesters WHERE id = ?", (semester_id,)).fetchone()
        if row is None:
            raise_error("SEMESTER_NOT_FOUND", "Semester not found", 404)
        return row["id"]
    row = db.execute(
        "SELECT id FROM semesters ORDER BY start_date DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise_error("SEMESTER_NOT_FOUND", "Semester not found", 404)
    return row["id"]


def _fetch_schedule_map(db: sqlite3.Connection, course_ids: list[int]) -> dict[int, list[ScheduleItem]]:
    schedule_map: dict[int, list[ScheduleItem]] = {course_id: [] for course_id in course_ids}
    if not course_ids:
        return schedule_map
    placeholders = ",".join(["?"] * len(course_ids))
    rows = db.execute(
        f"""
        SELECT course_id, day_of_week, start_time, end_time
        FROM course_times
        WHERE course_id IN ({placeholders})
        ORDER BY course_id, day_of_week, start_time
        """,
        course_ids,
    ).fetchall()
    for row in rows:
        schedule_map[row["course_id"]].append(
            ScheduleItem(day=row["day_of_week"], start=row["start_time"], end=row["end_time"])
        )
    return schedule_map


@router.get("/timetable", response_model=TimetableOut)
def get_timetable(
    semester_id: Optional[int] = Query(default=None),
    x_student_id: Optional[str] = Header(default=None, alias="X-Student-Id"),
    db: sqlite3.Connection = Depends(get_db),
) -> TimetableOut:
    student_id = parse_student_id(x_student_id)
    _ensure_student(db, student_id)
    resolved_semester_id = _resolve_semester_id(db, semester_id)

    rows = db.execute(
        """
        SELECT
          e.id AS enrollment_id,
          c.id AS course_id,
          c.code,
          c.name,
          c.credits
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        WHERE e.student_id = ? AND e.semester_id = ?
        ORDER BY c.code
        """,
        (student_id, resolved_semester_id),
    ).fetchall()

    course_ids = [row["course_id"] for row in rows]
    schedule_map = _fetch_schedule_map(db, course_ids)

    items = [
        TimetableItem(
            enrollment_id=row["enrollment_id"],
            course_id=row["course_id"],
            code=row["code"],
            name=row["name"],
            credits=row["credits"],
            schedule=schedule_map.get(row["course_id"], []),
        )
        for row in rows
    ]
    total_credits = sum(item.credits for item in items)

    return TimetableOut(
        student_id=student_id,
        semester_id=resolved_semester_id,
        total_credits=total_credits,
        items=items,
    )
