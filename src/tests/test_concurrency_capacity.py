from __future__ import annotations

import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
os.environ["APP_DB_PATH"] = str(ROOT / "data" / "test.db")

from app import db
from app.services.enrollment_service import create_enrollment


class ConcurrencyCapacityTest(unittest.TestCase):
    def setUp(self) -> None:
        db.reset_db()

    def test_capacity_one_concurrency(self) -> None:
        conn = db.get_connection()
        with conn:
            course_id = conn.execute(
                "SELECT id FROM courses WHERE capacity = 1 ORDER BY id LIMIT 1"
            ).fetchone()["id"]
            student_ids = [
                row["id"]
                for row in conn.execute("SELECT id FROM students ORDER BY id LIMIT 100").fetchall()
            ]
        conn.close()

        barrier = Barrier(len(student_ids))

        def attempt(student_id: int) -> str:
            local = db.get_connection()
            try:
                barrier.wait(timeout=10)
                create_enrollment(local, student_id, course_id)
                return "success"
            except HTTPException as exc:
                return exc.detail["error"]["code"]
            finally:
                local.close()

        with ThreadPoolExecutor(max_workers=len(student_ids)) as executor:
            results = list(executor.map(attempt, student_ids))

        success_count = results.count("success")
        fail_count = len(results) - success_count

        verify = db.get_connection()
        enrolled_count = verify.execute(
            "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = ?", (course_id,)
        ).fetchone()["cnt"]
        verify.close()

        print(f"success={success_count} fail={fail_count} enrolled_count={enrolled_count}")

        self.assertEqual(success_count, 1)
        self.assertEqual(fail_count, 99)
        self.assertEqual(enrolled_count, 1)


if __name__ == "__main__":
    unittest.main()
