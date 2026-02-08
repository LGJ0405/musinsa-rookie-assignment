# 요구사항 분석 및 설계 결정

## A. 요구사항 요약(현재 확정된 것만)
- 수강신청 시스템을 Python + FastAPI + SQLite로 구현한다.
- 제출물 구조를 준수하고 문서와 프롬프트 이력을 포함한다.
- 조회 API는 학생/교수/강좌 목록과 내 시간표를 제공한다.
- 수강신청은 정원, 학점, 시간표 중복, 중복 신청을 검증한다.
- 인증은 `X-Student-Id` 헤더로 단순화한다.

## B. 모호/누락 항목 리스트(결정 필요)
- 학기(semester) 범위 및 기본 선택 기준
- 강좌와 과목의 구분(분반/강좌 구조)
- 수강신청 취소 이력 보존 여부
- 교수/학과 정보의 공개 범위
- 대기열, 선수과목, 수강기간 제한 적용 여부

## C. 내가 채택한 가정/정책(선택지와 이유 포함)
- 학기 기본값: `semester_id`가 없으면 **내 시간표 조회**에서 시작일이 가장 최근인 학기를 사용한다. 강좌 목록은 필터 미지정 시 전체를 반환한다.
  - 이유: 클라이언트 입력을 줄이면서도 결정 기준이 명확하다.
- 강좌 모델: 학기 단위 강좌(강좌 자체가 학기와 일정/정원을 가진다).
  - 이유: 과제 범위를 단순화하면서도 시간표/정원 검증에 충분하다.
- 인증: `X-Student-Id` 헤더를 필수로 받고 별도 로그인은 구현하지 않는다.
  - 이유: 요구사항에서 인증을 단순화하도록 명시되었다.
- 정원 정책: 정원 초과는 절대 허용하지 않으며, 대기열은 제공하지 않는다.
  - 이유: 핵심 규칙을 우선 구현하고 범위를 제한한다.
- 중복 신청: `(student_id, course_id, semester_id)` 유니크 제약으로 차단한다.
  - 이유: DB 차원에서 정합성을 보장한다.
- 시간표 충돌: 동일 학기에서 요일/시간이 겹치는 강좌는 신청 불가.
  - 이유: 현실적인 제약이며 최소한의 로직으로 검증 가능하다.
- 최대 학점: 학생별 최대 18학점, 초과 시 거절.
  - 이유: 일반적인 학사 정책이며 단순 합계로 검증 가능하다.
- 취소 정책: 수강신청 취소 시 Enrollment를 삭제하며 별도 이력은 남기지 않는다.
  - 이유: 과제 범위 밖 기능을 배제한다.

## D. 주요 데이터 모델/도메인 용어 정의
- Student
  - `id`, `name`, `max_credits`
- Professor
  - `id`, `name`, `department_id`
- Department
  - `id`, `name`
- Semester
  - `id`, `name`, `start_date`, `end_date`
- Course
  - `id`, `department_id`, `professor_id`, `semester_id`, `code`, `name`, `credits`, `capacity`
- CourseTime
  - `id`, `course_id`, `day_of_week`, `start_time`, `end_time`
- Enrollment
  - `id`, `student_id`, `course_id`, `semester_id`, `created_at`
  - 유니크: `(student_id, course_id, semester_id)`

## E. 동시성/정합성 전략(핵심)
- SQLite 트랜잭션을 `BEGIN IMMEDIATE`로 시작하여 동시에 쓰기 경합 시 하나만 진행되도록 한다.
- 같은 트랜잭션에서 정원, 중복, 학점, 시간표를 검증하고 조건을 만족할 때만 Enrollment를 생성한다.
- DB 제약(유니크)과 애플리케이션 검증을 함께 사용해 중복 신청을 방지한다.
- `journal_mode=WAL`을 사용해 읽기/쓰기 동시성을 개선한다.
- SQLite는 단일 writer 제약이 있으므로 고부하 환경에서는 DB 락 대기/지연이 발생할 수 있다.
  - 보완 전략: 프로덕션에서는 PostgreSQL 같은 다중 writer DB로 전환하거나, 신청 요청을 큐로 직렬화한다.

## F. 구현 범위
- MVP
  - 학생/교수/강좌 목록 조회
  - 내 시간표 조회
  - 수강신청/취소
  - 정원/학점/시간표/중복 검증
  - SQLite 파일 DB 초기화 및 시드
- 제외
  - 로그인/권한, 대기열, 선수과목, 수강기간 제한, 성적/수강료, 감사 이력

## 검증 로그
- Step3 DB 시드 확인: `python -m app.db summary` 실행
  - CS101 capacity=2 enrolled=0 times=MON 09:00-10:15, WED 09:00-10:15
  - CS102 capacity=2 enrolled=0 times=MON 09:30-10:45, WED 09:30-10:45
  - CS201 capacity=1 enrolled=0 times=TUE 13:00-14:15, THU 13:00-14:15
  - EE101 capacity=2 enrolled=0 times=MON 10:30-11:45, WED 10:30-11:45
  - EE201 capacity=2 enrolled=0 times=WED 09:00-10:15, FRI 09:00-10:15
- Step4 스모크 테스트: 서버 실행 후 curl 호출
  - GET /health -> {"status":"ok"}
  - GET /students -> 3명 반환
  - GET /courses -> 5개 강좌 반환 (정원/현재인원/시간 포함)
  - GET /me/timetable (X-Student-Id: 1) -> semester_id=2, items=[]
- Step5 규칙 테스트: `python -m unittest src/tests/test_enrollment_rules.py`
  - credit limit / time conflict / duplicate / cancel 검증 OK
- Step6 동시성 테스트: `python -m unittest src/tests/test_concurrency_capacity.py`
  - success=1 fail=2 enrolled_count=1
