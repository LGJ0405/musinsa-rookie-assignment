# Detailed Diff Summary

## Target Commit
- Hash: 93e180e4d6f40bfeb71c2d58dd8e5e685566691d
- Subject: [기능] 대규모 시드 자동 생성
- Date: 2026-02-08T17:04:40+09:00

## Summary (git show --stat)
```
commit 93e180e4d6f40bfeb71c2d58dd8e5e685566691d
Author: LGJ0405 <rlfwls03@naver.com>
Date:   Sun Feb 8 17:04:40 2026 +0900

    [기능] 대규모 시드 자동 생성
    
    포함: startup 자동 시드, 대규모 데이터 생성, 스모크 테스트 추가, 문서 갱신, httpx 추가
    
    검증: python -m app.db reset (Seeded data in 6.56s: departments=12, professors=100, students=10000, courses=500)
    
    검증: python -m unittest src/tests/test_seed_smoke.py (OK)
    
    검증: python -m unittest src/tests/test_enrollment_rules.py (OK)
    
    검증: python -m unittest src/tests/test_concurrency_capacity.py (success=1 fail=99 enrolled_count=1)

 README.md                              |  11 +-
 docs/API.md                            |   1 +
 docs/REQUIREMENTS.md                   |  40 ++--
 requirements.txt                       |   1 +
 src/app/db.py                          | 424 ++++++++++++++++++++-------------
 src/app/main.py                        |   6 +-
 src/app/routers/enrollments.py         |   2 -
 src/tests/test_concurrency_capacity.py |   6 +-
 src/tests/test_enrollment_rules.py     |  41 +++-
 src/tests/test_seed_smoke.py           |  36 +++
 10 files changed, 362 insertions(+), 206 deletions(-)
```

## Detailed Diff (git show HEAD)
```diff
commit 93e180e4d6f40bfeb71c2d58dd8e5e685566691d
Author: LGJ0405 <rlfwls03@naver.com>
Date:   Sun Feb 8 17:04:40 2026 +0900

    [기능] 대규모 시드 자동 생성
    
    포함: startup 자동 시드, 대규모 데이터 생성, 스모크 테스트 추가, 문서 갱신, httpx 추가
    
    검증: python -m app.db reset (Seeded data in 6.56s: departments=12, professors=100, students=10000, courses=500)
    
    검증: python -m unittest src/tests/test_seed_smoke.py (OK)
    
    검증: python -m unittest src/tests/test_enrollment_rules.py (OK)
    
    검증: python -m unittest src/tests/test_concurrency_capacity.py (success=1 fail=99 enrolled_count=1)

diff --git a/README.md b/README.md
index eeacbd3..0d4aa7a 100644
--- a/README.md
+++ b/README.md
@@ -9,11 +9,10 @@
 `pip install -r requirements.txt`
 
 ## DB 초기화/시드
-초기화
-`$env:PYTHONPATH=\"src\"; python -m app.db init`
-시드
-`$env:PYTHONPATH=\"src\"; python -m app.db seed`
-전체 재생성
+- 서버 시작 시 자동으로 초기 데이터가 생성됩니다.
+- 데이터가 이미 최소 규모를 만족하면 재생성하지 않습니다.
+
+수동 초기화/재생성(필요 시):
 `$env:PYTHONPATH=\"src\"; python -m app.db reset`
 
 DB 파일은 `./data/app.db`에 생성됩니다.
@@ -21,6 +20,8 @@ DB 파일은 `./data/app.db`에 생성됩니다.
 ## 서버 실행
 `uvicorn app.main:app --app-dir src --reload --host 0.0.0.0 --port 8000`
 
+초기 시드 생성은 최대 1분 이내에 완료되며, `/health`가 200을 반환하는 시점에는 데이터가 준비된 상태입니다.
+
 ## 접속 정보
 - API Base URL: `http://localhost:8000`
 - OpenAPI 문서: `http://localhost:8000/docs`
diff --git a/docs/API.md b/docs/API.md
index 3b895fb..106e5e2 100644
--- a/docs/API.md
+++ b/docs/API.md
@@ -19,6 +19,7 @@
 ## 1) Health Check
 ### GET `/health`
 - 응답 200
+  - 200 OK 반환 시 초기 데이터 생성이 완료된 상태임을 의미한다.
 ```json
 { "status": "ok" }
 ```
diff --git a/docs/REQUIREMENTS.md b/docs/REQUIREMENTS.md
index 20908e5..f588de9 100644
--- a/docs/REQUIREMENTS.md
+++ b/docs/REQUIREMENTS.md
@@ -56,8 +56,9 @@
 - `journal_mode=WAL`을 사용해 읽기/쓰기 동시성을 개선한다.
 - SQLite는 단일 writer 제약이 있으므로 고부하 환경에서는 DB 락 대기/지연이 발생할 수 있다.
   - 보완 전략: 프로덕션에서는 PostgreSQL 같은 다중 writer DB로 전환하거나, 신청 요청을 큐로 직렬화한다.
-- DB 초기화 정책: `python -m app.db reset`으로 수동 초기화/시드를 수행한다.
-  이는 반복 실행 시 테스트 재현성과 enrolled_count 정합성을 보장하기 위한 운영 절차이다.
+- DB 초기화 정책: 서버 시작 시 데이터가 없거나 최소 규모에 미달하면 DB를 초기화하고 시드 데이터를 자동 생성한다.
+  최소 규모를 이미 만족하면 재생성을 건너뛰어 실행 시간을 단축한다.
+- 서버가 `/health`에 200을 반환하는 시점은 시드 완료 이후로 정의한다.
 
 ## F. 구현 범위
 - MVP
@@ -69,30 +70,21 @@
 - 제외
   - 로그인/권한, 대기열, 선수과목, 수강기간 제한, 성적/수강료, 감사 이력
 
-## 데이터 규모에 대한 범위 결정
+## 데이터 생성/규모 정책
 
-문제 원문에서는 대규모 데이터 생성을 요구한다(학생 10,000명, 강좌 500개 이상).
-그러나 본 과제에서는 제한된 시간 내 핵심 로직(정원/학점/시간표/동시성)의
-정합성과 재현 가능성을 우선 검증하기 위해,
-데이터 규모를 축소한 시나리오 기반 구현을 선택했다.
-
-대규모 데이터 생성 로직은 실제 프로덕션 환경에서의 확장 포인트로 간주하며,
-본 과제에서는 구현 대신 설계 및 동시성 전략 설명으로 대체한다.
+- 데이터 규모: Department 10+, Professor 100+, Student 10,000+, Course 500+를 기본으로 생성한다.
+- 생성 방식: 정적 파일(SQL/CSV)을 사용하지 않고 실행 시 로직으로 동적 생성한다.
+  - 소규모 토큰(학과명/이름 목록)은 코드에 포함한다.
+- 데이터 품질: "User1", "Course1" 같은 무의미한 데이터 대신 현실적인 이름/과목명을 조합한다.
+- 성능: 단일 트랜잭션과 `executemany`를 사용해 1분 이내 생성 완료를 목표로 한다.
 
 
 ## 검증 로그
-- Step3 DB 시드 확인: `python -m app.db summary` 실행
-  - CS101 capacity=2 enrolled=0 times=MON 09:00-10:15, WED 09:00-10:15
-  - CS102 capacity=2 enrolled=0 times=MON 09:30-10:45, WED 09:30-10:45
-  - CS201 capacity=1 enrolled=0 times=TUE 13:00-14:15, THU 13:00-14:15
-  - EE101 capacity=2 enrolled=0 times=MON 10:30-11:45, WED 10:30-11:45
-  - EE201 capacity=2 enrolled=0 times=WED 09:00-10:15, FRI 09:00-10:15
-- Step4 스모크 테스트: 서버 실행 후 curl 호출
-  - GET /health -> {"status":"ok"}
-  - GET /students -> 3명 반환
-  - GET /courses -> 5개 강좌 반환 (정원/현재인원/시간 포함)
-  - GET /me/timetable (X-Student-Id: 1) -> semester_id=2, items=[]
-- Step5 규칙 테스트: `python -m unittest src/tests/test_enrollment_rules.py`
+- StepA 대규모 시드 생성: `python -m app.db reset`
+  - Seeded data in 6.56s: departments=12, professors=100, students=10000, courses=500
+- StepB 시드 스모크 테스트: `python -m unittest src/tests/test_seed_smoke.py`
+  - /health 200 이후 학생/교수/강좌 최소 수량 이상 확인
+- StepC 규칙 테스트: `python -m unittest src/tests/test_enrollment_rules.py`
   - credit limit / time conflict / duplicate / cancel 검증 OK
-- Step6 동시성 테스트: `python -m unittest src/tests/test_concurrency_capacity.py`
-  - success=1 fail=2 enrolled_count=1
+- StepD 동시성 테스트(100 동시): `python -m unittest src/tests/test_concurrency_capacity.py`
+  - success=1 fail=99 enrolled_count=1
diff --git a/requirements.txt b/requirements.txt
index c198891..587eae8 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 ﻿fastapi
 uvicorn[standard]
+httpx
diff --git a/src/app/db.py b/src/app/db.py
index dc66024..125e847 100644
--- a/src/app/db.py
+++ b/src/app/db.py
@@ -1,9 +1,10 @@
 from __future__ import annotations
 
 import argparse
+import random
 import sqlite3
+import time
 from dataclasses import dataclass
-from pathlib import Path
 from typing import Iterable
 
 from .settings import DATA_DIR, DB_PATH, SQLITE_BUSY_TIMEOUT_MS
@@ -103,162 +104,262 @@ DROP TABLE IF EXISTS professors;
 DROP TABLE IF EXISTS departments;
 """
 
+REQUIRED_COUNTS = {
+    "departments": 10,
+    "courses": 500,
+    "students": 10_000,
+    "professors": 100,
+}
+
+DEPARTMENT_TOKENS = [
+    ("컴퓨터공학과", "CSE"),
+    ("전자공학과", "EEE"),
+    ("기계공학과", "MEC"),
+    ("산업공학과", "IND"),
+    ("경영학과", "BUS"),
+    ("경제학과", "ECO"),
+    ("통계학과", "STA"),
+    ("수학과", "MAT"),
+    ("물리학과", "PHY"),
+    ("화학과", "CHE"),
+    ("생명과학과", "BIO"),
+    ("심리학과", "PSY"),
+]
+
+SURNAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황"]
+GIVEN_NAMES = [
+    "민준",
+    "서연",
+    "지후",
+    "서준",
+    "하은",
+    "지민",
+    "도윤",
+    "윤서",
+    "지우",
+    "예준",
+    "수아",
+    "준우",
+    "유진",
+    "지현",
+    "시윤",
+    "채원",
+    "현우",
+    "지훈",
+    "나연",
+    "예린",
+    "민지",
+    "서현",
+    "준서",
+    "수빈",
+    "태현",
+    "은지",
+    "민수",
+    "영준",
+    "하준",
+    "다은",
+]
+
+COURSE_TITLES = [
+    "자료구조",
+    "알고리즘",
+    "운영체제",
+    "데이터베이스",
+    "컴퓨터네트워크",
+    "인공지능",
+    "머신러닝",
+    "소프트웨어공학",
+    "회로이론",
+    "전자기학",
+    "디지털공학",
+    "제어공학",
+    "경영학원론",
+    "재무관리",
+    "마케팅원론",
+    "미시경제",
+    "거시경제",
+    "통계학개론",
+    "확률론",
+    "선형대수",
+    "미분적분학",
+    "일반물리학",
+    "일반화학",
+    "생명과학개론",
+    "공업수학",
+    "실험물리",
+    "화학실험",
+    "인지심리학",
+    "발달심리학",
+    "산업심리학",
+]
+
+LEVEL_SUFFIX = ["I", "II", "III", "심화", "응용", "실습"]
+DAY_PAIRS = [("MON", "WED"), ("TUE", "THU"), ("MON", "THU"), ("TUE", "FRI"), ("WED", "FRI")]
+TIME_SLOTS = [("09:00", "10:15"), ("10:30", "11:45"), ("13:00", "14:15"), ("14:30", "15:45"), ("16:00", "17:15")]
+
 
 def init_db() -> None:
     conn = get_connection()
-    with conn:
-        conn.executescript(SCHEMA_SQL)
-
+    try:
+        with conn:
+            conn.executescript(SCHEMA_SQL)
+    finally:
+        conn.close()
 
-def seed_db() -> None:
-    conn = get_connection()
-    with conn:
-        existing = conn.execute("SELECT COUNT(*) AS cnt FROM courses").fetchone()["cnt"]
-        if existing > 0:
-            return
 
-        departments = ["CS", "EE"]
-        for name in departments:
-            conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
-
-        dept_map = {
-            row["name"]: row["id"]
-            for row in conn.execute("SELECT id, name FROM departments")
-        }
-
-        professors = [
-            ("Park", dept_map["CS"]),
-            ("Lee", dept_map["EE"]),
-        ]
-        conn.executemany(
-            "INSERT INTO professors (name, department_id) VALUES (?, ?)", professors
-        )
+def _has_required_counts(conn: sqlite3.Connection) -> bool:
+    for table, minimum in REQUIRED_COUNTS.items():
+        count = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()["cnt"]
+        if count < minimum:
+            return False
+    return True
 
-        students = [
-            ("Kim", 18),
-            ("Choi", 18),
-            ("Han", 18),
-        ]
-        conn.executemany(
-            "INSERT INTO students (name, max_credits) VALUES (?, ?)", students
-        )
 
-        semesters = [
-            ("2026 Spring", "2026-03-01", "2026-06-30"),
-            ("2026 Fall", "2026-09-01", "2026-12-15"),
-        ]
-        conn.executemany(
-            "INSERT INTO semesters (name, start_date, end_date) VALUES (?, ?, ?)",
-            semesters,
-        )
+def _generate_name_pool(count: int, rng: random.Random) -> list[str]:
+    names: list[str] = []
+    while len(names) < count:
+        surname = rng.choice(SURNAMES)
+        given = rng.choice(GIVEN_NAMES)
+        names.append(f"{surname}{given}")
+    return names
 
-        semester_map = {
-            row["name"]: row["id"]
-            for row in conn.execute("SELECT id, name FROM semesters")
-        }
-
-        professor_map = {
-            row["name"]: row["id"]
-            for row in conn.execute("SELECT id, name FROM professors")
-        }
-
-        courses = [
-            (
-                dept_map["CS"],
-                professor_map["Park"],
-                semester_map["2026 Spring"],
-                "CS101",
-                "Intro to CS",
-                3,
-                2,
-            ),
-            (
-                dept_map["CS"],
-                professor_map["Park"],
-                semester_map["2026 Spring"],
-                "CS102",
-                "Data Structures",
-                3,
-                2,
-            ),
-            (
-                dept_map["CS"],
-                professor_map["Park"],
-                semester_map["2026 Spring"],
-                "CS201",
-                "Algorithms",
-                3,
-                1,
-            ),
-            (
-                dept_map["EE"],
-                professor_map["Lee"],
-                semester_map["2026 Spring"],
-                "EE101",
-                "Circuits",
-                3,
-                2,
-            ),
-            (
-                dept_map["EE"],
-                professor_map["Lee"],
-                semester_map["2026 Spring"],
-                "EE201",
-                "Signals",
-                3,
-                2,
-            ),
-        ]
-        conn.executemany(
-            """
-            INSERT INTO courses (
-              department_id, professor_id, semester_id, code, name, credits, capacity
-            ) VALUES (?, ?, ?, ?, ?, ?, ?)
-            """,
-            courses,
-        )
 
-        course_map = {
-            row["code"]: row["id"]
-            for row in conn.execute("SELECT id, code FROM courses")
-        }
-
-        course_times = [
-            (course_map["CS101"], "MON", "09:00", "10:15"),
-            (course_map["CS101"], "WED", "09:00", "10:15"),
-            (course_map["CS102"], "MON", "09:30", "10:45"),
-            (course_map["CS102"], "WED", "09:30", "10:45"),
-            (course_map["CS201"], "TUE", "13:00", "14:15"),
-            (course_map["CS201"], "THU", "13:00", "14:15"),
-            (course_map["EE101"], "MON", "10:30", "11:45"),
-            (course_map["EE101"], "WED", "10:30", "11:45"),
-            (course_map["EE201"], "WED", "09:00", "10:15"),
-            (course_map["EE201"], "FRI", "09:00", "10:15"),
-        ]
-        conn.executemany(
-            """
-            INSERT INTO course_times (course_id, day_of_week, start_time, end_time)
-            VALUES (?, ?, ?, ?)
-            """,
-            course_times,
+def seed_db(force: bool = False) -> float:
+    conn = get_connection()
+    start = time.perf_counter()
+    try:
+        with conn:
+            if not force and _has_required_counts(conn):
+                print("Seed skipped: required counts already satisfied.")
+                return 0.0
+
+            conn.executescript(DROP_SQL)
+            conn.executescript(SCHEMA_SQL)
+
+            rng = random.Random(42)
+
+            dept_rows = [(name,) for name, _ in DEPARTMENT_TOKENS]
+            conn.executemany("INSERT INTO departments (name) VALUES (?)", dept_rows)
+
+            dept_map = {
+                row["name"]: row["id"]
+                for row in conn.execute("SELECT id, name FROM departments")
+            }
+            dept_codes = {name: code for name, code in DEPARTMENT_TOKENS}
+            dept_ids = list(dept_map.values())
+
+            professor_names = _generate_name_pool(REQUIRED_COUNTS["professors"], rng)
+            professor_rows = [
+                (name, dept_ids[idx % len(dept_ids)]) for idx, name in enumerate(professor_names)
+            ]
+            conn.executemany(
+                "INSERT INTO professors (name, department_id) VALUES (?, ?)", professor_rows
+            )
+
+            student_names = _generate_name_pool(REQUIRED_COUNTS["students"], rng)
+            student_rows = [(name, 18) for name in student_names]
+            conn.executemany(
+                "INSERT INTO students (name, max_credits) VALUES (?, ?)", student_rows
+            )
+
+            semesters = [
+                ("2026 Spring", "2026-03-01", "2026-06-30"),
+                ("2026 Fall", "2026-09-01", "2026-12-15"),
+            ]
+            conn.executemany(
+                "INSERT INTO semesters (name, start_date, end_date) VALUES (?, ?, ?)",
+                semesters,
+            )
+            semester_id = conn.execute(
+                "SELECT id FROM semesters ORDER BY start_date DESC LIMIT 1"
+            ).fetchone()["id"]
+
+            professor_by_dept: dict[int, list[int]] = {dept_id: [] for dept_id in dept_ids}
+            for row in conn.execute("SELECT id, department_id FROM professors"):
+                professor_by_dept[row["department_id"]].append(row["id"])
+
+            courses: list[tuple[int, int, int, str, str, int, int]] = []
+            course_per_dept = REQUIRED_COUNTS["courses"] // len(dept_ids)
+            extra = REQUIRED_COUNTS["courses"] % len(dept_ids)
+            course_index = 0
+            for dept_name, dept_id in dept_map.items():
+                target = course_per_dept + (1 if extra > 0 else 0)
+                if extra > 0:
+                    extra -= 1
+                for i in range(target):
+                    title = COURSE_TITLES[(course_index + i) % len(COURSE_TITLES)]
+                    suffix = LEVEL_SUFFIX[(course_index + i) % len(LEVEL_SUFFIX)]
+                    name = f"{title} {suffix}"
+                    code = f"{dept_codes[dept_name]}{100 + (course_index + i) % 900:03d}"
+                    credits = rng.choices([1, 2, 3], weights=[2, 3, 5], k=1)[0]
+                    capacity = (
+                        1 if (course_index + i) % 50 == 0 else rng.choice([20, 30, 40, 50, 60])
+                    )
+                    professor_id = rng.choice(professor_by_dept[dept_id])
+                    courses.append(
+                        (dept_id, professor_id, semester_id, code, name, credits, capacity)
+                    )
+                course_index += target
+
+            conn.executemany(
+                """
+                INSERT INTO courses (
+                  department_id, professor_id, semester_id, code, name, credits, capacity
+                ) VALUES (?, ?, ?, ?, ?, ?, ?)
+                """,
+                courses,
+            )
+
+            course_rows = conn.execute("SELECT id FROM courses ORDER BY id").fetchall()
+            course_times: list[tuple[int, str, str, str]] = []
+            for idx, row in enumerate(course_rows):
+                day_pair = DAY_PAIRS[idx % len(DAY_PAIRS)]
+                slot = TIME_SLOTS[idx % len(TIME_SLOTS)]
+                course_times.append((row["id"], day_pair[0], slot[0], slot[1]))
+                course_times.append((row["id"], day_pair[1], slot[0], slot[1]))
+
+            conn.executemany(
+                """
+                INSERT INTO course_times (course_id, day_of_week, start_time, end_time)
+                VALUES (?, ?, ?, ?)
+                """,
+                course_times,
+            )
+
+            counts = {
+                "departments": conn.execute("SELECT COUNT(*) AS cnt FROM departments").fetchone()["cnt"],
+                "professors": conn.execute("SELECT COUNT(*) AS cnt FROM professors").fetchone()["cnt"],
+                "students": conn.execute("SELECT COUNT(*) AS cnt FROM students").fetchone()["cnt"],
+                "courses": conn.execute("SELECT COUNT(*) AS cnt FROM courses").fetchone()["cnt"],
+            }
+
+        duration = time.perf_counter() - start
+        print(
+            f"Seeded data in {duration:.2f}s: "
+            f"departments={counts['departments']}, "
+            f"professors={counts['professors']}, "
+            f"students={counts['students']}, "
+            f"courses={counts['courses']}"
         )
+        return duration
+    finally:
+        conn.close()
 
 
 def reset_db() -> None:
     if DB_PATH.exists():
         try:
             DB_PATH.unlink()
-            init_db()
-            seed_db()
+            seed_db(force=True)
             return
         except PermissionError:
             pass
+    seed_db(force=True)
 
-    conn = get_connection()
-    with conn:
-        conn.executescript(DROP_SQL)
+
+def ensure_seeded() -> float:
     init_db()
-    seed_db()
+    return seed_db(force=False)
 
 
 @dataclass(frozen=True)
@@ -271,27 +372,30 @@ class CourseSummary:
 
 def fetch_course_summaries() -> Iterable[CourseSummary]:
     conn = get_connection()
-    rows = conn.execute(
-        """
-        SELECT
-          c.code,
-          c.capacity,
-          COUNT(e.id) AS enrolled_count,
-          GROUP_CONCAT(ct.day_of_week || ' ' || ct.start_time || '-' || ct.end_time, ', ') AS times
-        FROM courses c
-        LEFT JOIN enrollments e ON e.course_id = c.id
-        LEFT JOIN course_times ct ON ct.course_id = c.id
-        GROUP BY c.id
-        ORDER BY c.code
-        """
-    ).fetchall()
-    for row in rows:
-        yield CourseSummary(
-            code=row["code"],
-            capacity=row["capacity"],
-            enrolled_count=row["enrolled_count"],
-            times=row["times"] or "",
-        )
+    try:
+        rows = conn.execute(
+            """
+            SELECT
+              c.code,
+              c.capacity,
+              COUNT(e.id) AS enrolled_count,
+              GROUP_CONCAT(ct.day_of_week || ' ' || ct.start_time || '-' || ct.end_time, ', ') AS times
+            FROM courses c
+            LEFT JOIN enrollments e ON e.course_id = c.id
+            LEFT JOIN course_times ct ON ct.course_id = c.id
+            GROUP BY c.id
+            ORDER BY c.code
+            """
+        ).fetchall()
+        for row in rows:
+            yield CourseSummary(
+                code=row["code"],
+                capacity=row["capacity"],
+                enrolled_count=row["enrolled_count"],
+                times=row["times"] or "",
+            )
+    finally:
+        conn.close()
 
 
 def print_course_summary() -> None:
@@ -314,13 +418,11 @@ def main() -> None:
     if args.command == "init":
         init_db()
     elif args.command == "seed":
-        init_db()
-        seed_db()
+        seed_db(force=False)
     elif args.command == "reset":
         reset_db()
     elif args.command == "summary":
-        init_db()
-        seed_db()
+        seed_db(force=False)
         print_course_summary()
 
 
diff --git a/src/app/main.py b/src/app/main.py
index f85ac6f..d9cea78 100644
--- a/src/app/main.py
+++ b/src/app/main.py
@@ -4,7 +4,7 @@ from fastapi import FastAPI, Request
 from fastapi.exceptions import HTTPException, RequestValidationError
 from fastapi.responses import JSONResponse
 
-from .db import init_db
+from .db import ensure_seeded
 from .routers import courses, enrollments, me, professors, students
 
 app = FastAPI(title="Course Registration API")
@@ -12,7 +12,9 @@ app = FastAPI(title="Course Registration API")
 
 @app.on_event("startup")
 def on_startup() -> None:
-    init_db()
+    duration = ensure_seeded()
+    app.state.seed_duration = duration
+    app.state.data_ready = True
 
 
 @app.exception_handler(HTTPException)
diff --git a/src/app/routers/enrollments.py b/src/app/routers/enrollments.py
index 8d7cda5..f6647f8 100644
--- a/src/app/routers/enrollments.py
+++ b/src/app/routers/enrollments.py
@@ -1,7 +1,5 @@
 from __future__ import annotations
 
-from __future__ import annotations
-
 import sqlite3
 from typing import Optional
 
diff --git a/src/tests/test_concurrency_capacity.py b/src/tests/test_concurrency_capacity.py
index c27c992..16b6259 100644
--- a/src/tests/test_concurrency_capacity.py
+++ b/src/tests/test_concurrency_capacity.py
@@ -21,10 +21,12 @@ class ConcurrencyCapacityTest(unittest.TestCase):
     def test_capacity_one_concurrency(self) -> None:
         conn = db.get_connection()
         with conn:
-            course_id = conn.execute("SELECT id FROM courses WHERE code = 'CS201'").fetchone()["id"]
+            course_id = conn.execute(
+                "SELECT id FROM courses WHERE capacity = 1 ORDER BY id LIMIT 1"
+            ).fetchone()["id"]
             student_ids = [
                 row["id"]
-                for row in conn.execute("SELECT id FROM students ORDER BY id LIMIT 3").fetchall()
+                for row in conn.execute("SELECT id FROM students ORDER BY id LIMIT 100").fetchall()
             ]
         conn.close()
 
diff --git a/src/tests/test_enrollment_rules.py b/src/tests/test_enrollment_rules.py
index 4e807e3..b7f3b9a 100644
--- a/src/tests/test_enrollment_rules.py
+++ b/src/tests/test_enrollment_rules.py
@@ -14,9 +14,15 @@ from app.services.enrollment_service import cancel_enrollment, create_enrollment
 
 
 class EnrollmentRulesTest(unittest.TestCase):
-    def setUp(self) -> None:
+    @classmethod
+    def setUpClass(cls) -> None:
         db.reset_db()
+
+    def setUp(self) -> None:
         self.conn = db.get_connection()
+        with self.conn:
+            self.conn.execute("DELETE FROM enrollments")
+            self.conn.execute("DELETE FROM students WHERE name = 'Limit'")
 
     def tearDown(self) -> None:
         self.conn.close()
@@ -27,8 +33,11 @@ class EnrollmentRulesTest(unittest.TestCase):
                 "INSERT INTO students (name, max_credits) VALUES (?, ?)", ("Limit", 3)
             )
             student_id = self.conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
-            course_a = self.conn.execute("SELECT id FROM courses WHERE code = 'CS101'").fetchone()["id"]
-            course_b = self.conn.execute("SELECT id FROM courses WHERE code = 'CS201'").fetchone()["id"]
+            courses = self.conn.execute(
+                "SELECT id FROM courses WHERE credits >= 3 ORDER BY id LIMIT 2"
+            ).fetchall()
+            course_a = courses[0]["id"]
+            course_b = courses[1]["id"]
 
         create_enrollment(self.conn, student_id, course_a)
         with self.assertRaises(HTTPException) as ctx:
@@ -37,9 +46,21 @@ class EnrollmentRulesTest(unittest.TestCase):
 
     def test_time_conflict(self) -> None:
         with self.conn:
-            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Kim'").fetchone()["id"]
-            course_a = self.conn.execute("SELECT id FROM courses WHERE code = 'CS101'").fetchone()["id"]
-            course_b = self.conn.execute("SELECT id FROM courses WHERE code = 'CS102'").fetchone()["id"]
+            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
+            row = self.conn.execute(
+                """
+                SELECT t1.course_id AS course_a, t2.course_id AS course_b
+                FROM course_times t1
+                JOIN course_times t2
+                  ON t1.day_of_week = t2.day_of_week
+                 AND t1.start_time = t2.start_time
+                 AND t1.end_time = t2.end_time
+                 AND t1.course_id < t2.course_id
+                LIMIT 1
+                """
+            ).fetchone()
+            course_a = row["course_a"]
+            course_b = row["course_b"]
 
         create_enrollment(self.conn, student_id, course_a)
         with self.assertRaises(HTTPException) as ctx:
@@ -48,8 +69,8 @@ class EnrollmentRulesTest(unittest.TestCase):
 
     def test_duplicate_enrollment(self) -> None:
         with self.conn:
-            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Choi'").fetchone()["id"]
-            course_id = self.conn.execute("SELECT id FROM courses WHERE code = 'EE101'").fetchone()["id"]
+            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
+            course_id = self.conn.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()["id"]
 
         create_enrollment(self.conn, student_id, course_id)
         with self.assertRaises(HTTPException) as ctx:
@@ -58,8 +79,8 @@ class EnrollmentRulesTest(unittest.TestCase):
 
     def test_cancel_enrollment(self) -> None:
         with self.conn:
-            student_id = self.conn.execute("SELECT id FROM students WHERE name = 'Han'").fetchone()["id"]
-            course_id = self.conn.execute("SELECT id FROM courses WHERE code = 'EE201'").fetchone()["id"]
+            student_id = self.conn.execute("SELECT id FROM students ORDER BY id LIMIT 1").fetchone()["id"]
+            course_id = self.conn.execute("SELECT id FROM courses ORDER BY id LIMIT 2").fetchone()["id"]
 
         enrollment = create_enrollment(self.conn, student_id, course_id)
         cancel_enrollment(self.conn, student_id, enrollment["id"])
diff --git a/src/tests/test_seed_smoke.py b/src/tests/test_seed_smoke.py
new file mode 100644
index 0000000..eb706e7
--- /dev/null
+++ b/src/tests/test_seed_smoke.py
@@ -0,0 +1,36 @@
+from __future__ import annotations
+
+import os
+import time
+import unittest
+from pathlib import Path
+
+from fastapi.testclient import TestClient
+
+ROOT = Path(__file__).resolve().parents[2]
+os.environ["APP_DB_PATH"] = str(ROOT / "data" / "test_large.db")
+
+from app.main import app
+
+
+class SeedSmokeTest(unittest.TestCase):
+    def test_seed_and_minimum_counts(self) -> None:
+        start = time.perf_counter()
+        with TestClient(app) as client:
+            health = client.get("/health")
+            self.assertEqual(health.status_code, 200)
+
+            students = client.get("/students").json()
+            courses = client.get("/courses").json()
+            professors = client.get("/professors").json()
+
+        elapsed = time.perf_counter() - start
+
+        self.assertGreaterEqual(len(students), 10_000)
+        self.assertGreaterEqual(len(courses), 500)
+        self.assertGreaterEqual(len(professors), 100)
+        self.assertLess(elapsed, 60.0)
+
+
+if __name__ == "__main__":
+    unittest.main()
```
