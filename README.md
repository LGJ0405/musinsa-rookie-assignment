# 수강신청 시스템

## 빌드/설치
1. Python 3.10+ 설치
2. venv 생성/활성화
`python -m venv venv`
`./venv/Scripts/Activate.ps1`
3. 의존성 설치
`pip install -r requirements.txt`

## DB 초기화/시드
초기화
`python -m src.app.db init`
시드
`python -m src.app.db seed`
전체 재생성
`python -m src.app.db reset`

DB 파일은 `./data/app.db`에 생성됩니다.

## 서버 실행
`uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000`

## 접속 정보
- API Base URL: `http://localhost:8000`
- OpenAPI 문서: `http://localhost:8000/docs`
- 정적 API 문서: `docs/API.md`
