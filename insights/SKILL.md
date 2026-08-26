---
name: insights
description: Generate an interactive visual Session Insights Report and analytics dashboard from Antigravity and Claude Code conversation logs and git history. Use this skill whenever the user types /insights, asks for a session report (세션 보고서), activity analysis (활동 분석), usage statistics (대화 통계/사용량), developer insights (인사이트 리포트), or wants to identify repetitive workflows to turn into custom skills, hooks, or subagents.
---

# Session Insights Skill (/insights)

Analyze AI coding agent sessions (Antigravity transcripts, Claude Code logs, and Git repository history) to produce an interactive, comprehensive HTML Session Insights Dashboard modeled after Anthropic's Claude Code Insights report.

## When to Use

Trigger this skill whenever the user:
- Types `/insights` or `/session-report`
- Asks for "세션 보고서", "인사이트 보고서", "활동 분석", "대화 통계", "세션 요약 리포트"
- Asks to identify repetitive commands/workflows and convert them into reusable custom skills (`skill-creator`), hooks, or subagents.
- Asks for productivity tips, friction analysis, or AGENTS.md rule recommendations based on past sessions.

## Workflow

### 1. Execute the Insights Generator Script

Run the bundled Python script to parse session logs, compute statistics, render the self-contained HTML report, and open it in the default browser:

```bash
python3 /Users/smk/projects/my-agent-skills/insights/scripts/generate_insights.py
```

#### Optional CLI Options
- `--source <all|antigravity|claude>`: Filter by session source (default: `all`)
- `--days <N>`: Filter sessions within the last N days (e.g. `--days 7` for weekly insights)
- `--no-open`: Skip automatic browser launch (useful in headless/CI environments)
- `--json-summary`: Output structured JSON for parsing

### 2. Present Key Highlights in Chat

After generating the report, output a clean, concise executive summary in the chat:

```markdown
### 📊 AI 코딩 에이전트 세션 인사이트 보고서가 생성되었습니다!

- 🗓️ **분석 기간**: {시작일} ~ {종료일} ({활성 일수}일간)
- 💬 **총 세션 / 메시지**: {세션 수}개 세션 / {총 메시지 수}개 사용자 메시지 ({총 시간}시간)
- 💻 **코드 라인 증감**: +{추가 라인} / -{삭제 라인} 줄 ({수정된 파일 수}개 파일)
- 🌐 **보고서 위치**: [{report.html}](file://{절대경로})

#### 📌 핵심 요약
1. **주요 도메인**: {가장 많이 작업한 도메인}
2. **반복 작업 스킬화 제안**:
   - `/verify` (린트+타입체크+DB스키마 일괄 검증 스킬)
   - `debug-sheet-failure` (하드코딩 테넌트 값 및 로그 조사 서브에이전트)
3. **AGENTS.md 추가 추천 규칙**:
   - {증거 기반 디버깅, 사전 질문 지침 등}

브라우저에 보고서가 자동으로 열렸습니다. 브라우저에서 인터랙티브 차트, 시간대별 활동, AGENTS.md 규칙 원클릭 복사, 반복 작업 스킬 생성 스크립트, 세션 로그 탐색기를 확인하실 수 있습니다.
```

### 3. Progressive Customization & Skill Scaffolding

If the user wants to convert a recommended pattern into a real skill or subagent:
- Invoke `/skill-creator` or create the skill directory directly in `/Users/smk/projects/my-agent-skills/<skill-name>`.
- Offer to update `AGENTS.md` directly with the recommended rules.
