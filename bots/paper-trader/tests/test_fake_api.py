"""End-to-end against a fake API: the real HTTP client, loop, state and CSV."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import paper_trader as pt  # noqa: E402
from fake_api import KEY, FakeApi, signal  # noqa: E402

T0 = pt.parse_ts("2026-10-07T10:05:00Z")  # 5 minutes after the fixtures' createdAt
BOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paper_trader.py")


class Clock(object):
    def __init__(self):
        self.t = T0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


class Scenario(unittest.TestCase):
    def go(self, frames, *extra, loops=None, key=None):
        self.api = FakeApi(frames)
        self.addCleanup(self.api.close)
        self.dir = tempfile.mkdtemp()
        self.clock, self.out = Clock(), io.StringIO()
        argv = ["--state-dir", self.dir, "--interval", "60", "--max-loops", str(loops or len(frames))] + list(extra)
        env = {"SIGNALS_API_KEY": key or self.api.key, "SIGNALS_API_BASE": self.api.base}
        self.code = pt.run(argv, sleep=self.clock.sleep, now=self.clock.now, out=self.out, env=env)
        self.log = self.out.getvalue()
        self.trades = pt.read_trades(self.dir)
        return self.code

    def test_pro_open_then_target(self):
        self.go([
            {"signals": [signal("s1", live=100.5)]},
            {"signals": [signal("s1", live=95.5)]},
        ])
        self.assertEqual(self.code, 0)
        self.assertIn("OPEN  SOL", self.log)
        self.assertEqual(len(self.trades), 1)
        t = self.trades[0]
        self.assertEqual((t["exit_reason"], float(t["exit_price"]), float(t["fill_price"])), ("target", 96.0, 100.5))
        self.assertGreater(float(t["pnl_usd"]), 0)

    def test_stop_gap_fills_at_observed(self):
        self.go([{"signals": [signal("s1")]}, {"signals": [signal("s1", live=110.0)]}])
        t = self.trades[0]
        self.assertEqual((t["exit_reason"], float(t["exit_price"])), ("stop", 110.0))

    def test_server_resolved_and_vanished(self):
        resolved = signal("s1", live=101.0, status="success", tp_hit=True)
        self.go([
            {"signals": [signal("s1"), signal("s2", coin="ETH")]},
            {"signals": [], "details": {"s1": resolved}},  # s2 has no detail → 404 → vanished
        ])
        reasons = sorted(t["exit_reason"] for t in self.trades)
        self.assertEqual(reasons, ["target", "vanished"])

    def test_expired_closes_at_last_price(self):
        expired = signal("s1", live=99.0, status="failed")
        self.go([{"signals": [signal("s1")]}, {"signals": [], "details": {"s1": expired}}])
        t = self.trades[0]
        self.assertEqual((t["exit_reason"], float(t["exit_price"])), ("expired", 99.0))

    def test_server_stop_beats_later_price_past_target(self):
        # Asleep (or backing off) while the server booked the stop; by the next
        # poll the price has moved past the target. That is a stop-out, not a win.
        stopped = signal("s1", live=95.0, status="failed", sl_hit=True)
        self.go([{"signals": [signal("s1")]}, {"signals": [], "details": {"s1": stopped}}])
        self.assertEqual(len(self.trades), 1)
        t = self.trades[0]
        self.assertEqual((t["exit_reason"], float(t["exit_price"])), ("stop", 104.0))
        self.assertLess(float(t["pnl_usd"]), 0)

    def test_expired_without_live_price_frees_the_slot(self):
        expired = signal("s1", live=None, status="expired")
        self.go([{"signals": [signal("s1", live=100.5)]}, {"signals": [], "details": {"s1": expired}}])
        t = self.trades[0]
        self.assertEqual((t["exit_reason"], float(t["exit_price"])), ("expired", 100.5))
        self.assertEqual(pt.load_state(self.dir, "all")["positions"], {})

    def test_kill_between_csv_row_and_state_save_does_not_duplicate(self):
        self.go([{"signals": [signal("s1")]}])  # s1 open, state saved
        st = pt.load_state(self.dir, "all")
        # The close row reaches the CSV, then the bot is killed before the state is saved.
        pt.close_position(st["positions"]["s1"], "target", 96.0, T0, pt.build_parser().parse_args([]), self.dir, st,
                          lambda msg: None)
        with open(os.path.join(self.dir, pt.STATE_FILE)) as f:
            self.assertIn("s1", json.load(f)["positions"])
        # Restart while s1 is still live and past its target.
        self.api.frames, self.api.list_calls = [{"signals": [signal("s1", live=95.0)]}], 0
        out = io.StringIO()
        env = {"SIGNALS_API_KEY": self.api.key, "SIGNALS_API_BASE": self.api.base}
        pt.run(["--state-dir", self.dir, "--once"], sleep=self.clock.sleep, now=self.clock.now, out=out, env=env)
        self.assertNotIn("CLOSE", out.getvalue())
        self.assertEqual([t["signal_id"] for t in pt.read_trades(self.dir)], ["s1"])
        self.assertEqual(pt.load_state(self.dir, "all")["positions"], {})

    def test_error_pages_logged_as_one_line(self):
        page = ("<html>\r\n<head><title>502 Bad Gateway</title></head>\r\n<body>\r\n"
                "<center><h1>502 Bad Gateway</h1></center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n")
        self.go([{"status": 502, "body": page},
                 {"status": 500, "body": "upstream said:\n  X-Api-Key: %s\n  oops" % KEY},
                 {"signals": []}])
        errors = [line for line in self.log.splitlines() if "API error" in line]
        self.assertEqual(len(errors), 2)
        self.assertIn("502", errors[0])
        self.assertIn("retrying in 60s", errors[0])  # the whole message on one line
        self.assertNotIn("<html", self.log)
        self.assertNotIn(KEY, self.log)
        for line in self.log.splitlines():
            self.assertRegex(line, r"^\d{4}-\d\d-\d\dT")  # every line is a timestamped log line

    def test_old_or_already_hit_signals_are_skipped(self):
        self.go([{"signals": [
            signal("old", created="2026-10-07T08:00:00.000Z"),
            signal("past", live=95.0),            # already below the short's target
            signal("nolive", live=None),
        ]}])
        self.assertNotIn("OPEN", self.log)

    def test_pro_to_free_mid_run(self):
        self.go([
            {"signals": [signal("s1")]},
            {"plan": "free", "signals": [signal("s1", plan="free"), signal("s2", plan="free", coin="ETH")]},
            {"plan": "free", "signals": [signal("s1", plan="free", live=95.0), signal("s3", plan="free", coin="BTC")]},
        ])
        self.assertEqual(self.log.count("Upgrade: https://signals.x70.ai/api/go/upgrade?src=bot"), 1)
        self.assertEqual(self.log.count("Paper results so far"), 2)  # at the paywall + at exit
        self.assertIn("Open positions keep being tracked", self.log)
        self.assertEqual(self.log.count("OPEN "), 1)                 # nothing new opened on free
        self.assertEqual([t["exit_reason"] for t in self.trades], ["target"])  # s1 still closed

    def test_trial_ends_with_no_new_signals(self):
        # Same signal before and after the switch: the notice must still appear.
        self.go([
            {"signals": [signal("s1")]},
            {"plan": "free", "signals": [signal("s1", plan="free")]},
            {"plan": "free", "signals": [signal("s1", plan="free", live=95.0)]},
        ])
        self.assertEqual(self.log.count("Upgrade:"), 1)
        self.assertEqual([t["exit_reason"] for t in self.trades], ["target"])

    def test_free_with_empty_list_still_explains(self):
        self.go([{"plan": "free", "signals": []}])
        self.assertEqual(self.log.count("Upgrade:"), 1)

    def test_free_from_start(self):
        self.go([{"plan": "free", "signals": [signal("s1", plan="free")]}], loops=2)
        self.assertEqual(self.log.count("Upgrade:"), 1)
        self.assertEqual(self.trades, [])

    def test_rate_limit_waits_for_reset(self):
        self.go([{"status": 429, "headers": {"RateLimit-Reset": "1200"}}, {"signals": []}])
        self.assertEqual(self.clock.sleeps[0], 1200)

    def test_server_errors_back_off_then_recover(self):
        self.go([{"status": 500}, {"status": 502}, {"signals": [signal("s1")]}])
        self.assertEqual(self.clock.sleeps[:2], [60, 120])
        self.assertIn("OPEN", self.log)

    def test_401_exits_3(self):
        self.assertEqual(self.go([{"signals": []}], key="ask_wrong"), pt.EXIT_AUTH)

    def test_format_change_stops_new_trades_keeps_state(self):
        self.go([{"signals": [signal("s1")], "drop": "livePrice"}])
        self.assertIn("API format changed", self.log)
        self.assertNotIn("OPEN", self.log)

    def test_restart_does_not_reopen(self):
        frames = [{"signals": [signal("s1")]}]
        self.go(frames)
        state_dir = self.dir
        out = io.StringIO()
        env = {"SIGNALS_API_KEY": self.api.key, "SIGNALS_API_BASE": self.api.base}
        pt.run(["--state-dir", state_dir, "--once"], sleep=self.clock.sleep, now=self.clock.now, out=out, env=env)
        self.assertNotIn("OPEN", out.getvalue())

    def test_second_instance_exits_5(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, pt.LOCK_FILE), "w") as f:
            f.write(str(os.getppid()))  # a live process that isn't us
        out = io.StringIO()
        code = pt.run(["--state-dir", d, "--once"], out=out, env={"SIGNALS_API_KEY": "k"})
        self.assertEqual(code, pt.EXIT_LOCKED)

    def test_headers_and_preset_filters_on_every_request(self):
        self.go([{"signals": [signal("s1")]}, {"signals": [], "details": {}}], "--preset", "trend-down")
        for r in self.api.requests:
            self.assertEqual(r["headers"].get("X-Api-Key"), self.api.key)
            self.assertTrue(r["headers"].get("User-Agent", "").startswith("signals-paper-trader/"))
        q = self.api.requests[0]["query"]
        self.assertEqual(q["primaryTrigger"], ["trend_trending_down"])
        self.assertEqual(q["confidenceMin"], ["0.70"])

    def test_stop_cap_applied(self):
        self.go([{"signals": [signal("s1", stop=109.0, target=96.0)]}], "--stop-cap", "1.0")
        self.assertIn("stop 104.0", self.log)

    def test_key_never_printed(self):
        self.go([{"signals": [signal("s1")]}, {"plan": "free", "signals": [signal("s2", plan="free")]}])
        self.assertNotIn(self.api.key, self.log)
        for name in os.listdir(self.dir):
            with open(os.path.join(self.dir, name)) as f:
                self.assertNotIn(self.api.key, f.read())

    def test_selftest(self):
        self.api = FakeApi([{"plan": "free", "signals": [signal("s1", plan="free")]}])
        self.addCleanup(self.api.close)
        out = io.StringIO()
        code = pt.run(["--selftest"], out=out, env={"SIGNALS_API_KEY": self.api.key, "SIGNALS_API_BASE": self.api.base})
        self.assertEqual(code, 0)
        self.assertIn("plan: free", out.getvalue())
        self.assertIn("src=bot", out.getvalue())


class LegacyCodePages(unittest.TestCase):
    """Windows consoles and redirected output often use a legacy code page; the
    bot must not crash on its own output or on API text (the em dash in the
    upgrade title), and must leave no lock behind."""

    def bot(self, encoding, *argv):
        api = FakeApi([{"plan": "free", "signals": [signal("s1", plan="free")]}])
        self.addCleanup(api.close)
        d = tempfile.mkdtemp()
        env = dict(os.environ, PYTHONIOENCODING=encoding, SIGNALS_API_KEY=api.key, SIGNALS_API_BASE=api.base)
        p = subprocess.run([sys.executable, BOT, "--state-dir", d] + list(argv), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        msg = "%s %s: %s" % (encoding, argv, p.stderr.decode("ascii", "replace"))
        self.assertEqual(p.returncode, 0, msg)
        self.assertNotIn(b"Traceback", p.stderr, msg)
        self.assertFalse(os.path.exists(os.path.join(d, pt.LOCK_FILE)), msg)
        return p.stdout

    def test_no_crash(self):
        for enc in ("cp932", "cp949", "cp874", "cp1251", "cp1253", "cp437"):
            self.assertIn(b"PAPER TRADING ONLY", self.bot(enc, "--once", "--stop-cap", "1.0"))
            self.assertIn(b"plan: free", self.bot(enc, "--selftest"))


if __name__ == "__main__":
    unittest.main()
