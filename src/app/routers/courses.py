from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..db import get_db
from ..schemas import CourseOut, ScheduleItem

router = APIRouter(prefix="/courses", tags=["courses"])


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


@router.get("", response_model=list[CourseOut])
def list_courses(
    department_id: Optional[int] = Query(default=None),
    semester_id: Optional[int] = Query(default=None),
    db: sqlite3.Connection = Depends(get_db),
) -> list[CourseOut]:
    params: list[int] = []
    where_clauses = []
    if department_id is not None:
        where_clauses.append("c.department_id = ?")
        params.append(department_id)
    if semester_id is not None:
        where_clauses.append("c.semester_id = ?")
        params.append(semester_id)
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    rows = db.execute(
        f"""
        SELECT
          c.id,
          c.code,
          c.name,
          c.credits,
          c.department_id,
          d.name AS department_name,
          c.professor_id,
          p.name AS professor_name,
          c.semester_id,
          c.capacity,
          (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS enrolled_count
        FROM courses c
        JOIN departments d ON d.id = c.department_id
        JOIN professors p ON p.id = c.professor_id
        {where_sql}
        ORDER BY c.code
        """,
        params,
    ).fetchall()

    course_ids = [row["id"] for row in rows]
    schedule_map = _fetch_schedule_map(db, course_ids)

    return [
        CourseOut(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            credits=row["credits"],
            department_id=row["department_id"],
            department_name=row["department_name"],
            professor_id=row["professor_id"],
            professor_name=row["professor_name"],
            semester_id=row["semester_id"],
            capacity=row["capacity"],
            enrolled_count=row["enrolled_count"],
            schedule=schedule_map.get(row["id"], []),
        )
        for row in rows
    ]
