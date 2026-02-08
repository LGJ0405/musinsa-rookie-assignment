from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import HTTPException

from ..errors import raise_error
from ..utils.time_conflict import has_time_conflict


def create_enrollment(
    db: sqlite3.Connection, student_id: int, course_id: int
) -> dict[str, Any]:
    try:
        db.execute("BEGIN IMMEDIATE")

        student = db.execute(
            "SELECT id, max_credits FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        if student is None:
            raise_error("STUDENT_NOT_FOUND", "Student not found", 404)

        course = db.execute(
            """
            SELECT id, semester_id, credits, capacity
            FROM courses
            WHERE id = ?
            """,
            (course_id,),
        ).fetchone()
        if course is None:
            raise_error("COURSE_NOT_FOUND", "Course not found", 404)

        semester_id = course["semester_id"]

        duplicate = db.execute(
            """
            SELECT 1 FROM enrollments
            WHERE student_id = ? AND course_id = ? AND semester_id = ?
            """,
            (student_id, course_id, semester_id),
        ).fetchone()
        if duplicate is not None:
            raise_error("DUPLICATE_ENROLLMENT", "Duplicate enrollment", 409)

        enrolled_count = db.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = ?",
            (course_id,),
        ).fetchone()["cnt"]
        if enrolled_count >= course["capacity"]:
            raise_error("CAPACITY_FULL", "Course capacity is full", 409)

        current_credits = db.execute(
            """
            SELECT COALESCE(SUM(c.credits), 0) AS total
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.student_id = ? AND e.semester_id = ?
            """,
            (student_id, semester_id),
        ).fetchone()["total"]
        if current_credits + course["credits"] > student["max_credits"]:
            raise_error("CREDIT_LIMIT_EXCEEDED", "Credit limit exceeded", 409)

        target_times = db.execute(
            """
            SELECT day_of_week, start_time, end_time
            FROM course_times
            WHERE course_id = ?
            """,
            (course_id,),
        ).fetchall()
        existing_times = db.execute(
            """
            SELECT ct.day_of_week, ct.start_time, ct.end_time
            FROM course_times ct
            JOIN enrollments e ON e.course_id = ct.course_id
            WHERE e.student_id = ? AND e.semester_id = ?
            """,
            (student_id, semester_id),
        ).fetchall()
        if has_time_conflict(target_times, existing_times):
            raise_error("TIME_CONFLICT", "Course time conflicts with existing schedule", 409)

        cursor = db.execute(
            """
            INSERT INTO enrollments (student_id, course_id, semester_id)
            VALUES (?, ?, ?)
            """,
            (student_id, course_id, semester_id),
        )
        enrollment_id = cursor.lastrowid

        row = db.execute(
            """
            SELECT id, student_id, course_id, semester_id, created_at
            FROM enrollments
            WHERE id = ?
            """,
            (enrollment_id,),
        ).fetchone()

        db.execute("COMMIT")
        return dict(row)
    except sqlite3.IntegrityError:
        db.execute("ROLLBACK")
        raise_error("DUPLICATE_ENROLLMENT", "Duplicate enrollment", 409)
    except HTTPException:
        db.execute("ROLLBACK")
        raise
    except Exception:
        db.execute("ROLLBACK")
        raise


def cancel_enrollment(
    db: sqlite3.Connection, student_id: int, enrollment_id: int
) -> None:
    row = db.execute(
        "SELECT id, student_id FROM enrollments WHERE id = ?",
        (enrollment_id,),
    ).fetchone()
    if row is None:
        raise_error("ENROLLMENT_NOT_FOUND", "Enrollment not found", 404)
    if row["student_id"] != student_id:
        raise_error("FORBIDDEN_ENROLLMENT_CANCEL", "Cannot cancel other student's enrollment", 403)

    db.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
