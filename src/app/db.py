from __future__ import annotations

import argparse
import random
import sqlite3
import time
from dataclasses import dataclass
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

DROP_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS course_times;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS semesters;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS professors;
DROP TABLE IF EXISTS departments;
"""

REQUIRED_COUNTS = {
    "departments": 10,
    "courses": 500,
    "students": 10_000,
    "professors": 100,
}

DEPARTMENT_TOKENS = [
    ("컴퓨터공학과", "CSE"),
    ("전자공학과", "EEE"),
    ("기계공학과", "MEC"),
    ("산업공학과", "IND"),
    ("경영학과", "BUS"),
    ("경제학과", "ECO"),
    ("통계학과", "STA"),
    ("수학과", "MAT"),
    ("물리학과", "PHY"),
    ("화학과", "CHE"),
    ("생명과학과", "BIO"),
    ("심리학과", "PSY"),
]

SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황"]
GIVEN_NAMES = [
    "민준",
    "서연",
    "지후",
    "서준",
    "하은",
    "지민",
    "도윤",
    "윤서",
    "지우",
    "예준",
    "수아",
    "준우",
    "유진",
    "지현",
    "시윤",
    "채원",
    "현우",
    "지훈",
    "나연",
    "예린",
    "민지",
    "서현",
    "준서",
    "수빈",
    "태현",
    "은지",
    "민수",
    "영준",
    "하준",
    "다은",
]

COURSE_TITLES = [
    "자료구조",
    "알고리즘",
    "운영체제",
    "데이터베이스",
    "컴퓨터네트워크",
    "인공지능",
    "머신러닝",
    "소프트웨어공학",
    "회로이론",
    "전자기학",
    "디지털공학",
    "제어공학",
    "경영학원론",
    "재무관리",
    "마케팅원론",
    "미시경제",
    "거시경제",
    "통계학개론",
    "확률론",
    "선형대수",
    "미분적분학",
    "일반물리학",
    "일반화학",
    "생명과학개론",
    "공업수학",
    "실험물리",
    "화학실험",
    "인지심리학",
    "발달심리학",
    "산업심리학",
]

LEVEL_SUFFIX = ["I", "II", "III", "심화", "응용", "실습"]
DAY_PAIRS = [("MON", "WED"), ("TUE", "THU"), ("MON", "THU"), ("TUE", "FRI"), ("WED", "FRI")]
TIME_SLOTS = [("09:00", "10:15"), ("10:30", "11:45"), ("13:00", "14:15"), ("14:30", "15:45"), ("16:00", "17:15")]


def init_db() -> None:
    conn = get_connection()
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()


def _has_required_counts(conn: sqlite3.Connection) -> bool:
    for table, minimum in REQUIRED_COUNTS.items():
        count = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()["cnt"]
        if count < minimum:
            return False
    return True


def _generate_name_pool(count: int, rng: random.Random) -> list[str]:
    names: list[str] = []
    while len(names) < count:
        surname = rng.choice(SURNAMES)
        given = rng.choice(GIVEN_NAMES)
        names.append(f"{surname}{given}")
    return names


def seed_db(force: bool = False) -> float:
    conn = get_connection()
    start = time.perf_counter()
    try:
        with conn:
            if not force and _has_required_counts(conn):
                print("Seed skipped: required counts already satisfied.")
                return 0.0

            conn.executescript(DROP_SQL)
            conn.executescript(SCHEMA_SQL)

            rng = random.Random(42)

            dept_rows = [(name,) for name, _ in DEPARTMENT_TOKENS]
            conn.executemany("INSERT INTO departments (name) VALUES (?)", dept_rows)

            dept_map = {
                row["name"]: row["id"]
                for row in conn.execute("SELECT id, name FROM departments")
            }
            dept_codes = {name: code for name, code in DEPARTMENT_TOKENS}
            dept_ids = list(dept_map.values())

            professor_names = _generate_name_pool(REQUIRED_COUNTS["professors"], rng)
            professor_rows = [
                (name, dept_ids[idx % len(dept_ids)]) for idx, name in enumerate(professor_names)
            ]
            conn.executemany(
                "INSERT INTO professors (name, department_id) VALUES (?, ?)", professor_rows
            )

            student_names = _generate_name_pool(REQUIRED_COUNTS["students"], rng)
            student_rows = [(name, 18) for name in student_names]
            conn.executemany(
                "INSERT INTO students (name, max_credits) VALUES (?, ?)", student_rows
            )

            semesters = [
                ("2026 Spring", "2026-03-01", "2026-06-30"),
                ("2026 Fall", "2026-09-01", "2026-12-15"),
            ]
            conn.executemany(
                "INSERT INTO semesters (name, start_date, end_date) VALUES (?, ?, ?)",
                semesters,
            )
            semester_id = conn.execute(
                "SELECT id FROM semesters ORDER BY start_date DESC LIMIT 1"
            ).fetchone()["id"]

            professor_by_dept: dict[int, list[int]] = {dept_id: [] for dept_id in dept_ids}
            for row in conn.execute("SELECT id, department_id FROM professors"):
                professor_by_dept[row["department_id"]].append(row["id"])

            courses: list[tuple[int, int, int, str, str, int, int]] = []
            course_per_dept = REQUIRED_COUNTS["courses"] // len(dept_ids)
            extra = REQUIRED_COUNTS["courses"] % len(dept_ids)
            course_index = 0
            for dept_name, dept_id in dept_map.items():
                target = course_per_dept + (1 if extra > 0 else 0)
                if extra > 0:
                    extra -= 1
                for i in range(target):
                    title = COURSE_TITLES[(course_index + i) % len(COURSE_TITLES)]
                    suffix = LEVEL_SUFFIX[(course_index + i) % len(LEVEL_SUFFIX)]
                    name = f"{title} {suffix}"
                    code = f"{dept_codes[dept_name]}{100 + (course_index + i) % 900:03d}"
                    credits = rng.choices([1, 2, 3], weights=[2, 3, 5], k=1)[0]
                    capacity = (
                        1 if (course_index + i) % 50 == 0 else rng.choice([20, 30, 40, 50, 60])
                    )
                    professor_id = rng.choice(professor_by_dept[dept_id])
                    courses.append(
                        (dept_id, professor_id, semester_id, code, name, credits, capacity)
                    )
                course_index += target

            conn.executemany(
                """
                INSERT INTO courses (
                  department_id, professor_id, semester_id, code, name, credits, capacity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                courses,
            )

            course_rows = conn.execute("SELECT id FROM courses ORDER BY id").fetchall()
            course_times: list[tuple[int, str, str, str]] = []
            for idx, row in enumerate(course_rows):
                day_pair = DAY_PAIRS[idx % len(DAY_PAIRS)]
                slot = TIME_SLOTS[idx % len(TIME_SLOTS)]
                course_times.append((row["id"], day_pair[0], slot[0], slot[1]))
                course_times.append((row["id"], day_pair[1], slot[0], slot[1]))

            conn.executemany(
                """
                INSERT INTO course_times (course_id, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """,
                course_times,
            )

            counts = {
                "departments": conn.execute("SELECT COUNT(*) AS cnt FROM departments").fetchone()["cnt"],
                "professors": conn.execute("SELECT COUNT(*) AS cnt FROM professors").fetchone()["cnt"],
                "students": conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()["cnt"],
                "courses": conn.execute("SELECT COUNT(*) AS cnt FROM courses").fetchone()["cnt"],
            }

        duration = time.perf_counter() - start
        print(
            f"Seeded data in {duration:.2f}s: "
            f"departments={counts['departments']}, "
            f"professors={counts['professors']}, "
            f"students={counts['students']}, "
            f"courses={counts['courses']}"
        )
        return duration
    finally:
        conn.close()


def reset_db() -> None:
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
            seed_db(force=True)
            return
        except PermissionError:
            pass
    seed_db(force=True)


def ensure_seeded() -> float:
    init_db()
    return seed_db(force=False)


@dataclass(frozen=True)
class CourseSummary:
    code: str
    capacity: int
    enrolled_count: int
    times: str


def fetch_course_summaries() -> Iterable[CourseSummary]:
    conn = get_connection()
    try:
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
    finally:
        conn.close()


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
        seed_db(force=False)
    elif args.command == "reset":
        reset_db()
    elif args.command == "summary":
        seed_db(force=False)
        print_course_summary()


if __name__ == "__main__":
    main()
