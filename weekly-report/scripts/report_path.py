#!/usr/bin/env python3
"""주간보고서 저장 폴더 설정과 저장 파일 경로 계산.

  report_path.py --out-dir                  저장 폴더 출력
  report_path.py --set-out-dir PATH         저장 폴더 변경 (다시 바꿀 때까지 유지)
  report_path.py --start 0713 [--week N]    저장 경로를 JSON으로 출력: {폴더}/{N}주차-0713.md

N을 안 주면 같은 MMDD 파일이 있으면 그 주차를, 없으면 폴더의 최대 주차 + 1을 쓴다.
"""
import argparse
import json
import os
import re
import unicodedata

CONFIG = os.path.expanduser("~/.config/weekly-report/config.json")  # 저장소 밖 — 머신별로 유지
DEFAULT_OUT = "/Users/smk/projects/weekly-reports"
NAME = re.compile(r"^(\d+)주차-(\d{4})\.md$")


def out_dir():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)["out_dir"]
    except (OSError, ValueError, KeyError):
        return DEFAULT_OUT


def set_out_dir(path):
    path = os.path.abspath(os.path.expanduser(path))
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"out_dir": path}, f, ensure_ascii=False)
    return path


def report_path(start, week=None):
    d = out_dir()
    names = os.listdir(d) if os.path.isdir(d) else []
    # Finder에서 만든 파일명은 NFD라 정규화하지 않으면 '주차'가 매칭되지 않는다
    existing = [(int(m[1]), m[2]) for m in (NAME.match(unicodedata.normalize("NFC", n)) for n in names) if m]
    if week is None:
        same = [n for n, s in existing if s == start]
        week = same[0] if same else max((n for n, _ in existing), default=0) + 1
    path = os.path.join(d, f"{week}주차-{start}.md")
    return {"path": path, "week": week, "exists": os.path.exists(path), "first_report": not existing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", action="store_true")
    ap.add_argument("--set-out-dir", metavar="PATH")
    ap.add_argument("--start", help="보고서 주의 첫 기록 날짜 MMDD")
    ap.add_argument("--week", type=int)
    a = ap.parse_args()
    if a.set_out_dir:
        print(set_out_dir(a.set_out_dir))
    elif a.start:
        if not re.fullmatch(r"\d{4}", a.start) or (a.week is not None and a.week < 1):
            ap.error("--start는 MMDD 4자리, --week는 1 이상")
        print(json.dumps(report_path(a.start, a.week), ensure_ascii=False))
    else:
        print(out_dir())


if __name__ == "__main__":
    main()
