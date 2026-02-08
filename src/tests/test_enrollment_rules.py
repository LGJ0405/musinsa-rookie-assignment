from __future__ import annotations

import os
import unittest
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
os.environ["APP_DB_PATH"] = str(ROOT / "data" / "test.db")

from app import db
from app.services.enrollment_service import cancel_enrollment, create_enrollment


class EnrollmentRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        db.reset_db()

    def setUp(self) -> None:
        self.conn = db.get_connection()
        with self.conn:
            self.conn.execute("DELETE FROM enrollments")
            self.conn.execute("DELETE FROM students WHERE name = 'Limit'")

    def tearDown(self) -> None:
        self.conn.close()

    def test_credit_limit(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO students (name, max_credits) VALUES (?, ?)", ("Limit", 3)
            )
            student_id = self.conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            courses = self.conn.execute(
                "SELECT id FROM courses WHERE credits >= 3 ORDER BY id LIMIT 2"
            ).fetchall()
            course_a = courses[0]["id"]
            course_b = courses[1]["id"]

        create_enrollment(self.conn, student_id, course_a)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_b)
        self.assertEqual(ctx.exception.detail["error"]["code"], "CREDIT_LIMIT_EXCEEDED")

    def test_time_conflict(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
            row = self.conn.execute(
                """
                SELECT t1.course_id AS course_a, t2.course_id AS course_b
                FROM course_times t1
                JOIN course_times t2
                  ON t1.day_of_week = t2.day_of_week
                 AND t1.start_time = t2.start_time
                 AND t1.end_time = t2.end_time
                 AND t1.course_id < t2.course_id
                LIMIT 1
                """
            ).fetchone()
            course_a = row["course_a"]
            course_b = row["course_b"]

        create_enrollment(self.conn, student_id, course_a)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_b)
        self.assertEqual(ctx.exception.detail["error"]["code"], "TIME_CONFLICT")

    def test_duplicate_enrollment(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
            course_id = self.conn.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()["id"]

        create_enrollment(self.conn, student_id, course_id)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_id)
        self.assertEqual(ctx.exception.detail["error"]["code"], "DUPLICATE_ENROLLMENT")

    def test_cancel_enrollment(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
            course_id = self.conn.execute("SELECT id FROM courses ORDER BY id LIMIT 2").fetchone()["id"]

        enrollment = create_enrollment(self.conn, student_id, course_id)
        cancel_enrollment(self.conn, student_id, enrollment["id"])

        row = self.conn.execute(
            "SELECT id FROM enrollments WHERE id = ?", (enrollment["id"],)
        ).fetchone()
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
