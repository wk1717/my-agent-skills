#!/usr/bin/env python3
"""Claude Code·Antigravity 세션 로그를 프로젝트별로 모아 읽기 좋은 digest로 만든다.

  collect_sessions.py --list
  collect_sessions.py --project PTC-CS --out DIR [--since 2026-07-01] [--until ...] [--skip-from 기존노트.md]
  collect_sessions.py --notes-dir              노트 저장 폴더 출력
  collect_sessions.py --set-notes-dir PATH     노트 저장 폴더 변경(다시 바꿀 때까지 유지)

세션의 프로젝트는 로그에 가장 많이 등장한 `{root}/<프로젝트>` 경로로 정한다
(Claude는 cwd가 모든 줄에 찍혀 사실상 cwd, Antigravity는 cwd가 없어 언급 빈도).
digest에는 사용자 발화·어시스턴트 답변·Bash 명령·수정 파일만 남긴다(thinking·tool 결과 제외).
"""
import argparse
import collections
import glob
import json
import os
import re
from datetime import datetime

HOME = os.path.expanduser("~")
CLAUDE_GLOB = f"{HOME}/.claude/projects/*/*.jsonl"
AG_GLOBS = [f"{HOME}/.gemini/antigravity/brain/*/.system_generated/logs",
            f"{HOME}/.gemini/antigravity-cli/brain/*/.system_generated/logs"]
CONFIG = f"{HOME}/.config/project-report/config.json"  # 저장소 밖에 둬서 머신별로 따로 유지
DEFAULT_NOTES = "/Users/smk/projects/project-notes"
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
USER_MAX, ASSIST_MAX, CMD_MAX, SUMMARY_MAX = 800, 1500, 160, 1500
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# 명령은 digest 부피의 1/5을 차지하는데 대부분 git status·grep 같은 조회다.
# 작업 내용(커밋 메시지)·기술(설치)·배포를 드러내는 명령만 남긴다.
KEEP_CMD = re.compile(r"git commit|gh pr create|\b(npm|pnpm|yarn|bun) (install|i|add)\b|pip3? install|uv (add|pip)|"
                      r"brew install|npx create|docker|supabase|vercel|fly |pm2|systemctl|crontab|deploy", re.I)


def notes_dir():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)["notes_dir"]
    except (OSError, ValueError, KeyError):
        return DEFAULT_NOTES


def set_notes_dir(path):
    path = os.path.abspath(os.path.expanduser(path))
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"notes_dir": path}, f, ensure_ascii=False)
    return path


def clip(s, n):
    s = s.strip()
    return s if len(s) <= n else s[:n] + f" …(+{len(s) - n}자)"


def local(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return None


def unquote(v):
    # Antigravity tool args는 JSON 문자열로 한 번 더 감싸져 있다: "\"/path\""
    if isinstance(v, str) and v.startswith('"'):
        try:
            return json.loads(v)
        except ValueError:
            pass
    return v if isinstance(v, str) else ""


def clean_user(t):
    t = re.sub(r"<system-reminder>.*?</system-reminder>", "", t, flags=re.S).strip()
    m = re.search(r"<command-name>(.*?)</command-name>.*?<command-args>(.*?)</command-args>", t, re.S)
    if m:  # 슬래시 명령은 인자가 있을 때만 의미가 있다
        return f"{m.group(1).strip()} {m.group(2).strip()}" if m.group(2).strip() else ""
    if t.startswith(("<local-command", "[Request interrupted", "<command-message>", "Caveat:", "<task-notification>")):
        return ""
    return t


def new_session(sid, source):
    return dict(id=sid, source=source, title="", events=[], files=set(), ts=[], hits=collections.Counter())


def parse_claude(path, pat):
    s = new_session(os.path.basename(path)[:-6], "claude")
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s["hits"].update(pat.findall(line))
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t = o.get("type")
            if t == "ai-title":
                s["title"] = o.get("aiTitle", "")
                continue
            if t not in ("user", "assistant") or o.get("isSidechain") or o.get("isMeta"):
                continue
            d = local(o.get("timestamp"))
            if d:
                s["ts"].append(d)
            c = (o.get("message") or {}).get("content")
            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
            for b in blocks:
                if b.get("type") == "text":
                    txt = clean_user(b.get("text", "")) if t == "user" else b.get("text", "").strip()
                    if txt:
                        kind = "U" if t == "user" else "A"
                        s["events"].append((d, kind, clip(txt, USER_MAX if kind == "U" else ASSIST_MAX)))
                elif b.get("type") == "tool_use":
                    inp = b.get("input") or {}
                    if b.get("name") == "Bash" and KEEP_CMD.search(inp.get("command") or ""):
                        s["events"].append((d, "$", clip(inp["command"].splitlines()[0], CMD_MAX)))
                    elif b.get("name") in EDIT_TOOLS and inp.get("file_path"):
                        s["files"].add(inp["file_path"])
    return s


def parse_ag(logdir, pat):
    f = next((p for p in (f"{logdir}/transcript_full.jsonl", f"{logdir}/transcript.jsonl") if os.path.exists(p)), None)
    if not f:
        return None
    s = new_session(logdir.split(os.sep)[-3], "antigravity")
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s["hits"].update(pat.findall(line))
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t, d = o.get("type"), local(o.get("created_at"))
            if d:
                s["ts"].append(d)
            if t == "USER_INPUT":
                c = o.get("content", "")
                m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", c, re.S)
                txt = (m.group(1) if m else c).strip()
                if txt:
                    s["title"] = s["title"] or clip(txt.splitlines()[0], 60)
                    s["events"].append((d, "U", clip(txt, USER_MAX)))
            elif t == "PLANNER_RESPONSE":
                if o.get("content"):
                    s["events"].append((d, "A", clip(o["content"], ASSIST_MAX)))
                for call in o.get("tool_calls") or []:
                    args = call.get("args") or {}
                    cmd = unquote(args.get("CommandLine"))
                    if cmd and KEEP_CMD.search(cmd):
                        s["events"].append((d, "$", clip(cmd.splitlines()[0], CMD_MAX)))
                    target = unquote(args.get("TargetFile"))
                    if target:
                        s["files"].add(target)
            elif t == "CHECKPOINT" and o.get("content"):
                s["events"].append((d, "S", clip(o["content"], SUMMARY_MAX)))
    return s


def load_all(root):
    pat = re.compile(re.escape(root.rstrip("/")) + r"/([A-Za-z0-9_-][A-Za-z0-9_.-]*)")
    sessions = [parse_claude(p, pat) for p in glob.glob(CLAUDE_GLOB)]
    for g in AG_GLOBS:
        sessions += [s for s in (parse_ag(d, pat) for d in glob.glob(g)) if s]
    sessions = [s for s in sessions if s["ts"] and any(e[1] == "U" for e in s["events"])]
    casing = collections.defaultdict(collections.Counter)  # 대소문자만 다른 경로(PTcorp-AX/PTCorp-AX)는 한 프로젝트
    for s in sessions:
        low = collections.Counter()
        for name, n in s["hits"].items():
            low[name.lower()] += n
            casing[name.lower()][name] += n
        top = low.most_common(1)
        s["project"] = top[0][0] if top and top[0][1] >= 3 else "(미분류)"
        s["start"], s["end"] = min(s["ts"]), max(s["ts"])
        s["size"] = sum(len(e[2]) for e in s["events"])
    names = {k: c.most_common(1)[0][0] for k, c in casing.items()}
    return sessions, names


def render(s, root):
    stamp = lambda d: d.strftime("%m/%d %H:%M") if d else "--:--"
    files = sorted(os.path.relpath(p, root) if p.startswith(root) else p for p in s["files"])
    out = [f"# {s['title'] or '(제목 없음)'}",
           f"- id: {s['id']} ({s['source']})",
           f"- 기간: {s['start']:%Y-%m-%d %H:%M} ~ {s['end']:%m/%d %H:%M}"]
    if files:
        more = f" 외 {len(files) - 30}개" if len(files) > 30 else ""
        out.append(f"- 수정한 파일: {', '.join(files[:30])}{more}")
    out += ["", "## 대화 (U=사용자, A=어시스턴트, $=명령, S=이전 대화 요약)"]
    out += [f"[{stamp(d)}] {k}: {txt}" for d, k, txt in s["events"]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Users/smk/projects", help="프로젝트들이 있는 상위 폴더")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--project")
    ap.add_argument("--out")
    ap.add_argument("--since", help="YYYY-MM-DD (세션 시작일 기준, 포함)")
    ap.add_argument("--until", help="YYYY-MM-DD (포함)")
    ap.add_argument("--skip-from", help="이 파일에 적힌 세션 id(UUID)는 건너뜀 — 기존 노트 증분 갱신용")
    ap.add_argument("--notes-dir", action="store_true", help="노트 저장 폴더 출력")
    ap.add_argument("--set-notes-dir", metavar="PATH", help="노트 저장 폴더 변경 — 다시 바꿀 때까지 유지")
    a = ap.parse_args()
    if a.set_notes_dir:
        print(set_notes_dir(a.set_notes_dir))
        return
    if a.notes_dir:
        print(notes_dir())
        return
    root = a.root.rstrip("/")
    sessions, names = load_all(root)

    if a.list or not a.project:
        by = collections.defaultdict(list)
        for s in sessions:
            by[s["project"]].append(s)
        print(f"{'project':28} {'claude':>6} {'ag':>4}  {'기간':23} digest")
        for p, ss in sorted(by.items(), key=lambda kv: -len(kv[1])):
            n_c = sum(s["source"] == "claude" for s in ss)
            span = f"{min(s['start'] for s in ss):%Y-%m-%d} ~ {max(s['end'] for s in ss):%m-%d}"
            print(f"{names.get(p, p):28} {n_c:>6} {len(ss) - n_c:>4}  {span:23} ~{sum(s['size'] for s in ss) // 1024}KB")
        return

    key = a.project.lower()
    skip = set(UUID.findall(open(a.skip_from, encoding="utf-8").read())) if a.skip_from and os.path.exists(a.skip_from) else set()
    sel = sorted((s for s in sessions if s["project"] == key and s["id"] not in skip
                  and (not a.since or f"{s['start']:%Y-%m-%d}" >= a.since)
                  and (not a.until or f"{s['start']:%Y-%m-%d}" <= a.until)), key=lambda s: s["start"])
    if not sel:
        print(f"'{a.project}' 새 세션 없음 (건너뛴 기존 세션 {len(skip)}개). --list로 이름을 확인하세요.")
        return
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for s in sel:
        fn = f"{s['start']:%Y%m%d-%H%M}_{s['source']}_{s['id'][:8]}.md"
        with open(os.path.join(a.out, fn), "w", encoding="utf-8") as f:
            f.write(render(s, root))
        title = (s["title"] or "").replace("|", "/")
        rows.append(f"| {fn} | {s['start']:%Y-%m-%d} | {s['source']} | {title} | {s['size'] // 1024}KB |")
    total = sum(s["size"] for s in sel)
    with open(os.path.join(a.out, "index.md"), "w", encoding="utf-8") as f:
        f.write(f"# {names.get(key, a.project)} — {len(sel)}개 세션, digest 합계 ~{total // 1024}KB\n\n"
                "| 파일 | 날짜 | 소스 | 제목 | 크기 |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
                f"\n<!-- session_ids: {' '.join(s['id'] for s in sel)} -->\n")
    print(f"{names.get(key, a.project)}: {len(sel)}개 세션 → {a.out} (digest 합계 ~{total // 1024}KB, 건너뜀 {len(skip)})")


if __name__ == "__main__":
    main()
