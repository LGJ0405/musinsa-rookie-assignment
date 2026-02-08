# AGENTS.md

이 저장소에서 작업하는 AI 에이전트는 다음을 지킨다.

- 기술 스택: Python, FastAPI, SQLite. venv 사용. 의존성은 `requirements.txt`로 관리.
- 구현은 `docs/REQUIREMENTS.md`와 `docs/API.md`에 기록된 정책/스펙을 우선한다.
- 동시성/정합성(정원, 중복 수강, 시간표 충돌)을 최우선으로 고려한다.
- 과도한 오버엔지니어링은 피하고, 테스트 가능하도록 로직을 분리한다.
- 모든 변경은 `src/`에 반영하고 문서를 함께 업데이트한다.
