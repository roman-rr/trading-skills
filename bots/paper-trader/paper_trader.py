#!/usr/bin/env python3
"""
signals-paper-trader — paper-trade Signals (https://signals.x70.ai) with no real money.

Polls the Signals REST API, opens a simulated position when a fresh signal
arrives, closes it at its stop-loss or take-profit (or when the signal
expires), and keeps a CSV of every trade so you can judge the signals on your
own numbers before risking anything.

  export SIGNALS_API_KEY=...            # from https://signals.x70.ai/dashboard/mcp-key
  python3 paper_trader.py --selftest    # check the key and the API, then exit
  python3 paper_trader.py               # run (Ctrl-C to stop; state is kept)
  python3 paper_trader.py --report      # results so far

Paper trading only: it never places real orders and needs no exchange account.
Standard library only, Python 3.8+. Files are written to --state-dir (default:
the current directory): paper_state.json, paper_trades.csv, paper_trader.lock.

Fills are deliberately conservative: a position opens at the live price first
observed (not the signal's entry), fees are charged on both sides, a stop
fills at the worse of the stop and the observed price, and a target fills
exactly at the target, never better. Once the server has resolved a signal,
its verdict decides the exit, not the price seen later: stop at the stop (also
when both levels were hit), target at the target, and an expired signal at the
last live price the bot observed.

Exit codes: 0 ok · 1 network / SSL / server error (--selftest) or a crash
2 bad arguments / no API key · 3 API key rejected (401)
4 API response format changed (update the bot) · 5 another instance is running
"""

import argparse
import csv
import json
import os
import random
import re
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

VERSION = "1.0.1"
REPO_URL = "https://github.com/roman-rr/trading-skills/tree/main/bots/paper-trader"
USER_AGENT = "signals-paper-trader/%s (+https://github.com/roman-rr/trading-skills)" % VERSION
DEFAULT_BASE = "https://signals.x70.ai"
FALLBACK_UPGRADE_URL = "https://signals.x70.ai/api/go/upgrade?src=bot"
STATE_VERSION = 1
STATE_FILE, TRADES_FILE, LOCK_FILE = "paper_state.json", "paper_trades.csv", "paper_trader.lock"
SEEN_TTL_S = 35 * 86400
SKIP_REPORT_EVERY_S = 6 * 3600
TERMINAL = ("success", "failed", "expired")

EXIT_OK, EXIT_ARGS, EXIT_AUTH, EXIT_FORMAT, EXIT_LOCKED = 0, 2, 3, 4, 5

# Every field the bot reads. The Signals repo pins the same list in its REST
# contract test, so a breaking API change fails there first.
REQUIRED_LIST = ("success", "signals", "meta.plan")
REQUIRED_SIGNAL = ("id", "coin", "direction", "entryPrice", "stopLoss", "takeProfit", "livePrice",
                   "createdAt", "requiresSubscription", "verification.status",
                   "verification.takeProfitHit", "verification.stopLossHit")
REQUIRED_DETAIL = ("success", "signal")

# Presets are plain public API filters, so anything the bot does you can
# reproduce with the API or MCP tools yourself.
PRESETS = {
    "all": {},
    "trend-down": {"primaryTrigger": "trend_trending_down", "confidenceMin": "0.70",
                   "skipDOW": "Wednesday,Thursday,Saturday"},
    "mid-confidence": {"confidenceMin": "0.62", "confidenceMax": "0.76"},
    "btc-calm": {"btcRet24hMax": "1.5"},
}
FILTER_FLAGS = (
    ("coin-include", "coinInclude"), ("coin-exclude", "coinExclude"), ("direction", "direction"),
    ("confidence-min", "confidenceMin"), ("confidence-max", "confidenceMax"),
    ("primary-trigger", "primaryTrigger"), ("tags-include", "tagsInclude"),
    ("skip-dow", "skipDOW"), ("skip-hour-utc", "skipHourUtc"),
    ("btc-ret24h-max", "btcRet24hMax"), ("btc-ret24h-min", "btcRet24hMin"),
    ("rr-min", "riskRewardRatioMin"), ("rr-max", "riskRewardRatioMax"),
    ("sl-dist-pct-min", "slDistPctMin"), ("sl-dist-pct-max", "slDistPctMax"),
)
CSV_FIELDS = ("opened_at", "closed_at", "signal_id", "coin", "side", "signal_entry", "fill_price",
              "stop", "target", "exit_price", "exit_reason", "notional_usd", "fees_usd",
              "pnl_usd", "pnl_pct", "preset")


class Stop(Exception):
    """SIGINT/SIGTERM — leave the loop cleanly (state saved, lock released)."""


class ApiError(Exception):
    def __init__(self, status, message, retry_after=None):
        super(ApiError, self).__init__(message)
        self.status, self.retry_after = status, retry_after


# ── small helpers ──────────────────────────────────────────────────────────

def get_path(obj, path):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None, False
        obj = obj[part]
    return obj, True


def missing_fields(obj, fields):
    return [f for f in fields if not get_path(obj, f)[1]]


def parse_ts(value):
    """ISO-8601 (with 'Z' and milliseconds) → unix seconds."""
    s = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def num(v):
    try:
        f = float(v)
        return f if f == f and f not in (float("inf"), float("-inf")) else None
    except (TypeError, ValueError):
        return None


def one_line(body, limit=120):
    """An error body as one short log line: an HTML page's <title> (a proxy's
    502 page is 7 lines), anything else with whitespace collapsed and cut."""
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if m:
        body = m.group(1)
    elif re.search(r"<(!doctype|html|head|body)\b", body, re.I):
        return ""  # HTML without a title: the status says enough
    body = " ".join(body.split())
    return body if len(body) <= limit else body[:limit - 3] + "..."


def side_of(direction):
    return "short" if str(direction).lower() in ("bearish", "short") else "long"


def is_gated(sig):
    """Free plan: levels are null and the signal is marked requiresSubscription."""
    return bool(sig.get("requiresSubscription")) or num(sig.get("entryPrice")) is None


def capped_stop(side, entry, stop, target, cap):
    """--stop-cap: keep the stop no further than cap × the target distance."""
    if not cap:
        return stop
    t, s = abs(target - entry), abs(stop - entry)
    if s <= cap * t:
        return stop
    return entry + cap * t if side == "short" else entry - cap * t


def exit_for_price(side, stop, target, price):
    """(reason, fill) if the observed price reached the stop or target, else None.
    Stop fills at the worse of stop and observed; target at the target, never better."""
    if side == "long":
        if price <= stop:
            return "stop", min(stop, price)
        if price >= target:
            return "target", target
    else:
        if price >= stop:
            return "stop", max(stop, price)
        if price <= target:
            return "target", target
    return None


def decide_exit(pos, sig):
    """(reason, fill) to close an open position at, or None to keep it.
    The server's verdict comes first: after a sleep or backoff gap the price
    seen now may have crossed the target although the server already booked
    the stop (or the reverse). Only an unresolved signal is judged on price."""
    ver = sig.get("verification") or {}
    if ver.get("status") in TERMINAL:
        if ver.get("stopLossHit"):  # stop first if both were hit
            return "stop", pos["stop"]
        if ver.get("takeProfitHit"):
            return "target", pos["target"]
        # Expired, or resolved at the end of its window with neither level hit.
        return "expired", pos.get("last_price") or pos["fill"]
    price = num(sig.get("livePrice"))
    if price is None:
        return None
    return exit_for_price(pos["side"], pos["stop"], pos["target"], price)


def pnl(side, fill, exit_price, notional, fee_bps):
    qty = notional / fill
    gross = (exit_price - fill) * qty * (1 if side == "long" else -1)
    fees = notional * fee_bps / 1e4 + exit_price * qty * fee_bps / 1e4
    net = gross - fees
    return net, fees, net / notional * 100.0


# ── state / files ──────────────────────────────────────────────────────────

def new_state(preset):
    return {"version": STATE_VERSION, "preset": preset, "positions": {}, "seen": {},
            "paywall_shown": False, "skipped_gated": 0, "last_skip_report": 0, "format_warned": False}


def load_state(state_dir, preset):
    path = os.path.join(state_dir, STATE_FILE)
    if not os.path.exists(path):
        return new_state(preset)
    with open(path) as f:
        st = json.load(f)
    if st.get("version") != STATE_VERSION:
        raise SystemExit("paper_state.json has an unknown version; move it aside to start fresh")
    for k, v in new_state(preset).items():
        st.setdefault(k, v)
    # A close goes to the CSV first and to the state second. If the bot was
    # killed in between, the CSV row is the truth: drop the position instead
    # of closing it a second time.
    closed = set(t.get("signal_id") for t in read_trades(state_dir))
    for sid in [s for s in st["positions"] if s in closed]:
        del st["positions"][sid]
    return st


def save_state(state_dir, st, now_s):
    st["seen"] = {k: v for k, v in st["seen"].items() if now_s - v < SEEN_TTL_S}
    path = os.path.join(state_dir, STATE_FILE)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def append_trade(state_dir, row):
    path = os.path.join(state_dir, TRADES_FILE)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def read_trades(state_dir):
    path = os.path.join(state_dir, TRADES_FILE)
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def pid_alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_lock(state_dir):
    """Exclusive-create lock file holding our PID. Returns None, the running PID,
    or -1 if another copy keeps taking the lock as we free a stale one."""
    path = os.path.join(state_dir, LOCK_FILE)
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return None
        except FileExistsError:
            try:
                with open(path) as f:
                    pid = int(f.read().strip() or 0)
            except (OSError, ValueError):
                pid = 0
            if pid and pid != os.getpid() and pid_alive(pid):
                return pid
            try:
                os.remove(path)  # stale lock from a crashed run
            except OSError:  # another copy removed it first
                pass
    return -1


def release_lock(state_dir):
    try:
        os.remove(os.path.join(state_dir, LOCK_FILE))
    except OSError:
        pass


# ── API client ─────────────────────────────────────────────────────────────

class Api(object):
    def __init__(self, base, key, timeout=30):
        self.base, self.key, self.timeout = base.rstrip("/"), key, timeout

    def get(self, path, params=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, headers={"X-Api-Key": self.key, "User-Agent": USER_AGENT,
                                                   "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            retry = e.headers.get("RateLimit-Reset") or e.headers.get("Retry-After")
            body = ""
            try:
                body = one_line(e.read().decode("utf-8", "replace")[:4096])
            except Exception:
                pass
            if body.startswith(str(e.code)):  # "502 Bad Gateway" → "Bad Gateway"
                body = body[len(str(e.code)):].lstrip()
            if self.key:  # never log the key, even if an error page echoes the request
                body = body.replace(self.key, "***")
            raise ApiError(e.code, ("HTTP %d %s" % (e.code, body)).rstrip(), num(retry))
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise ApiError(0, "network: %s" % e)


# ── the bot ────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(prog="paper_trader.py", description="Paper-trade Signals (no real money).")
    p.add_argument("--interval", type=int, default=300, help="seconds between polls (min 60, default 300)")
    p.add_argument("--notional", type=float, default=100.0, help="USD per paper position (default 100)")
    p.add_argument("--max-open", type=int, default=5, help="max simultaneous positions (default 5)")
    p.add_argument("--max-signal-age", type=float, default=30.0,
                   help="only open signals younger than this many minutes (default 30)")
    p.add_argument("--fee-bps", type=float, default=4.5, help="fee per side in basis points (default 4.5)")
    p.add_argument("--stop-cap", type=float, default=None,
                   help="keep the stop within N x the target distance (e.g. 1.0)")
    p.add_argument("--preset", choices=sorted(PRESETS), default="all", help="signal filter preset")
    for flag, _ in FILTER_FLAGS:
        p.add_argument("--" + flag, default=None, help=argparse.SUPPRESS)
    p.add_argument("--state-dir", default=".", help="where state, trades CSV and lock live (default .)")
    p.add_argument("--once", action="store_true", help="one poll, then exit")
    p.add_argument("--max-loops", type=int, default=None, help="stop after N polls")
    p.add_argument("--selftest", action="store_true", help="check API key + response format, then exit")
    p.add_argument("--report", action="store_true", help="print results from the trades CSV, then exit")
    p.add_argument("--json", action="store_true", help="with --report: machine-readable output")
    p.add_argument("--version", action="version", version=VERSION)
    return p


def filters_for(args):
    f = dict(PRESETS[args.preset])
    for flag, param in FILTER_FLAGS:
        v = getattr(args, flag.replace("-", "_"))
        if v is not None:
            f[param] = v
    return f


def summarize(trades, open_count=0):
    closed = [t for t in trades if t.get("closed_at")]
    n = len(closed)
    pnls = [float(t["pnl_usd"]) for t in closed]
    pcts = [float(t["pnl_pct"]) for t in closed]
    by_day = {}
    for t in closed:
        by_day[t["closed_at"][:10]] = by_day.get(t["closed_at"][:10], 0.0) + float(t["pnl_usd"])
    return {
        "closed": n, "open": open_count,
        "win_rate": round(100.0 * sum(1 for x in pnls if x > 0) / n, 1) if n else None,
        "net_usd": round(sum(pnls), 2),
        "mean_usd": round(sum(pnls) / n, 3) if n else None,
        "mean_pct": round(sum(pcts) / n, 3) if n else None,
        "days": len(by_day),
        "positive_days_pct": round(100.0 * sum(1 for v in by_day.values() if v > 0) / len(by_day), 1) if by_day else None,
    }


# Everything the bot prints is plain ASCII: Windows consoles and redirected
# output often use a legacy code page (cp932, cp1251, cp437, ...).
def summary_line(s):
    if not s["closed"]:
        return "Paper results so far: no closed trades yet | open positions: %d" % s["open"]
    return ("Paper results so far: %d closed | win rate %.1f%% | net $%.2f (mean $%.3f / trade, %.3f%%) | open: %d"
            % (s["closed"], s["win_rate"], s["net_usd"], s["mean_usd"], s["mean_pct"], s["open"]))


def run(argv=None, sleep=time.sleep, now=time.time, out=None, env=None):
    out = out or sys.stdout
    env = os.environ if env is None else env

    def say(msg):
        out.write("%s  %s\n" % (iso(now()), msg))
        out.flush()

    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:
        return EXIT_OK if e.code in (0, None) else EXIT_ARGS

    state_dir = os.path.abspath(args.state_dir)
    os.makedirs(state_dir, exist_ok=True)

    if args.report:
        st = load_state(state_dir, args.preset)
        s = summarize(read_trades(state_dir), len(st["positions"]))
        s["preset"] = st.get("preset")
        out.write((json.dumps(s, indent=1) if args.json else summary_line(s)) + "\n")
        return EXIT_OK

    key = (env.get("SIGNALS_API_KEY") or "").strip()
    if not key:
        out.write("SIGNALS_API_KEY is not set. Get a key at https://signals.x70.ai/dashboard/mcp-key and run:\n"
                  "  export SIGNALS_API_KEY=<your key>\n")
        return EXIT_ARGS
    base = env.get("SIGNALS_API_BASE") or DEFAULT_BASE
    host = urllib.parse.urlparse(base).hostname or ""
    if not base.startswith("https://") and host not in ("127.0.0.1", "localhost"):
        out.write("SIGNALS_API_BASE must be https://\n")
        return EXIT_ARGS
    api = Api(base, key)
    filters = filters_for(args)
    interval = max(60, args.interval)

    if args.selftest:
        try:
            body = api.get("/api/skill/signals", dict(filters, limit=5, days=1))
        except ApiError as e:
            if e.status == 401:
                out.write("API key rejected (401). Check SIGNALS_API_KEY.\n")
                return EXIT_AUTH
            out.write("Selftest failed: %s\n" % e)
            return 1
        miss = missing_fields(body, REQUIRED_LIST) + [
            "signals[].%s" % f for s in body.get("signals") or [] for f in missing_fields(s, REQUIRED_SIGNAL)]
        if miss:
            out.write("API format changed (missing: %s) - update the bot: %s\n" % (", ".join(sorted(set(miss))), REPO_URL))
            return EXIT_FORMAT
        plan = get_path(body, "meta.plan")[0]
        out.write("OK | plan: %s | %d live signals match this filter\n" % (plan, len(body.get("signals") or [])))
        if plan != "pro":
            up = body.get("upgrade") or {}
            out.write("Free plan: you'll see coin + direction, but entry/stop/target are hidden, so the bot can't open "
                      "new paper trades. %s\n  %s\n" % (up.get("title") or "", up.get("upgradeUrl") or FALLBACK_UPGRADE_URL))
        return EXIT_OK

    running = acquire_lock(state_dir)
    if running is not None:
        if running > 0:
            out.write("Another paper trader is already running here (pid %s). Stop it first: kill %s\n"
                      % (running, running))
        else:
            out.write("Could not take the lock %s: another paper trader is starting in this folder right now. "
                      "Try again in a minute.\n" % os.path.join(state_dir, LOCK_FILE))
        return EXIT_LOCKED

    def on_signal(_signum, _frame):
        raise Stop()

    # From here on everything runs under the finally below, so a crash at any
    # point (bad state file, startup output, ...) still releases the lock.
    old, st = {}, None
    backoff, loops, code = 60, 0, EXIT_OK
    max_loops = 1 if args.once else args.max_loops
    try:
        st = load_state(state_dir, args.preset)
        for sig_name in ("SIGINT", "SIGTERM"):
            if hasattr(signal, sig_name):
                try:
                    old[sig_name] = signal.signal(getattr(signal, sig_name), on_signal)
                except ValueError:  # not the main thread (tests)
                    pass
        say("signals-paper-trader %s | PAPER TRADING ONLY - no real orders. Signals can be wrong; past results "
            "don't predict future results." % VERSION)
        say("preset %s %s | $%.0f per position | max %d open | fees %.1f bps/side%s | state: %s"
            % (args.preset, json.dumps(filters, sort_keys=True), args.notional, args.max_open, args.fee_bps,
               (" | stop cap %.2fx target" % args.stop_cap) if args.stop_cap else "", state_dir))

        while True:
            loops += 1
            delay, jitter = interval, True
            try:
                body = api.get("/api/skill/signals", dict(filters, limit=100, days=30))
                miss = missing_fields(body, REQUIRED_LIST) + [
                    f for s in body.get("signals") or [] for f in missing_fields(s, REQUIRED_SIGNAL)]
                if miss:
                    if not st["format_warned"]:
                        say("API format changed (missing: %s) - not opening new trades; state kept. Update the bot: %s"
                            % (", ".join(sorted(set(miss))), REPO_URL))
                        st["format_warned"] = True
                else:
                    st["format_warned"] = False
                    tick(api, body, st, args, state_dir, now, say)
                backoff = 60
            except ApiError as e:
                if e.status == 401:
                    say("API key rejected (401). Check SIGNALS_API_KEY. Stopping.")
                    code = EXIT_AUTH
                    break
                jitter = False
                if e.status == 429:
                    delay = int(min(3600, max(60, e.retry_after or 60)))
                    say("rate limited - waiting %ds" % delay)
                else:
                    delay = backoff
                    say("API error (%s) - retrying in %ds" % (e, delay))
                    backoff = min(900, backoff * 2)
            save_state(state_dir, st, now())
            if max_loops and loops >= max_loops:
                break
            # ±10% jitter on normal polls so many bots don't hit the API in lockstep.
            sleep(delay * random.uniform(0.9, 1.1) if jitter else delay)
    except Stop:
        say("stopping (signal received)")
    finally:
        try:
            if st is not None:
                save_state(state_dir, st, now())
        finally:
            release_lock(state_dir)
            for sig_name, handler in old.items():
                signal.signal(getattr(signal, sig_name), handler)
    say(summary_line(summarize(read_trades(state_dir), len(st["positions"]))))
    return code


def close_position(pos, reason, price, now_s, args, state_dir, st, say):
    net, fees, pct = pnl(pos["side"], pos["fill"], price, pos["notional"], args.fee_bps)
    append_trade(state_dir, {
        "opened_at": iso(pos["opened_at"]), "closed_at": iso(now_s), "signal_id": pos["id"], "coin": pos["coin"],
        "side": pos["side"], "signal_entry": pos["signal_entry"], "fill_price": pos["fill"], "stop": pos["stop"],
        "target": pos["target"], "exit_price": round(price, 10), "exit_reason": reason,
        "notional_usd": pos["notional"], "fees_usd": round(fees, 4), "pnl_usd": round(net, 4),
        "pnl_pct": round(pct, 4), "preset": st.get("preset"),
    })
    del st["positions"][pos["id"]]
    say("CLOSE %-6s %-5s %-8s @ %s  %+.2f USD (%+.2f%%)" % (pos["coin"], pos["side"], reason, price, net, pct))


def tick(api, body, st, args, state_dir, now, say):
    now_s = now()
    signals = body.get("signals") or []
    by_id = {str(s["id"]): s for s in signals}
    plan = get_path(body, "meta.plan")[0]

    # 1. Manage open positions (works on the free plan too: livePrice and the
    #    verification outcome are not gated).
    for pid in list(st["positions"]):
        pos = st["positions"][pid]
        sig = by_id.get(pid)
        if sig is None:
            try:
                detail = api.get("/api/skill/signals/" + urllib.parse.quote(pid))
                sig = detail.get("signal") if not missing_fields(detail, REQUIRED_DETAIL) else None
            except ApiError as e:
                if e.status == 404:
                    close_position(pos, "vanished", pos["last_price"], now_s, args, state_dir, st, say)
                    continue
                raise
        if sig is None:
            continue
        price = num(sig.get("livePrice"))
        if price is not None:
            pos["last_price"] = price
        hit = decide_exit(pos, sig)
        if hit:
            close_position(pos, hit[0], hit[1], now_s, args, state_dir, st, say)

    # 2. The paywall moment: levels went null (free key, or a trial ended).
    #    Keyed on the plan itself, not on new signals: a trial that ends while
    #    the same signals are still live must be noticed straight away.
    gated_new = [s for s in signals if str(s["id"]) not in st["seen"] and is_gated(s)]
    st["skipped_gated"] += len(gated_new)
    if plan != "pro" or gated_new:
        if not st["paywall_shown"]:
            st["paywall_shown"] = True
            up = body.get("upgrade") or {}
            say(summary_line(summarize(read_trades(state_dir), len(st["positions"]))))
            say("Your key is on the free plan: entry, stop-loss and take-profit are hidden, so no new paper trades can "
                "open. %s" % (up.get("title") or ""))
            say("Upgrade: %s" % (up.get("upgradeUrl") or FALLBACK_UPGRADE_URL))
            say("Open positions keep being tracked until they close.")
            st["last_skip_report"] = now_s
        elif now_s - st["last_skip_report"] >= SKIP_REPORT_EVERY_S:
            say("%d signals skipped so far on the free plan (levels hidden)." % st["skipped_gated"])
            st["last_skip_report"] = now_s
    elif plan == "pro" and st["paywall_shown"]:
        st["paywall_shown"] = False
        say("Pro levels available again - opening new paper trades.")

    # 3. Open new positions from fresh signals.
    for sig in sorted(signals, key=lambda s: str(s.get("createdAt"))):
        sid = str(sig["id"])
        if sid in st["seen"] or sid in st["positions"]:
            continue
        st["seen"][sid] = now_s
        if is_gated(sig):
            continue
        try:
            age_min = (now_s - parse_ts(sig["createdAt"])) / 60.0
        except (TypeError, ValueError):
            continue
        entry, stop, target, price = (num(sig.get(k)) for k in ("entryPrice", "stopLoss", "takeProfit", "livePrice"))
        if age_min > args.max_signal_age or None in (entry, stop, target) or price is None:
            continue
        if len(st["positions"]) >= args.max_open:
            continue
        side = side_of(sig.get("direction"))
        stop = capped_stop(side, entry, stop, target, args.stop_cap)
        if exit_for_price(side, stop, target, price):
            continue  # already past its stop or target — too late to enter honestly
        st["positions"][sid] = {"id": sid, "coin": sig.get("coin"), "side": side, "signal_entry": entry,
                                "fill": price, "stop": stop, "target": target, "notional": args.notional,
                                "opened_at": now_s, "last_price": price}
        say("OPEN  %-6s %-5s @ %s (signal entry %s) stop %s target %s" % (sig.get("coin"), side, price, entry,
                                                                            stop, target))


def main():
    # Text from the API (the upgrade title has an em dash) may not fit the
    # console's code page; print '?' for it instead of crashing.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):  # not a regular text stream
            pass
    sys.exit(run())


if __name__ == "__main__":
    main()
