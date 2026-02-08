from __future__ import annotations

import os
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
os.environ["APP_DB_PATH"] = str(ROOT / "data" / "test_large.db")

from app.main import app


class SeedSmokeTest(unittest.TestCase):
    def test_seed_and_minimum_counts(self) -> None:
        start = time.perf_counter()
        with TestClient(app) as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)

            students = client.get("/students").json()
            courses = client.get("/courses").json()
            professors = client.get("/professors").json()

        elapsed = time.perf_counter() - start

        self.assertGreaterEqual(len(students), 10_000)
        self.assertGreaterEqual(len(courses), 500)
        self.assertGreaterEqual(len(professors), 100)
        self.assertLess(elapsed, 60.0)


if __name__ == "__main__":
    unittest.main()
