# Verification Guide

## Purpose (PROBLEM.md 연결)
- `/health`가 200을 반환하는 시점에는 초기 데이터가 이미 준비되어 있어야 한다.
- 초기 데이터 생성은 1분 이내에 완료되어야 한다.
- 최소 데이터 규모는 Department >= 10, Professor >= 100, Student >= 10,000, Course >= 500을 만족해야 한다.
- 동시성 테스트는 정원 1 남은 강좌에 대해 success=1, fail=99를 기대한다.
- 인코딩 리스크를 줄이기 위해 `docs/PROBLEM.md`는 제출물에 포함하지 않는다. 심사자는 원본 과제의 PROBLEM.md를 기준으로 한다.

## Environment 확인 명령
1. `python --version`
2. `$PSVersionTable.PSVersion`
3. `Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture`

## 실행 순서(수동)
1. venv 활성화(필요 시): `./venv/Scripts/Activate.ps1`
2. `PYTHONPATH` 설정: `$env:PYTHONPATH="src"`
3. 시드 reset: `python -m app.db reset`
4. 서버 실행: `python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8000`
5. health 확인: `Invoke-WebRequest http://127.0.0.1:8000/health`
6. 유닛 테스트 3개 실행
7. 서버 종료(Ctrl+C)

참고:
- `python -m app.db reset`은 재현성을 위한 선택 단계(권장)이며, 생략해도 서버 시작 시 자동 시드가 수행된다.
- 서버 실행만으로도 `/health` 200 시점에 데이터가 준비됨을 확인한다.

## 실행 결과 저장 예시(PowerShell)
1. 환경 정보 저장
```
python --version 2>&1 | Tee-Object -FilePath docs/verification_env.txt
$PSVersionTable.PSVersion | Out-File -Append -Encoding utf8 docs/verification_env.txt
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, OSArchitecture | Out-String | Out-File -Append -Encoding utf8 docs/verification_env.txt
```
2. 시드 reset 로그 저장
```
python -m app.db reset 2>&1 | Tee-Object -FilePath docs/verification_seed.txt
```
3. health 응답 저장
```
Invoke-WebRequest http://127.0.0.1:8000/health | Select-Object StatusCode, Content | Out-File -Encoding utf8 docs/verification_health.txt
```
4. 유닛 테스트 로그 저장
```
python -m unittest src/tests/test_seed_smoke.py 2>&1 | Tee-Object -FilePath docs/verification_seed_smoke.txt
python -m unittest src/tests/test_enrollment_rules.py 2>&1 | Tee-Object -FilePath docs/verification_rules.txt
python -m unittest src/tests/test_concurrency_capacity.py 2>&1 | Tee-Object -FilePath docs/verification_concurrency.txt
```

## 기대 결과
- `python -m app.db reset` 로그에 생성 소요 시간과 최소 데이터 규모가 출력된다.
- `/health` 응답은 200이며, 시드 완료 이후에만 200을 반환한다.
- `/health` 200은 서버 시작 후 1분 이내에 확인되어야 한다.
- `test_seed_smoke`는 최소 데이터 규모를 확인한다.
- `test_concurrency_capacity`는 success=1, fail=99, enrolled_count=1을 검증한다.

## 단일 실행 스크립트
- `scripts/verify.ps1`는 위 순서를 자동으로 수행하고 `docs/verification_*.txt` 로그를 생성한다.
- 실패 시 종료 코드가 0이 아닌 값으로 종료된다.
- `venv/Scripts/python.exe`가 존재하면 해당 파이썬을 사용한다.
