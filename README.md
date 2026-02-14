# 수강신청 시스템

## 빌드/설치 (Windows / PowerShell)
1. Python 3.10+ 설치
2. venv 생성/활성화
    ```shell
    python -m venv venv
    ```
    ```shell
    ./venv/Scripts/Activate.ps1
    ```
3. 의존성 설치
    ```
    pip install -r requirements.txt
    ```

## DB 초기화/시드
- 서버 시작 시 자동으로 초기 데이터가 생성됩니다.
- 데이터가 이미 최소 규모를 만족하면 재생성하지 않습니다.

수동 초기화/재생성(필요 시):
```
$env:PYTHONPATH="src"; python -m app.db reset
```

DB 파일은 `./data/app.db`에 생성됩니다.

## 서버 실행
```shell
uvicorn app.main:app --app-dir src --reload --host 0.0.0.0 --port 8000
```
초기 시드 생성은 최대 1분 이내에 완료되며, `/health`가 200을 반환하는 시점에는 데이터가 준비된 상태입니다.

## 테스트 실행
- StepA 대규모 시드 생성: 
    ```shell
    python -m app.db reset
    ```
    - Seeded data in 6.56s: departments=12, professors=100, students=10000, courses=500
- StepB 시드 스모크 테스트: 
    ```shell
    python -m unittest src/tests/test_seed_smoke.py
    ```
    - /health 200 이후 학생/교수/강좌 최소 수량 이상 확인
- StepC 규칙 테스트: 
    ```shell
    python -m unittest src/tests/test_enrollment_rules.py
    ```
    - credit limit / time conflict / duplicate / cancel 검증 OK
- StepD 동시성 테스트(100 동시): 
    ```shell
    python -m unittest src/tests/test_concurrency_capacity.py
    ```
    - success=1 fail=99 enrolled_count=1

## 접속 정보
- API Base URL: `http://localhost:8000`
- OpenAPI 문서: `http://localhost:8000/docs`
- 정적 API 문서: [docs/API.md](./docs/API.md)