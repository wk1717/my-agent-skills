---
name: github-ops
description: Automate end-to-end GitHub commit, push, and Pull Request creation workflows using Git and GitHub CLI (gh). Triggered by /github-ops, /commit, or /pr.
---

# GitHub PR & Commit Automation Skill

Use this skill when the user requests GitHub operations, such as `/github-ops`, `/commit`, or `/pr`.

## Automatic Workflow Trigger (`/github-ops`)

When the user invokes `/github-ops` (or `/commit` / `/pr`), automatically perform the complete end-to-end Git & GitHub workflow in order:

1. **Inspect Changes**: Run `git status --short`, `git diff --stat`, and check current branch with `git branch --show-current`.
2. **Branch Check & Checkout (MANDATORY)**:
   - If on `dev` branch, automatically create and switch to a new branch:
     `git checkout -b <type>/<kebab-case-description>` (e.g. `feat/deposit-settlement-fields`).
3. **Stage & Group Commits (MANDATORY - DO NOT LUMP ALL IN ONE COMMIT)**:
   - **CRITICAL**: Do NOT commit all changed files in a single monolithic commit (`git add .` into one commit).
   - Group modified files into separate logical commits by domain/feature layer:
     - Group 1 (DB/Types/Constants): e.g., `schema.sql`, `types/`, `constants.ts` -> `feat: ...` / `mod: ...`
     - Group 2 (Services/Hooks/Functions): e.g., `services/`, `hooks/`, Edge Functions -> `feat: ...` / `refactor: ...`
     - Group 3 (UI Components/Pages/CSS): e.g., `components/`, `pages/`, `index.css` -> `feat: ...` / `design: ...`
   - For each logical group, perform `git add <files>` and GPG-signed commit using `BypassSandbox: true`:
     `git commit -S -m "<type>: <description>"`.
4. **Push Branch**:
   - Push to origin: `git push -u origin <branch-name>`.
5. **Create Pull Request**:
   - Create PR targeting `--base dev` using GitHub CLI:
     `gh pr create --base dev --title "<Generated Title>" --body "<Generated Body>"`.

---

## Detailed Guidelines & Conventions

### 1. Commit Message Convention (`AGENTS.md` & Conventional Commits)
- Format: `<type>: <description>` (e.g. `feat: 입금대조 그리드 수동 보완 항목 추가`)
- Allowed Types: `feat`, `fix`, `design`, `typo`, `mod`, `add`, `del`, `refactor`, `init`, `chore`, `merge`.

### 2. PR Body Generation
Use repository template `.github/pull_request_template.md` if present:
```markdown
## 목적
- [Brief summary of the PR purpose]

## 포함 내용
- [Bullet list of key updates]

## 확인
- [x] npm run lint (0 warnings)
- [x] npx tsc -b (typecheck pass)

## 특이사항
- [Special notes or deployment warnings]
```

### 3. Branching & PR Rules
- **Base Branch**: Always target `--base dev` when creating Pull Requests. Never merge directly into `main` unless explicitly requested.
- **Never Commit directly on `dev`**: Always branch out to `<type>/<kebab-case-description>` first.

### 4. GPG Signing (MANDATORY)
- All commits MUST be GPG-signed using `-S`: `git commit -S -m "..."`.
- Always set `BypassSandbox: true` when running `git commit` so GPG key access succeeds.
