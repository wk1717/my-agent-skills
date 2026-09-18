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
3. **Security & Secret Leak Pre-check (MANDATORY)**:
   - Before staging/committing, inspect `git status` and `git diff` for sensitive information:
     - **Environment & Config Files**: Ensure real `.env`, `.env.local`, `.env.bak*`, `credentials.json` are NOT tracked/staged (only `.env.example` with dummy values is allowed).
     - **API Keys & Secrets**: Coupang secret keys, Sabangnet API keys, AWS credentials, JWT tokens, DB connection strings with passwords, Google Chat/Slack webhook URLs.
     - **Private Keys & Certificates**: `*.pem`, `*.key`, `id_rsa*`, GPG private keys.
     - **Customer/Personal Data (PII)**: Real customer names, phone numbers, addresses, personal custom clearance codes in test fixtures or mock files.
     - **Runtime & Scratch Outputs**: `runtime/`, `work/`, `logs/`, `*.log`, `*.bak`, `*.tmp` must be properly ignored.
   - If any potential secret or untracked sensitive file is found:
     - **STOP** committing immediately.
     - Add the pattern to `.gitignore` or replace real credentials with dummy placeholders before proceeding.
4. **Stage & Group Commits (MANDATORY - DO NOT LUMP ALL IN ONE COMMIT)**:
   - **CRITICAL**: Do NOT commit all changed files in a single monolithic commit (`git add .` into one commit).
   - Group modified files into separate logical commits by domain/feature layer:
     - Group 1 (DB/Types/Constants): e.g., `schema.sql`, `types/`, `constants.ts` -> `feat: ...` / `mod: ...`
     - Group 2 (Services/Hooks/Functions): e.g., `services/`, `hooks/`, Edge Functions -> `feat: ...` / `refactor: ...`
     - Group 3 (UI Components/Pages/CSS): e.g., `components/`, `pages/`, `index.css` -> `feat: ...` / `design: ...`
     - Group 4 (Tests/Docs/Config): e.g., `tests/`, `docs/`, `README.md`, `.env.example` -> `test: ...` / `docs: ...` / `chore: ...`
   - For each logical group, perform `git add <files>` and GPG-signed commit using `BypassSandbox: true`:
     `git commit -S -m "<type>: <description>"`.
5. **Push Branch**:
   - Push to origin: `git push -u origin <branch-name>`.
6. **Create Pull Request**:
   - Create PR targeting `--base dev` using GitHub CLI:
     `gh pr create --base dev --title "<Generated Title>" --body "<Generated Body>"`.

---

## Detailed Guidelines & Conventions

### 1. Commit Message Convention (`AGENTS.md` & Conventional Commits)
- Format: `<type>: <description>` (e.g. `feat: 입금대조 그리드 수동 보완 항목 추가`)
- Allowed Types: `feat`, `fix`, `design`, `typo`, `mod`, `add`, `del`, `refactor`, `init`, `chore`, `merge`, `test`, `docs`.

### 2. PR Body Generation
Use repository template `.github/pull_request_template.md` if present:
```markdown
## 목적
- [Brief summary of the PR purpose]

## 포함 내용
- [Bullet list of key updates]

## 확인
- [x] npm run lint (0 warnings) / pytest pass
- [x] GPG 서명 커밋 완료

## 특이사항
- [Special notes or deployment warnings]
```

### 3. Branching & PR Rules
- **Base Branch**: Always target `--base dev` when creating Pull Requests. Never merge directly into `main` unless explicitly requested.
- **Never Commit directly on `dev`**: Always branch out to `<type>/<kebab-case-description>` first.

### 4. GPG Signing (MANDATORY)
- All commits MUST be GPG-signed using `-S`: `git commit -S -m "..."`.
- Always set `BypassSandbox: true` when running `git commit` so GPG key access succeeds.

### 5. Security & Secret Leak Prevention (MANDATORY)

모든 커밋 및 PR 생성 전 아래 체크리스트를 전수 확인해야 합니다:

1. **환경설정 파일 격리 확인**:
   - `.env`, `.env.*`(예: `.env.local`, `.env.bak*`, `.env.production`)은 절대 커밋 대상에 포함되지 않아야 합니다.
   - 템플릿 파일인 `.env.example`만 커밋할 수 있으며, 이 파일 안에도 실제 운영 키나 패스워드가 아닌 더미 값(예: `your-api-key-here`)만 포함되어야 합니다.

2. **하드코딩된 시크릿 검사**:
   - 코드, 테스트 코드, 주석 내에 실제 API Key, Secret Key, DB 접속 비밀번호, 토큰이 하드코딩되어 있는지 `git diff`를 전수 검사합니다.

3. **개인정보 및 운영 데이터 유출 방지 (PII)**:
   - 테스트용 목데이터나 픽스처 파일에 실제 고객 주문 정보(수취인명, 전화번호, 배송지 주소, 통관고유부호 등)가 마스킹 없이 포함되어 있는지 점검합니다.

4. **임시/백업/로그/런타임 파일 제외**:
   - `runtime/`, `work/`, `logs/`, `*.log`, `*.bak`, `*.tmp` 등 런타임 부산물이 `.gitignore`에 의해 정상 제외되었는지 확인합니다.
