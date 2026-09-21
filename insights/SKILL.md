---
name: agy-insights
description: Antigravity 세션 로그와 git 히스토리로 인터랙티브 HTML 세션 인사이트 대시보드를 만든다. 사용자가 /agy-insights를 치거나 "Antigravity 세션 보고서", "AG 활동 분석", "안티그래비티 대화 통계"를 요청할 때, 또는 Antigravity 작업에서 반복되는 워크플로를 찾아 커스텀 스킬·훅·서브에이전트로 만들려 할 때 쓴다. Claude Code 세션 분석은 내장 /insights가 맡으므로 이 스킬을 쓰지 않는다.
---

# Session Insights Skill (/agy-insights)

Antigravity 트랜스크립트와 git 히스토리를 분석해 인터랙티브 HTML 세션 인사이트 대시보드를 만든다. Anthropic의 Claude Code Insights 보고서 형식을 본떴다.

**Claude Code 세션은 이 스킬이 다루지 않는다.** Claude Code에는 내장 `/insights`가 있고 보고서가 `~/.claude/usage-data/report.html`에 저장된다. Claude Code 세션 분석을 요청받으면 내장 `/insights`를, 토큰·비용은 `/usage`를 안내한다. 이 스킬은 Antigravity 전용이다(스크립트에 `--source claude`가 남아 있지만 기본값은 Antigravity다).

## When to Use

Trigger this skill whenever the user:
- Types `/agy-insights`
- Asks for "Antigravity 세션 보고서", "AG 활동 분석", "안티그래비티 대화 통계"
- Asks to identify repetitive commands/workflows and convert them into reusable custom skills (`skill-creator`), hooks, or subagents.
- Asks for productivity tips, friction analysis, or AGENTS.md rule recommendations based on past sessions.

## Workflow

### 1. Execute the Insights Generator Script

Run the bundled Python script to parse session logs, compute statistics, render the self-contained HTML report, and open it in the default browser:

```bash
python3 /Users/smk/projects/my-agent-skills/insights/scripts/generate_insights.py --source antigravity
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
