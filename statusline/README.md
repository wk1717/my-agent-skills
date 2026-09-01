# statusline

입력창 바로 위에 한 줄 상태바를 띄웁니다. **Claude Code**와 **Antigravity(AGY)** 양쪽 버전이 들어 있습니다.

```
🤖 Opus 5 │ 🧠 medium │ 📊 6% (58.2k/1M) │ 💳 36% (↻14:40) · 36% (↻8/28 06:00)
```

| 칸 | 내용 |
|---|---|
| 🤖 | 현재 모델 표시명 |
| 🧠 | Effort 레벨 (`low` / `medium` / `high`) |
| 📊 | 컨텍스트 사용률 + `(사용/한도)` |
| 💳 | `/usage` 레이트리밋 — **5시간 창** · **7일 창**, 각각 `사용률 (↻초기화시각)` |

> 이건 에이전트 스킬이 아니라 **한 번 깔면 끝나는 설정물**이라 `SKILL.md`가 없습니다. 대화 중 호출할 일이 없어요.

---

## 설치

```bash
./install.sh          # 설치돼 있는 쪽 전부
./install.sh claude   # Claude Code만
./install.sh agy      # AGY만
```

하는 일:

1. 스크립트를 각 위치로 복사 (`~/.claude/scripts/statusline.py`, `~/.gemini/antigravity-cli/scripts/statusline.py`)
2. 각 `settings.json`의 **`statusLine` 키만** 파이썬 JSON 병합으로 주입 — `permissions`, `model`, `trustedWorkspaces` 등 나머지 키는 그대로 보존
3. 덮어쓰기 전 `.bak.<타임스탬프>` 백업

**재실행해도 안전합니다(멱등).** 설치돼 있지 않은 에이전트는 건너뛰고, `settings.json`이 깨진 JSON이면 손대지 않고 중단합니다.

> 💡 다른 에이전트가 `~/.claude/scripts/statusline.py`를 덮어썼다면 `./install.sh claude` 한 번이면 복구됩니다. 파일 잠금(`chflags uchg`)보다 이쪽이 실용적입니다.

---

## 읽는 법

### 💳 레이트리밋

```
💳 36% (↻14:40) · 36% (↻8/28 06:00)
   └ 5시간 창        └ 7일 창
```

앞이 **5시간**, 뒤가 **7일** 창입니다. 순서로 구분되니 라벨은 붙이지 않습니다.

`↻` 뒤는 **남은 시간이 아니라 초기화되는 절대 시각**(로컬 기준)입니다. 오늘이면 `14:40`, 아니면 `8/28 06:00`. 카운트다운으로 두지 않은 이유는 AGY 상태바가 이벤트 발생 시에만 다시 그려져서, `2h47m 남음` 같은 표시가 조용히 틀린 값이 되기 때문입니다. 절대 시각은 안 썩습니다.

### 색상

**5시간 창 사용률에만** 색이 붙습니다. 실제로 발목 잡는 건 그쪽이라서요.

| 사용률 | 색 |
|---|---|
| < 50% | 🟢 초록 |
| 50–79% | 🟡 노랑 |
| 80–94% | 🔴 빨강 |
| ≥ 95% | 🔴 **굵은 빨강** |

`NO_COLOR` 환경변수가 설정돼 있으면 색을 끕니다.

### 📊 컨텍스트 아이콘

60% 미만 `📊`, 85% 미만 `🟠`, 그 이상 `🔴`.

---

## 새 세션에서의 초기 표시

Claude Code는 **첫 API 응답이 오기 전까지 stdin 페이로드에 `context_window`도 `rate_limits`도 넣어주지 않습니다.** 그래서 이전 세션에서 값을 받았든 말든, 새 창에서 세션을 열면 상태바가 이렇게 뜹니다:

```
🤖 Opus 5 │ 🧠 medium │ 📊 --% │ 💳 $0.000
```

Claude 버전도 AGY처럼 마지막 값을 캐시해서 이 구간을 메웁니다 — `~/.claude/cache/statusline-state.json`:

```json
{"context_limit": 1000000, "rate_limits": [["5h", 24, "..."], ["7d", 18, "..."]]}
```

- **💳** — 레이트리밋은 세션이 아니라 **계정 전역** 값이라, 캐시된 창은 추측이 아니라 진짜 현재 수치입니다. `resets_at`이 지난 창은 리셋된 것이므로 `0%`로 표시하고 `↻` 시각은 뗍니다.
- **📊** — 새 세션에선 아직 아무것도 안 보냈으니 `0%`가 사실입니다. 창 크기(1M / 200k)만 캐시에서 가져옵니다. 캐시가 아직 없는 최초 1회만 `📊 0% (0/200k)`로 뜨고, 응답을 한 번 받으면 이후로는 정확합니다.

값이 바뀌었을 때만 쓰고, 임시 파일에 쓴 뒤 `os.replace()`로 원자적 교체하므로 여러 세션을 동시에 띄워도 안전합니다. 캐시 읽기/쓰기 실패는 전부 삼키고 예전처럼 `--%`로 표시합니다.

캐시를 비우려면 그냥 파일을 지우면 됩니다 — 다음 갱신 때 다시 채워집니다.

---

## 갱신 방식 (두 에이전트가 다릅니다)

| | Claude Code | AGY |
|---|---|---|
| 방식 | 타이머 폴링 | 이벤트 (`triggerStatusLineUpdate`) |
| `refreshInterval` | ✅ `30`초로 설정됨 | ❌ **지원 안 함** (`type`/`command`/`padding`/`stack_with_default`만 인식) |
| 사용량 데이터 | stdin 페이로드의 `rate_limits` (없으면 자체 캐시) | `agy -p /usage` 결과를 자체 캐시 |

AGY는 `refreshInterval`이 없어서 스크립트가 직접 캐시를 관리합니다:

```python
CACHE_TTL     = 300   # 스냅샷 유효 시간(초)
LOCK_TTL      = 60    # 갱신이 진행 중이라고 보는 시간
FETCH_TIMEOUT = 20    # `agy -p /usage`는 실측 ~5초
```

갱신은 **항상 백그라운드**로 돕니다. 동기로 돌리면 `agy -p /usage`가 5초 걸리는 동안 프롬프트가 멈춥니다.

---

## 환경변수 (Claude 버전)

| 변수 | 효과 |
|---|---|
| `NO_COLOR` | 색상 비활성화 |
| `STATUSLINE_DEBUG=1` | stdin 페이로드를 `/tmp/statusline-payload.json`에 덤프 |
| `STATUSLINE_CONTEXT_LIMIT` | 페이로드에 컨텍스트 한도가 없을 때 쓸 기본값 (기본 `200000`) |

> 캐시에 창 크기가 남아 있으면 그쪽을 먼저 씁니다. `STATUSLINE_CONTEXT_LIMIT`은 캐시도 없을 때의 최종 폴백입니다.

---

## 문제가 생기면

**상태바가 안 보임** → `settings.json`에 `statusLine` 키가 들어갔는지 확인하고 새 세션을 여세요.

**💳 칸이 `n/a`** → 페이로드에 `rate_limits`가 없는 겁니다. 실제로 뭐가 오는지 보려면:

```bash
STATUSLINE_DEBUG=1  # settings.json의 command 앞에 붙여서 한 세션 실행
cat /tmp/statusline-payload.json
```

**AGY 💳가 계속 안 뜸** → 캐시가 아직 안 만들어졌을 수 있습니다. 첫 생성까지 ~6초 걸립니다.

```bash
cat ~/.gemini/antigravity-cli/cache/usage_cache.json
```

**직접 실행해서 테스트**

```bash
echo '{}' | python3 ~/.claude/scripts/statusline.py
```

**되돌리기** → 설치할 때 남긴 백업을 쓰세요.

```bash
ls ~/.claude/settings.json.bak.*
cp ~/.claude/settings.json.bak.<타임스탬프> ~/.claude/settings.json
```
