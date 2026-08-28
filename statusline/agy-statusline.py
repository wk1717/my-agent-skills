#!/usr/bin/env python3
"""AGY & Gemini/Claude Real-time Status Line
Format: 🤖 Model │ 🧠 Effort │ 📊 Context% (Used/Limit) │ 💳 Rate Limits
"""
import json, os, sys, datetime, re, subprocess, time

HOME = os.path.expanduser("~")
CACHE_FILE = os.path.join(HOME, ".gemini", "antigravity-cli", "cache", "usage_cache.json")
LOCK_FILE = os.path.join(HOME, ".gemini", "antigravity-cli", "cache", "usage_cache.lock")
CACHE_TTL = 300      # seconds a fetched usage snapshot stays good
LOCK_TTL = 60        # seconds a refresh is assumed to still be in flight
FETCH_TIMEOUT = 20   # `agy -p /usage` measured at ~5s; leave headroom

def dig(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d if d is not None else default

def flatten_effort(v):
    seen = 0
    while isinstance(v, dict) and seen < 5:
        seen += 1
        for k in ("level", "name", "value", "effort", "effortLevel"):
            if k in v:
                v = v[k]
                break
        else:
            v = next(iter(v.values()), "high")
    s = str(v).lower()
    return s if s in ("low", "medium", "high") else "high"

def human(n):
    try:
        n = int(n)
    except Exception:
        return str(n)
    for div, suf in ((1_000_000, "M"), (1_000, "k")):
        if n >= div:
            v = n / div
            return f"{v:.0f}{suf}" if v >= 100 or v == int(v) else f"{v:.1f}{suf}"
    return str(n)

def first_num(d, *keys):
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return v
    return None

def until(ts):
    if not ts:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    if isinstance(ts, (int, float)):
        try:
            t = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        except Exception:
            return None
    elif isinstance(ts, str):
        try:
            t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    else:
        return None
    secs = int((t - now).total_seconds())
    if secs <= 0:
        return "0m"
    h, m = secs // 3600, (secs % 3600) // 60
    if h >= 24:
        days = h // 24
        return f"{days}d"
    return f"{h}h{m:02d}m" if h else f"{m}m"

def color(text, pct):
    """ANSI-colour a usage figure: green under 50%, yellow to 80%, red above."""
    if os.environ.get("NO_COLOR"):
        return text
    if pct >= 95:
        code = "1;31"   # bold red - effectively spent
    elif pct >= 80:
        code = "31"     # red
    elif pct >= 50:
        code = "33"     # yellow
    else:
        code = "32"     # green
    return f"\033[{code}m{text}\033[0m"

def reset_clock(ts):
    """Local wall-clock time a window resets at: '14:30', or '9/3 09:30' if not today.

    Absolute rather than a countdown: the status line may be redrawn only on
    events, and a stale 'in 2h47m' would silently be wrong. A fixed time never is.
    """
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        try:
            t = datetime.datetime.fromtimestamp(ts)
        except Exception:
            return None
    elif isinstance(ts, str):
        try:
            t = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
        t = t.astimezone().replace(tzinfo=None) if t.tzinfo else t
    else:
        return None
    if t.date() == datetime.date.today():
        return t.strftime("%H:%M")
    return f"{t.month}/{t.day} {t:%H:%M}"

def parse_usage_text(text):
    gemini_5h, gemini_7d = None, None
    claude_5h, claude_7d = None, None

    for line in text.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        group, limit_type, rem_str, reset_str = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        try:
            rem_pct = float(rem_str.replace("%", "").strip())
        except Exception:
            continue
        used_pct = max(0.0, 100.0 - rem_pct)

        info = {
            "used_percentage": used_pct,
            "remaining_percentage": rem_pct,
            "resets_at": reset_str
        }

        group_lower = group.lower()
        limit_lower = limit_type.lower()
        if "gemini" in group_lower:
            if "five" in limit_lower or "5" in limit_lower:
                gemini_5h = info
            elif "weekly" in limit_lower or "7" in limit_lower:
                gemini_7d = info
        elif "claude" in group_lower or "gpt" in group_lower:
            if "five" in limit_lower or "5" in limit_lower:
                claude_5h = info
            elif "weekly" in limit_lower or "7" in limit_lower:
                claude_7d = info

    return {
        "gemini": {"five_hour": gemini_5h, "seven_day": gemini_7d},
        "claude": {"five_hour": claude_5h, "seven_day": claude_7d},
        "updated_at": time.time()
    }

def get_live_usage_data():
    # Check cache file
    cached_data = None
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached_data = json.load(f)
        except Exception:
            pass

    now = time.time()
    # If cache is still fresh, return it. `agy -p /usage` takes ~5s, so keep
    # the window well above the status line's refresh cadence.
    if cached_data and (now - cached_data.get("updated_at", 0) < CACHE_TTL):
        return cached_data

    # Refresh cache in background if lock not active
    should_refresh_bg = True
    if os.path.exists(LOCK_FILE):
        try:
            if now - os.path.getmtime(LOCK_FILE) < LOCK_TTL:
                should_refresh_bg = False
        except Exception:
            pass

    if should_refresh_bg:
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(LOCK_FILE, "w") as f:
                f.write(str(now))
            
            # Always refresh in the background. Never block the status line:
            # `agy -p /usage` takes ~5s and would freeze the prompt.
            if True:
                subprocess.Popen(
                    ["python3", "-c", """
import subprocess, json, os, time
from importlib.machinery import SourceFileLoader
try:
    res = subprocess.run(["agy", "-p", "/usage"], capture_output=True, text=True, timeout=20)
    if res.returncode == 0 and res.stdout.strip():
        mod = SourceFileLoader("statusline", os.path.expanduser("~/.gemini/antigravity-cli/scripts/statusline.py")).load_module()
        data = mod.parse_usage_text(res.stdout)
        cache_file = os.path.expanduser("~/.gemini/antigravity-cli/cache/usage_cache.json")
        with open(cache_file, "w") as f:
            json.dump(data, f)
except Exception:
    pass
"""],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass

    # No cache yet: say so rather than showing stale hard-coded numbers.
    return cached_data or {}

def format_usage_for_provider(provider, usage_data):
    p_data = usage_data.get(provider) or usage_data.get("gemini") or {}
    fh = p_data.get("five_hour")
    sd = p_data.get("seven_day")

    bits = []
    for label, w in (("5h", fh), ("7d", sd)):
        if not isinstance(w, dict):
            continue
        p = w.get("used_percentage", 0)
        figure = f"{p:.0f}%"
        if label == "5h":
            figure = color(figure, p)
        clock = reset_clock(w.get("resets_at"))
        bits.append(f"{figure} (↻{clock})" if clock else figure)

    if bits:
        return "💳 " + " · ".join(bits)
    return "💳 …"

def main():
    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        data = {}

    # 1. 🤖 Active Model
    default_model = "Gemini 3.7 Flash"
    default_effort = "high"

    # Read from settings.json
    try:
        with open(os.path.join(HOME, ".gemini", "antigravity-cli", "settings.json")) as f:
            s = json.load(f)
            if s.get("model"):
                default_model = s["model"]
            if s.get("effort") or s.get("effortLevel"):
                default_effort = s.get("effort") or s.get("effortLevel")
    except Exception:
        pass

    model_val = data.get("model") or data.get("model_name") or data.get("displayName") or dig(data, "model_info", "display_name")
    if isinstance(model_val, dict):
        model_name = model_val.get("display_name") or model_val.get("name") or model_val.get("id") or default_model
    elif isinstance(model_val, str) and model_val.strip():
        model_name = model_val.strip()
    else:
        model_name = default_model

    # Check provider type based on model name
    m_lower = model_name.lower()
    if "claude" in m_lower or "opus" in m_lower or "sonnet" in m_lower or "gpt" in m_lower:
        provider = "claude"
    else:
        provider = "gemini"

    # Clean effort from model name (e.g. "Gemini 3.7 Flash (High)" -> "Gemini 3.7 Flash")
    effort_from_name = None
    m_effort = re.search(r"\((low|medium|high)\)", model_name, re.I)
    if m_effort:
        effort_from_name = m_effort.group(1).lower()
        model_name = re.sub(r"\s*\((low|medium|high)\)", "", model_name, flags=re.I).strip()

    # 2. 🧠 Effort Level
    raw_effort = (data.get("effort") or data.get("effortLevel") or dig(data, "model", "effort")
                  or dig(data, "model", "effortLevel") or effort_from_name or default_effort or "high")
    effort_str = flatten_effort(raw_effort)

    # 3. 📊 Context Window & Token Usage
    cw = data.get("context_window") if isinstance(data.get("context_window"), dict) else (data.get("context") if isinstance(data.get("context"), dict) else {})
    cu = cw.get("current_usage") if isinstance(cw.get("current_usage"), dict) else (cw.get("usage") if isinstance(cw.get("usage"), dict) else {})

    used = sum(cu.get(k, 0) for k in (
        "input_tokens", "output_tokens", "cache_read_input_tokens",
        "cache_creation_input_tokens", "cached_content_token_count", "total_tokens"
    )) or first_num(cw, "used_tokens", "usedTokens", "tokens", "input_tokens", "total_tokens") or first_num(data, "total_tokens", "input_tokens") or 0

    # Limit depends on model provider
    limit = first_num(cw, "context_window_size", "max_tokens", "maxTokens", "context_limit") or first_num(data, "context_window_size", "max_tokens")
    if not limit:
        if provider == "gemini":
            limit = 2_000_000 if ("2m" in m_lower or "pro" in m_lower) else 1_000_000
        else:
            limit = 200_000

    pct = first_num(cw, "used_percentage", "usedPercentage", "used_pct") or first_num(data, "used_percentage")
    if pct is None:
        pct = (used * 100.0 / limit) if limit else 0.0

    icon = "📊" if pct < 60 else ("🟠" if pct < 85 else "🔴")
    tail = f" ({human(used)}/{human(limit)})"
    context_part = f"{icon} {pct:.0f}%{tail}"

    # 4. 💳 Model-specific /usage Rate Limits
    usage_data = get_live_usage_data()
    usage_part = format_usage_for_provider(provider, usage_data)

    parts = [
        f"🤖 {model_name}",
        f"🧠 {effort_str}",
        f"{context_part}",
        f"{usage_part}"
    ]

    sys.stdout.write(" │ ".join(parts))

if __name__ == "__main__":
    main()
