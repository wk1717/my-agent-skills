# My Agent Skills Repository

AI 에이전트(**Claude Code** & **Antigravity / AGY**)용 개인 커스텀 스킬 모음 저장소입니다.

Standard Agent Skills 스펙(`SKILL.md` + YAML 헤더)을 준수하며, 심볼릭 링크(symlink)를 통해 **Claude Code**와 **Antigravity(AGY)** 양쪽에 동기화되어 동작합니다.

---

## 🛠️ 포함된 스킬 목록

1. 🛡️ **`audit-webapp-security`**
   - **설명**: 웹서비스 코드베이스 증거 기반 다각도 보안 감사 스킬 (인증/세션, API, DB, 비밀정보, XSS, 업로드 등 점검)
   - **포함 자료**: 세부 체크리스트(`references/review-checklist.md`), 보고서 양식(`references/report-format.md`)
2. 🐙 **`github-ops`**
   - **설명**: Git & GitHub CLI(`gh`) 기반 자동 커밋, 푸시, PR 생성 워크플로우
3. 🎨 **`frontend-design`**
   - **설명**: 고품질 프론트엔드 UI 디자인 및 컴포넌트 생성 가이드
4. 🔍 **`find-skills`**
   - **설명**: 에이전트 스킬 생태계(`npx skills`) 탐색 도구
5. 📝 **`skill-creator`**
   - **설명**: 새로운 `SKILL.md` 스킬 작성 및 검증 메타 도구

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
```

### 2. Claude Code
```bash
mkdir -p ~/.claude/skills
ln -s ~/projects/my-agent-skills/audit-webapp-security ~/.claude/skills/
ln -s ~/projects/my-agent-skills/github-ops ~/.claude/skills/
ln -s ~/projects/my-agent-skills/frontend-design ~/.claude/skills/
ln -s ~/projects/my-agent-skills/find-skills ~/.claude/skills/
ln -s ~/projects/my-agent-skills/skill-creator ~/.claude/skills/
```

---

## 💡 사용 방법

에이전트(Claude Code / AGY)와 대화 시 자연어로 요청합니다:

- *"웹 보안 점검 수행해줘"* -> `audit-webapp-security` 실행
- *"PR 올려줘 / 커밋해줘"* -> `github-ops` 실행
- *"UI 디자인 개선해줘"* -> `frontend-design` 실행
- *"React 스킬 검색해줘"* -> `find-skills` 실행
- *"새 스킬 만들어줘"* -> `skill-creator` 실행
