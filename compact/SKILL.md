---
name: compact
description: Summarize and compress the current conversation context, key user requests, modified files, technical decisions, and pending tasks. Use this skill whenever the user types /compact, asks to summarize/compress the conversation history, clean up context, or reset focus to next steps.
---

# Compact (Context Compression & Summarization)

This skill summarizes the ongoing conversation history, key user requirements, technical decisions, modified files, and remaining tasks to keep the context clean, focused, and token-efficient.

## Important Rule: Output Format
- **DO NOT** create or save the summary to a `.md` file on disk.
- Output the clean, structured summary **directly in the chat response**.

---

## Summarization Workflow

When triggered by `/compact` or a request to compress context, execute the following steps:

### 1. Analyze Conversation State
Review the conversation history and extract:
- **Core Goal**: The primary task or project objective.
- **Key User Requirements & Constraints**: Specific user choices, preferences, or technical constraints.
- **Completed Work & File Changes**: List of files created/modified and summary of changes made.
- **Key Technical Decisions**: Important decisions, architecture choices, or debugging findings.
- **Pending Tasks & Next Steps**: What needs to be done next.

### 2. Output Compact Summary Template
Format the summary in the chat using the following structure:

```markdown
## 🧹 Context Compact Summary

### 🎯 1. 핵심 목적 및 요구사항 (Core Goal)
- [목적 및 주요 요구사항 요약]

### 📁 2. 작업 및 파일 변경 내역 (Completed Work)
- `path/to/file.ext`: [주요 수정사항 요약]
- `path/to/another_file.ext`: [주요 수정사항 요약]

### 💡 3. 주요 결정 및 현재 상태 (Key Decisions & Status)
- [기술적 결정 사항 및 파악된 주요 정보]

### 📌 4. 다음 수행 과제 (Next Steps)
1. [남은 과제 1]
2. [남은 과제 2]
```

### 3. Transition to Compacted State
After displaying the summary, inform the user:
> "대화 맥락이 성공적으로 요약 정돈되었습니다. 이후 작업은 위 요약된 컨텍스트를 기준으로 진행합니다."
