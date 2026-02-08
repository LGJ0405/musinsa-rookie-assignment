당신은 이 저장소를 감점 리스크 제거 목적만으로 최소 수정하라. (기능 확장 금지)

목표: 아래 감점 가능 포인트를 제거하고, 수정 후 테스트/검증 로그까지 남겨라.

필수 수정 항목(우선순위 순):

1) docs/PROBLEM.md 인코딩 리스크 제거
- 제출물에 docs/PROBLEM.md가 존재한다면:
  - (권장) 파일을 제거한다. 원본 과제 PROBLEM.md는 심사자가 보유하므로 제출물에 중복 포함할 필요가 없다.
  - 또는 UTF-8로 변환해서 한글이 깨지지 않게 한다.
- 어떤 선택을 했는지 docs/verification.md 또는 README.md에 1~2문장으로 명시해라.

2) 시드 데이터 토큰 모지박 제거 (src/app/db.py 또는 시드 모듈)
- 학과/이름/과목 토큰 목록에서 깨진 문자열(모지박)을 모두 제거하고,
  UTF-8에서 정상 표시되는 현실적인 토큰(한글 또는 ASCII)으로 교체하라.
- "User1", "Course1" 같은 의미 없는 더미 패턴 금지.
- 교체 후 /students, /courses에서 사람이 보기에 자연스러운 값이 나오도록 한다.

3) docs/verification.md 문서 보완 (reset 전제 오해 제거)
- 실행 순서를 다음 의미로 정리하라:
  - `python -m app.db reset`은 재현성을 위한 선택 단계(권장)이며,
  - 서버 실행만으로도 자동 시드가 수행되고 `/health` 200 시점에 데이터가 준비됨을 명시한다.
- 문장 2~4줄 추가/수정으로 충분하다.

4) 스모크 테스트 보강 (요구사항 증빙 강화)
- src/tests/test_seed_smoke.py에 Department 최소 수(>=10) 검증 assert를 추가하라.
- 기존 students/professors/courses 최소 수 검증이 있다면 동일 스타일로 맞춰라.

5) 동시성 테스트 보강 (증명력 강화)
- src/tests/test_concurrency_capacity.py에서 동시 시작을 보장하도록 동기화 장치(threading.Barrier 또는 동등)를 추가하라.
- 결과를 명시적으로 assert 하라:
  - success_count == 1
  - fail_count == 99
  - enrolled_count == 1

선택(가능하면 적용):
6) /health 문서-코드 정합성
- 문서에는 /health 200은 시드 완료로 정의돼 있으므로,
  코드에서 seed 완료 상태 플래그를 도입해 응답 의미를 더 명확히 하라.
- 단, 현재 구조상 startup 이후 요청만 받는다면 최소 변경으로 일관성만 확보해라(과도한 리팩토링 금지).

검증/증빙(필수):
- 위 변경 후 다음을 실제 실행하고 출력 로그를 파일로 저장하라:
  - python -m app.db reset  -> docs/verification_seed.txt
  - python -m unittest src/tests/test_seed_smoke.py -> docs/verification_seed_smoke.txt
  - python -m unittest src/tests/test_enrollment_rules.py -> docs/verification_rules.txt
  - python -m unittest src/tests/test_concurrency_capacity.py -> docs/verification_concurrency.txt
- 로그 파일에는 최소 데이터 규모(Department/Professor/Student/Course), 생성 시간(1분 이내), 동시성 success/fail/enrolled_count가 보이도록 하라.
  (필요하면 테스트에서 print/log 추가)

출력 요구:
- 변경된 파일 목록
- 각 변경의 의도(감점 리스크 제거 관점) 1~2줄 요약
- 재실행 방법(한 줄 커맨드) 안내

주의:
- 기능 추가, 새로운 엔드포인트 추가, 요구사항 밖 기능 구현 금지.
- 기존 API 스펙/문서(README, REQUIREMENTS, API.md)와 모순 생기지 않게 유지.
