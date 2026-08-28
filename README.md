# My Agent Skills Repository

AI 에이전트(**Claude Code** & **Antigravity / AGY**)용 개인 커스텀 스킬 모음 저장소입니다.

Standard Agent Skills 스펙(`SKILL.md` + YAML 헤더)을 준수하며, 심볼릭 링크(symlink)를 통해 **Claude Code**와 **Antigravity(AGY)** 양쪽에 동기화되어 동작합니다.

---

## 🛠️ Skills

1. **`audit-webapp-security`**
   - **설명**: 웹서비스 코드베이스 증거 기반 다각도 보안 감사 스킬 (인증/세션, API, DB, 비밀정보, XSS, 업로드 등 점검)
   - **포함 자료**: 세부 체크리스트(`references/review-checklist.md`), 보고서 양식(`references/report-format.md`)
2. **`github-ops`**
   - **설명**: Git & GitHub CLI(`gh`) 기반 자동 커밋, 푸시, PR 생성 워크플로우
3. **`frontend-design`**
   - **설명**: 고품질 프론트엔드 UI 디자인 및 컴포넌트 생성 가이드
4. **`find-skills`**
   - **설명**: 에이전트 스킬 생태계(`npx skills`) 탐색 도구
5. **`skill-creator`**
   - **설명**: 새로운 `SKILL.md` 스킬 작성 및 검증 메타 도구
6. **`insights`**
   - **설명**: Antigravity / Claude Code 대화 로그와 git 히스토리를 분석해 인터랙티브 HTML 세션 인사이트 대시보드 생성
   - **포함 자료**: 리포트 생성 스크립트(`scripts/generate_insights.py`), 평가셋(`evals/evals.json`)
7. **`compact`** *(AGY 전용)*
   - **설명**: 현재 대화 맥락(목표/변경 파일/기술적 결정/남은 과제)을 구조화된 요약으로 압축
   - **참고**: Claude Code에는 동명의 내장 `/compact` 명령이 있어 링크하지 않습니다.

---

## ⚙️ 스킬이 아닌 도구

- **`statusline`**
  - **설명**: 입력창 위에 한 줄 상태바 표시 — 🤖 모델 / 🧠 Effort / 📊 컨텍스트 사용률 / 💳 `/usage` 레이트리밋(5시간 · 7일, 초기화 절대 시각)
  - **대상**: Claude Code + AGY 양쪽 버전 포함
  - **설치**: `cd statusline && ./install.sh` — 각 `settings.json`의 `statusLine` 키만 병합하고 나머지 설정은 보존합니다
  - 한 번 설치하면 끝나는 설정물이라 `SKILL.md`가 없고, 심볼릭 링크도 필요 없습니다. 자세한 내용은 [`statusline/README.md`](statusline/README.md)

---

## 🔗 연동 및 동기화 설정 (Symlinks)

### 1. Antigravity (AGY / Gemini CLI)
```bash
mkdir -p ~/.gemini/config/skills
ln -s ~/projects/my-agent-skills/audit-webapp-security ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/github-ops ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/frontend-design ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/find-skills ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/skill-creator ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/insights ~/.gemini/config/skills/
ln -s ~/projects/my-agent-skills/compact ~/.gemini/config/skills/
```

### 2. Claude Code
```bash
mkdir -p ~/.claude/skills
ln -s ~/projects/my-agent-skills/audit-webapp-security ~/.claude/skills/
ln -s ~/projects/my-agent-skills/github-ops ~/.claude/skills/
ln -s ~/projects/my-agent-skills/frontend-design ~/.claude/skills/
ln -s ~/projects/my-agent-skills/find-skills ~/.claude/skills/
ln -s ~/projects/my-agent-skills/skill-creator ~/.claude/skills/
ln -s ~/projects/my-agent-skills/insights ~/.claude/skills/
```
> `compact`은 Claude Code 내장 `/compact` 명령과 이름이 겹치므로 AGY에만 링크합니다.

---

## 💡 사용 방법 (2가지 호출 방식)

### 1️⃣ 슬래시 명령어 / 스킬명 직접 지정 (추천 ⚡)
AI 대화창에 슬래시(`/`) 또는 스킬 이름을 직접 지정하면 AI가 해당 스킬 지침을 100% 우선 로드합니다:
- `/github-ops` 또는 `github-ops 스킬로 PR 올려줘`
- `/audit-webapp-security` 또는 `audit-webapp-security 스킬 실행해줘`
- `/frontend-design` 또는 `frontend-design 지침 적용해줘`
- `/insights` 또는 `insights 스킬로 세션 리포트 만들어줘`
- `/compact` 또는 `대화 맥락 요약해줘`

### 2️⃣ 자연어 유도 방식 (Natural Language Trigger)
스킬 이름을 몰라도 관련 대화를 건네면 에이전트가 `SKILL.md` 헤더의 `description` 키워드를 인식하여 자동 발동합니다:
- *"웹 보안 점검 수행해줘"* -> `audit-webapp-security` 자동 트리거
- *"이슈 12번 커밋하고 PR 올려줘"* -> `github-ops` 자동 트리거
- *"React 스킬 검색해줘"* -> `find-skills` 자동 트리거
- *"이번 주 세션 활동 분석해줘"* -> `insights` 자동 트리거
- *"지금까지 내용 정리하고 다음 할 일 알려줘"* -> `compact` 자동 트리거

