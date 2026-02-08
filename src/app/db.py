from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .settings import DATA_DIR, DB_PATH, SQLITE_BUSY_TIMEOUT_MS


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS};")
    return conn


def get_db() -> sqlite3.Connection:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS departments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS professors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  department_id INTEGER NOT NULL,
  FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  max_credits INTEGER NOT NULL DEFAULT 18
);

CREATE TABLE IF NOT EXISTS semesters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  department_id INTEGER NOT NULL,
  professor_id INTEGER NOT NULL,
  semester_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  credits INTEGER NOT NULL,
  capacity INTEGER NOT NULL,
  FOREIGN KEY(department_id) REFERENCES departments(id),
  FOREIGN KEY(professor_id) REFERENCES professors(id),
  FOREIGN KEY(semester_id) REFERENCES semesters(id)
);

CREATE TABLE IF NOT EXISTS course_times (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  day_of_week TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  semester_id INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(student_id) REFERENCES students(id),
  FOREIGN KEY(course_id) REFERENCES courses(id),
  FOREIGN KEY(semester_id) REFERENCES semesters(id),
  UNIQUE(student_id, course_id, semester_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_course_times_course ON course_times(course_id);
"""


def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.executescript(SCHEMA_SQL)


def seed_db() -> None:
    conn = get_connection()
    with conn:
        existing = conn.execute("SELECT COUNT(*) AS cnt FROM courses").fetchone()["cnt"]
        if existing > 0:
            return

        departments = ["CS", "EE"]
        for name in departments:
            conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))

        dept_map = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM departments")
        }

        professors = [
            ("Park", dept_map["CS"]),
            ("Lee", dept_map["EE"]),
        ]
        conn.executemany(
            "INSERT INTO professors (name, department_id) VALUES (?, ?)", professors
        )

        students = [
            ("Kim", 18),
            ("Choi", 18),
            ("Han", 18),
        ]
        conn.executemany(
            "INSERT INTO students (name, max_credits) VALUES (?, ?)", students
        )

        semesters = [
            ("2026 Spring", "2026-03-01", "2026-06-30"),
            ("2026 Fall", "2026-09-01", "2026-12-15"),
        ]
        conn.executemany(
            "INSERT INTO semesters (name, start_date, end_date) VALUES (?, ?, ?)",
            semesters,
        )

        semester_map = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM semesters")
        }

        professor_map = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM professors")
        }

        courses = [
            (
                dept_map["CS"],
                professor_map["Park"],
                semester_map["2026 Spring"],
                "CS101",
                "Intro to CS",
                3,
                2,
            ),
            (
                dept_map["CS"],
                professor_map["Park"],
                semester_map["2026 Spring"],
                "CS102",
                "Data Structures",
                3,
                2,
            ),
            (
                dept_map["CS"],
                professor_map["Park"],
                semester_map["2026 Spring"],
                "CS201",
                "Algorithms",
                3,
                1,
            ),
            (
                dept_map["EE"],
                professor_map["Lee"],
                semester_map["2026 Spring"],
                "EE101",
                "Circuits",
                3,
                2,
            ),
            (
                dept_map["EE"],
                professor_map["Lee"],
                semester_map["2026 Spring"],
                "EE201",
                "Signals",
                3,
                2,
            ),
        ]
        conn.executemany(
            """
            INSERT INTO courses (
              department_id, professor_id, semester_id, code, name, credits, capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            courses,
        )

        course_map = {
            row["code"]: row["id"]
            for row in conn.execute("SELECT id, code FROM courses")
        }

        course_times = [
            (course_map["CS101"], "MON", "09:00", "10:15"),
            (course_map["CS101"], "WED", "09:00", "10:15"),
            (course_map["CS102"], "MON", "09:30", "10:45"),
            (course_map["CS102"], "WED", "09:30", "10:45"),
            (course_map["CS201"], "TUE", "13:00", "14:15"),
            (course_map["CS201"], "THU", "13:00", "14:15"),
            (course_map["EE101"], "MON", "10:30", "11:45"),
            (course_map["EE101"], "WED", "10:30", "11:45"),
            (course_map["EE201"], "WED", "09:00", "10:15"),
            (course_map["EE201"], "FRI", "09:00", "10:15"),
        ]
        conn.executemany(
            """
            INSERT INTO course_times (course_id, day_of_week, start_time, end_time)
            VALUES (?, ?, ?, ?)
            """,
            course_times,
        )


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    seed_db()


@dataclass(frozen=True)
class CourseSummary:
    code: str
    capacity: int
    enrolled_count: int
    times: str


def fetch_course_summaries() -> Iterable[CourseSummary]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
          c.code,
          c.capacity,
          COUNT(e.id) AS enrolled_count,
          GROUP_CONCAT(ct.day_of_week || ' ' || ct.start_time || '-' || ct.end_time, ', ') AS times
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN course_times ct ON ct.course_id = c.id
        GROUP BY c.id
        ORDER BY c.code
        """
    ).fetchall()
    for row in rows:
        yield CourseSummary(
            code=row["code"],
            capacity=row["capacity"],
            enrolled_count=row["enrolled_count"],
            times=row["times"] or "",
        )


def print_course_summary() -> None:
    for summary in fetch_course_summaries():
        print(
            f"{summary.code} | capacity={summary.capacity} "
            f"| enrolled={summary.enrolled_count} | times={summary.times}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="DB utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("seed")
    sub.add_parser("reset")
    sub.add_parser("summary")
    args = parser.parse_args()

    if args.command == "init":
        init_db()
    elif args.command == "seed":
        init_db()
        seed_db()
    elif args.command == "reset":
        reset_db()
    elif args.command == "summary":
        init_db()
        seed_db()
        print_course_summary()


if __name__ == "__main__":
    main()
