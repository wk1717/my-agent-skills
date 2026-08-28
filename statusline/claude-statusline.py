#!/usr/bin/env python3
"""Claude Code status line: 🤖 model | 🧠 effort | 📊 context% | 💳 rate-limit usage"""
import json, os, sys, datetime

HOME = os.path.expanduser("~")
DUMP = os.environ.get("STATUSLINE_DEBUG") == "1"

def dig(d, *path, default=None):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d if d is not None else default

def flatten(v):
    """A field may arrive bare or wrapped, e.g. {"level": "medium"}."""
    seen = 0
    while isinstance(v, dict) and seen < 5:
        seen += 1
        for k in ("level", "name", "value", "effort", "effortLevel"):
            if k in v:
                v = v[k]
                break
        else:
            v = next(iter(v.values()), "?")
    return str(v)

def human(n):
    n = int(n)
    for div, suf in ((1_000_000, "M"), (1_000, "k")):
        if n >= div:
            v = n / div
            return f"{v:.0f}{suf}" if v >= 100 or v == int(v) else f"{v:.1f}{suf}"
    return str(n)

def settings_effort():
    for p in (os.path.join(HOME, ".claude", "settings.local.json"),
              os.path.join(HOME, ".claude", "settings.json")):
        try:
            with open(p) as f:
                v = json.load(f).get("effortLevel")
            if v:
                return v
        except Exception:
            pass
    return None

def transcript_tokens(path):
    """Fallback context size: newest assistant usage record."""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            lines = f.readlines()
    except Exception:
        return None
    for raw in reversed(lines):
        try:
            rec = json.loads(raw)
        except Exception:
            continue
        if rec.get("isSidechain"):
            continue
        u = dig(rec, "message", "usage")
        if not isinstance(u, dict):
            continue
        total = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                 + u.get("cache_read_input_tokens", 0) + u.get("output_tokens", 0))
        if total:
            return total
    return None

def first_num(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return v
    return None

def until(ts):
    """2h12m remaining until a unix epoch or ISO timestamp, or None."""
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
        return None
    h, m = secs // 3600, (secs % 3600) // 60
    if h >= 24:
        return f"{h // 24}d{h % 24}h"
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

def rate_windows(rl):
    """Normalize rate_limits into [(label, pct, resets_at), ...]."""
    out = []
    if isinstance(rl, dict):
        items = list(rl.items())
    elif isinstance(rl, list):
        items = [(w.get("window") or w.get("name") or w.get("type") or "", w)
                 for w in rl if isinstance(w, dict)]
    else:
        return out
    for key, w in items:
        if not isinstance(w, dict):
            continue
        pct = first_num(w, "used_percentage", "usedPercentage", "used_pct", "utilization")
        if pct is None:
            continue
        k = str(key).lower()
        if "5" in k or "five" in k or ("hour" in k and "24" not in k):
            label = "5h"
        elif "7" in k or "seven" in k or "week" in k:
            label = "7d"
        elif "opus" in k:
            label = "opus"
        else:
            label = str(key)[:6] or "usage"
        out.append((label, pct, w.get("resets_at") or w.get("resetsAt")))
    order = {"5h": 0, "7d": 1, "opus": 2}
    out.sort(key=lambda x: order.get(x[0], 3))
    return out

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if DUMP:
        try:
            with open("/tmp/statusline-payload.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    parts = []

    # 🤖 model
    parts.append("🤖 " + (dig(data, "model", "display_name") or dig(data, "model", "id") or "?"))

    # 🧠 effort level
    effort = (data.get("effort") or data.get("effortLevel") or dig(data, "model", "effort")
              or dig(data, "model", "effortLevel") or settings_effort() or "default")
    parts.append("🧠 " + flatten(effort).lower())

    # 📊 context window
    cw = data.get("context_window") if isinstance(data.get("context_window"), dict) else {}
    cu = cw.get("current_usage") if isinstance(cw.get("current_usage"), dict) else {}
    used = sum(cu.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                      "cache_read_input_tokens", "output_tokens")) or None
    if used is None:
        used = first_num(cw, "used_tokens", "usedTokens", "tokens")
    limit = first_num(cw, "context_window_size", "max_tokens", "maxTokens", "context_limit")
    pct = first_num(cw, "used_percentage", "usedPercentage")
    if used is None:
        used = transcript_tokens(data.get("transcript_path"))
    if not limit:
        limit = int(os.environ.get("STATUSLINE_CONTEXT_LIMIT", "200000"))
        if used and used > limit:
            limit = 1_000_000 if used <= 1_000_000 else used
    if used and limit:
        pct = used * 100.0 / limit
    elif pct is None and used:
        pct = used * 100.0 / limit
    if pct is not None:
        icon = "📊" if pct < 60 else ("🟠" if pct < 85 else "🔴")
        tail = f" ({human(used)}/{human(limit)})" if used else ""
        parts.append(f"{icon} {pct:.0f}%{tail}")
    else:
        parts.append("📊 --%")

    # 💳 /usage rate limits
    wins = rate_windows(data.get("rate_limits"))
    if wins:
        bits = []
        for label, p, resets in wins:
            # every window: how much is used and when it resets. the windows are
            # ordered 5h then 7d and separated by "·", so labels would be noise.
            # the 5h window is the one that bites, so colour that figure.
            figure = f"{p:.0f}%"
            if label == "5h":
                figure = color(figure, p)
            clock = reset_clock(resets)
            bits.append(f"{figure} (↻{clock})" if clock else figure)
        parts.append("💳 " + " · ".join(bits))
    else:
        cost = dig(data, "cost", "total_cost_usd")
        parts.append(f"💳 ${cost:.3f}" if isinstance(cost, (int, float)) else "💳 n/a")

    sys.stdout.write(" │ ".join(parts))

main()
