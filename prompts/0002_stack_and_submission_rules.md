당신이 사용할 기술은 Python + Fastapi 입니다.
Python 환경은 venv 를 사용할 것이며, DB 의 경우 SQlite 를 사용할 것입니다.
아래 내용을 확인하여 프로젝트 구조 및 문서 작성을 진행 후 커밋까지 완료하라
```
제출물 구조
project-root/
 README.md                  필수: 빌드 및 실행 방법
 CLAUDE.md 또는 AGENTS.md   필수: AI 에이전트 지침
 (빌드 설정 파일)            필수: build.gradle, package.json, requirements.txt 등
 docs/
    REQUIREMENTS.md        필수: 요구사항 분석 및 설계 결정
    (API 문서)             필수: API 명세
 prompts/                   필수: AI에 입력한 프롬프트 이력
    *.md
 src/                       필수: 소스 코드
필수 문서 안내
README.md
프로젝트 빌드 방법
서버 실행 방법
API 서버 접속 정보 (포트 등)
prompts/ (프롬프트 이력)
AI에 입력한 프롬프트를 제출하세요.

허용되는 형식:

프롬프트를 직접 기록한 마크다운 파일
AI 도구의 대화 내보내기 (export)
자동화된 로깅 (단, 누락되지 않도록 본인이 확인)
핵심: AI를 어떻게 활용했는지 평가자가 파악할 수 있어야 합니다. 누락 시 AI 활용 평가에서 감점됩니다.

docs/REQUIREMENTS.md
기획팀 요청사항에서 도출한 요구사항 분석
불명확한 부분에 대한 판단과 결정 사항
설계 의사결정 및 근거
docs/ 내 API 문서
구현한 API의 상세 명세
요청/응답 형식
각 상황에 대한 응답 정의
```
