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
    def setUp(self) -> None:
        db.reset_db()
        self.conn = db.get_connection()

    def tearDown(self) -> None:
        self.conn.close()

    def test_credit_limit(self) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO students (name, max_credits) VALUES (?, ?)", ("Limit", 3)
            )
            student_id = self.conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            course_a = self.conn.execute("SELECT id FROM courses WHERE code = 'CS101'").fetchone()["id"]
            course_b = self.conn.execute("SELECT id FROM courses WHERE code = 'CS201'").fetchone()["id"]

        create_enrollment(self.conn, student_id, course_a)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_b)
        self.assertEqual(ctx.exception.detail["error"]["code"], "CREDIT_LIMIT_EXCEEDED")

    def test_time_conflict(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Kim'").fetchone()["id"]
            course_a = self.conn.execute("SELECT id FROM courses WHERE code = 'CS101'").fetchone()["id"]
            course_b = self.conn.execute("SELECT id FROM courses WHERE code = 'CS102'").fetchone()["id"]

        create_enrollment(self.conn, student_id, course_a)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_b)
        self.assertEqual(ctx.exception.detail["error"]["code"], "TIME_CONFLICT")

    def test_duplicate_enrollment(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Choi'").fetchone()["id"]
            course_id = self.conn.execute("SELECT id FROM courses WHERE code = 'EE101'").fetchone()["id"]

        create_enrollment(self.conn, student_id, course_id)
        with self.assertRaises(HTTPException) as ctx:
            create_enrollment(self.conn, student_id, course_id)
        self.assertEqual(ctx.exception.detail["error"]["code"], "DUPLICATE_ENROLLMENT")

    def test_cancel_enrollment(self) -> None:
        with self.conn:
            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Han'").fetchone()["id"]
            course_id = self.conn.execute("SELECT id FROM courses WHERE code = 'EE201'").fetchone()["id"]

        enrollment = create_enrollment(self.conn, student_id, course_id)
        cancel_enrollment(self.conn, student_id, enrollment["id"])

        row = self.conn.execute(
            "SELECT id FROM enrollments WHERE id = ?", (enrollment["id"],)
        ).fetchone()
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
