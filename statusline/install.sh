#!/usr/bin/env bash
# Install the one-line status bar into Claude Code and/or Antigravity (AGY).
#
#   ./install.sh          both, whichever are present
#   ./install.sh claude   Claude Code only
#   ./install.sh agy      Antigravity only
#
# Safe to re-run. Existing settings keys are preserved (the statusLine key is
# merged in, never a whole-file overwrite), and anything replaced is backed up.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGETS="${1:-all}"

say()  { printf '  %s\n' "$*"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# back up a file next to itself, only if it exists
backup() {
  [ -f "$1" ] || return 0
  cp "$1" "$1.bak.$STAMP"
  say "backup  $1.bak.$STAMP"
}

# merge_settings <settings.json> <command> <refresh_interval|"">
#
# Rewrites ONLY the statusLine key. Every other key survives untouched -- this
# file holds permissions, model choice and trusted workspaces, and clobbering
# it wholesale is exactly the accident this script exists to prevent.
merge_settings() {
  python3 - "$1" "$2" "${3:-}" <<'PY'
import json, os, sys
path, command, refresh = sys.argv[1], sys.argv[2], sys.argv[3]

data = {}
if os.path.exists(path):
    with open(path) as f:
        text = f.read().strip()
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            sys.exit(f"  ABORT   {path} is not valid JSON ({e}); left untouched")
    if not isinstance(data, dict):
        sys.exit(f"  ABORT   {path} is not a JSON object; left untouched")

line = {"type": "command", "command": command, "padding": 0}
if refresh:
    # Claude Code polls on a timer. AGY redraws on events and ignores this key,
    # so it is only ever passed for Claude.
    line["refreshInterval"] = int(refresh)

before = json.dumps(data.get("statusLine"), sort_keys=True)
data["statusLine"] = line
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

kept = sorted(k for k in data if k != "statusLine")
print("  unchanged" if before == json.dumps(line, sort_keys=True) else "  updated",
      f" statusLine in {path}")
print(f"  kept    {len(kept)} other key(s): {', '.join(kept) or '(none)'}")
PY
}

install_one() {
  local name="$1" script_dir="$2" settings="$3" command="$4" refresh="$5"
  local dest="$script_dir/statusline.py"

  head_ "$name"
  if [ ! -d "$(dirname "$settings")" ]; then
    say "skip    $(dirname "$settings") not found - $name is not installed here"
    return 0
  fi

  mkdir -p "$script_dir"
  backup "$dest"
  install -m 755 "$SRC/$6" "$dest"
  say "wrote   $dest"

  backup "$settings"
  merge_settings "$settings" "$command" "$refresh"
}

case "$TARGETS" in
  all|claude|agy) ;;
  *) echo "usage: $0 [all|claude|agy]" >&2; exit 2 ;;
esac

if [ "$TARGETS" = all ] || [ "$TARGETS" = claude ]; then
  install_one "Claude Code" \
    "$HOME/.claude/scripts" \
    "$HOME/.claude/settings.json" \
    'python3 ~/.claude/scripts/statusline.py' \
    30 \
    claude-statusline.py
fi

if [ "$TARGETS" = all ] || [ "$TARGETS" = agy ]; then
  # AGY refreshes its usage snapshot through a background `agy -p /usage` call
  # and caches the result here; the directory has to exist before the first run.
  # Guarded, so a machine without AGY is not given an AGY tree it never asked for.
  [ -d "$HOME/.gemini/antigravity-cli" ] && mkdir -p "$HOME/.gemini/antigravity-cli/cache"
  install_one "Antigravity (AGY)" \
    "$HOME/.gemini/antigravity-cli/scripts" \
    "$HOME/.gemini/antigravity-cli/settings.json" \
    "python3 $HOME/.gemini/antigravity-cli/scripts/statusline.py" \
    "" \
    agy-statusline.py
fi

head_ "Done"
say "Open a new session, or press Enter, to redraw the bar."
