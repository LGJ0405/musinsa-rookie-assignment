목표: 테스트를 내가 직접 실행해서 확인할 수 있게 저장소에 재현 가능한 형태로 남겨라.

작업:
1) docs/verification.md 파일을 새로 만들고, 아래 내용을 포함해라.
   - 실행 환경(파이썬 버전, OS 확인 명령)
   - 실행 순서(시드 reset -> health 확인 -> unittest 3~4개)
   - 기대 결과(최소 데이터 규모, 동시성 success=1 fail=99 등)
2) PowerShell 기준으로, 각 실행 결과를 docs/verification_*.txt 로 저장하는 명령 예시를 추가해라.
3) REQUIREMENTS.md의 검증 로그 섹션에는 verification.md를 참조하도록 링크/요약을 정리해라.
4) 가능하면 scripts/verify.ps1 를 추가해서 한 번에 실행 가능하게 만들어라.
   - 내부에서 PYTHONPATH 설정
   - 실패 시 종료 코드 반영

주의:
- PROBLEM.md 요구사항(health=200 이후 데이터 준비, 1분 이내 생성, 최소 데이터 규모)을 verification.md에 명확히 연결해라.
- 기존 문서와 충돌 나지 않게 맞춰라.
