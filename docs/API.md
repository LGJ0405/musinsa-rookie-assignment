# API 명세

## 공통
- Base URL: `http://localhost:8000`
- Content-Type: `application/json`
- 인증 헤더: `X-Student-Id`는 내 시간표/수강신청/취소에 필수

### 에러 응답 형식
```json
{
  "error": {
    "code": "STRING_CODE",
    "message": "Human readable message",
    "details": {"optional": "context"}
  }
}
```

## 1) Health Check
### GET `/health`
- 응답 200
  - 200 OK 반환 시 초기 데이터 생성이 완료된 상태임을 의미한다.
- 응답 503
  - 시드 진행 중 또는 데이터 준비 전 상태
```json
{ "status": "ok" }
```

## 2) 학생 목록
### GET `/students`
- 응답 200
```json
[
  { "id": 1, "name": "Kim", "max_credits": 18 }
]
```

## 3) 교수 목록
### GET `/professors`
- 응답 200
```json
[
  { "id": 1, "name": "Park", "department_id": 1, "department_name": "CS" }
]
```

## 4) 강좌 목록
### GET `/courses`
- Query Params
  | name | type | required | description |
  | --- | --- | --- | --- |
  | department_id | int | no | 학과 필터 |
  | semester_id | int | no | 학기 필터 |

- 응답 200
```json
[
  {
    "id": 10,
    "code": "CS101",
    "name": "Intro to CS",
    "credits": 3,
    "department_id": 1,
    "department_name": "CS",
    "professor_id": 1,
    "professor_name": "Park",
    "semester_id": 1,
    "capacity": 30,
    "enrolled_count": 12,
    "schedule": [
      { "day": "MON", "start": "09:00", "end": "10:15" },
      { "day": "WED", "start": "09:00", "end": "10:15" }
    ]
  }
]
```

## 5) 내 시간표
### GET `/me/timetable`
- Headers
  | name | required | description |
  | --- | --- | --- |
  | X-Student-Id | yes | 학생 ID |

- Query Params
  | name | type | required | description |
  | --- | --- | --- | --- |
  | semester_id | int | no | 미지정 시 시작일이 가장 최근인 학기 사용 |

- 응답 200
```json
{
  "student_id": 1,
  "semester_id": 1,
  "total_credits": 6,
  "items": [
    {
      "enrollment_id": 100,
      "course_id": 10,
      "code": "CS101",
      "name": "Intro to CS",
      "credits": 3,
      "schedule": [
        { "day": "MON", "start": "09:00", "end": "10:15" }
      ]
    }
  ]
}
```
- 응답 400: `INVALID_STUDENT_HEADER`
- 응답 404: `STUDENT_NOT_FOUND`, `SEMESTER_NOT_FOUND`

## 6) 수강신청
### POST `/enrollments`
- Headers
  | name | required | description |
  | --- | --- | --- |
  | X-Student-Id | yes | 학생 ID |

- 요청
```json
{ "course_id": 10 }
```
- 응답 201
```json
{ "id": 100, "student_id": 1, "course_id": 10, "semester_id": 1, "created_at": "2026-02-08T12:00:00Z" }
```

- 응답 400: `INVALID_STUDENT_HEADER`, `VALIDATION_ERROR`
- 응답 404: `COURSE_NOT_FOUND`, `STUDENT_NOT_FOUND`
- 응답 409:
  - `CAPACITY_FULL`
  - `DUPLICATE_ENROLLMENT`
  - `TIME_CONFLICT`
  - `CREDIT_LIMIT_EXCEEDED`

## 7) 수강취소
### DELETE `/enrollments/{enrollment_id}`
- Headers
  | name | required | description |
  | --- | --- | --- |
  | X-Student-Id | yes | 학생 ID |

- 응답 204
- 응답 400: `INVALID_STUDENT_HEADER`
- 응답 403: `FORBIDDEN_ENROLLMENT_CANCEL`
- 응답 404: `ENROLLMENT_NOT_FOUND`
