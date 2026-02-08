# API 명세

## 공통
- Base URL: `http://localhost:8000`
- Content-Type: `application/json`

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
```json
{ "status": "ok" }
```

## 2) 학생
### POST `/students`
- 요청
```json
{ "name": "Kim", "max_credits": 18 }
```
- 응답 201
```json
{ "id": 1, "name": "Kim", "max_credits": 18 }
```

### GET `/students/{student_id}`
- 응답 200
```json
{ "id": 1, "name": "Kim", "max_credits": 18 }
```
- 응답 404: `STUDENT_NOT_FOUND`

### GET `/students/{student_id}/enrollments`
- 응답 200
```json
[
  {
    "id": 10,
    "section_id": 3,
    "course_code": "CS101",
    "term_id": 1,
    "created_at": "2026-02-08T12:00:00Z"
  }
]
```

## 3) 학기
### POST `/terms`
- 요청
```json
{ "name": "2026 Spring", "start_date": "2026-03-01", "end_date": "2026-06-30" }
```
- 응답 201
```json
{ "id": 1, "name": "2026 Spring", "start_date": "2026-03-01", "end_date": "2026-06-30" }
```

## 4) 과목
### POST `/courses`
- 요청
```json
{ "code": "CS101", "name": "Intro to CS", "credits": 3 }
```
- 응답 201
```json
{ "id": 1, "code": "CS101", "name": "Intro to CS", "credits": 3 }
```
- 응답 409: `COURSE_CODE_CONFLICT`

## 5) 분반
### POST `/sections`
- 요청
```json
{
  "course_id": 1,
  "term_id": 1,
  "section_no": "001",
  "capacity": 30,
  "schedule": [
    { "day": "MON", "start": "09:00", "end": "10:15" },
    { "day": "WED", "start": "09:00", "end": "10:15" }
  ]
}
```
- 응답 201
```json
{ "id": 3, "course_id": 1, "term_id": 1, "section_no": "001", "capacity": 30 }
```

### GET `/sections`
- Query Params: `term_id`, `course_code`, `available_only`(true|false)
- 응답 200
```json
[
  {
    "id": 3,
    "course_id": 1,
    "course_code": "CS101",
    "term_id": 1,
    "section_no": "001",
    "capacity": 30,
    "enrolled_count": 12,
    "schedule": [
      { "day": "MON", "start": "09:00", "end": "10:15" }
    ]
  }
]
```

## 6) 수강신청
### POST `/enrollments`
- 요청
```json
{ "student_id": 1, "section_id": 3 }
```
- 응답 201
```json
{ "id": 10, "student_id": 1, "section_id": 3, "created_at": "2026-02-08T12:00:00Z" }
```
- 응답 404: `STUDENT_NOT_FOUND`, `SECTION_NOT_FOUND`
- 응답 409:
  - `CAPACITY_FULL`
  - `DUPLICATE_COURSE`
  - `TIME_CONFLICT`
  - `CREDIT_LIMIT_EXCEEDED`

### DELETE `/enrollments/{enrollment_id}`
- 응답 204
- 응답 404: `ENROLLMENT_NOT_FOUND`
