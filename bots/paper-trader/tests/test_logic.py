"""Pure logic: entries, exits, P&L with fees, stop cap, state, CSV, report."""
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import paper_trader as pt  # noqa: E402


class Exits(unittest.TestCase):
    def test_long(self):
        self.assertIsNone(pt.exit_for_price("long", 95, 110, 100))
        self.assertEqual(pt.exit_for_price("long", 95, 110, 111), ("target", 110))  # never better than target
        self.assertEqual(pt.exit_for_price("long", 95, 110, 95), ("stop", 95))
        self.assertEqual(pt.exit_for_price("long", 95, 110, 90), ("stop", 90))      # gap: worse of stop/observed

    def test_short(self):
        self.assertIsNone(pt.exit_for_price("short", 105, 90, 100))
        self.assertEqual(pt.exit_for_price("short", 105, 90, 89), ("target", 90))
        self.assertEqual(pt.exit_for_price("short", 105, 90, 112), ("stop", 112))

    def test_stop_cap(self):
        # short: entry 100, target 96 (T=4), stop 109 (S=9) → capped to 104 at 1×
        self.assertAlmostEqual(pt.capped_stop("short", 100, 109, 96, 1.0), 104)
        self.assertAlmostEqual(pt.capped_stop("long", 100, 91, 104, 1.5), 94)
        self.assertEqual(pt.capped_stop("short", 100, 103, 96, 1.0), 103)  # already inside
        self.assertEqual(pt.capped_stop("short", 100, 109, 96, None), 109)


class ServerVerdict(unittest.TestCase):
    POS = {"side": "short", "fill": 100.5, "stop": 104.0, "target": 96.0, "last_price": 101.0}

    @staticmethod
    def sig(status, live, tp=False, sl=False):
        return {"livePrice": live, "verification": {"status": status, "takeProfitHit": tp, "stopLossHit": sl}}

    def test_verdict_beats_later_price(self):
        # After a gap: the server booked the stop, the price is now past the target (and vice versa).
        self.assertEqual(pt.decide_exit(self.POS, self.sig("failed", 95.0, sl=True)), ("stop", 104.0))
        self.assertEqual(pt.decide_exit(self.POS, self.sig("success", 110.0, tp=True)), ("target", 96.0))
        self.assertEqual(pt.decide_exit(self.POS, self.sig("success", 95.0, tp=True, sl=True)), ("stop", 104.0))

    def test_expired_is_terminal(self):
        self.assertIn("expired", pt.TERMINAL)
        self.assertEqual(pt.decide_exit(self.POS, self.sig("expired", None)), ("expired", 101.0))
        self.assertEqual(pt.decide_exit(dict(self.POS, last_price=None), self.sig("expired", None)), ("expired", 100.5))
        self.assertEqual(pt.decide_exit(self.POS, self.sig("failed", 99.0)), ("expired", 101.0))  # no level hit

    def test_unresolved_judged_on_price(self):
        self.assertEqual(pt.decide_exit(self.POS, self.sig("pending", 95.0)), ("target", 96.0))
        self.assertEqual(pt.decide_exit(self.POS, self.sig("pending", 110.0)), ("stop", 110.0))
        self.assertIsNone(pt.decide_exit(self.POS, self.sig("pending", None)))
        self.assertIsNone(pt.decide_exit(self.POS, self.sig("unverified", 100.0)))


class Pnl(unittest.TestCase):
    def test_long_and_short_with_fees(self):
        net, fees, pct = pt.pnl("long", 100.0, 110.0, 100.0, 4.5)
        self.assertAlmostEqual(fees, 0.045 + 0.0495)
        self.assertAlmostEqual(net, 10 - fees)
        self.assertAlmostEqual(pct, net)  # $100 notional → % == $
        net, fees, _ = pt.pnl("short", 100.0, 90.0, 100.0, 4.5)
        self.assertAlmostEqual(net, 10 - fees)
        net, _, _ = pt.pnl("short", 100.0, 105.0, 100.0, 0)
        self.assertAlmostEqual(net, -5)

    def test_gating_and_side(self):
        self.assertTrue(pt.is_gated({"requiresSubscription": True, "entryPrice": 1}))
        self.assertTrue(pt.is_gated({"requiresSubscription": False, "entryPrice": None}))
        self.assertFalse(pt.is_gated({"requiresSubscription": False, "entryPrice": 1.5}))
        self.assertEqual(pt.side_of("bearish"), "short")
        self.assertEqual(pt.side_of("bullish"), "long")

    def test_timestamps(self):
        self.assertEqual(pt.parse_ts("2026-10-07T10:00:00.000Z"), pt.parse_ts("2026-10-07T10:00:00+00:00"))

    def test_error_body_one_line(self):
        page = ("<html>\r\n<head><title>502 Bad Gateway</title></head>\r\n<body>\r\n"
                "<center><h1>502 Bad Gateway</h1></center>\r\n</body>\r\n</html>\r\n")
        self.assertEqual(pt.one_line(page), "502 Bad Gateway")
        self.assertEqual(pt.one_line("<!DOCTYPE html>\n<html><body>oops</body></html>"), "")
        self.assertEqual(pt.one_line('{"error":\n  "Invalid   key"}'), '{"error": "Invalid key"}')
        self.assertEqual(len(pt.one_line("x " * 500)), 120)


class StateAndFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_state_round_trip_and_prune(self):
        st = pt.new_state("all")
        st["seen"] = {"old": 0, "new": 10 ** 9}
        pt.save_state(self.dir, st, 10 ** 9 + 100)
        back = pt.load_state(self.dir, "all")
        self.assertEqual(set(back["seen"]), {"new"})  # 35-day prune
        self.assertFalse(os.path.exists(os.path.join(self.dir, pt.STATE_FILE + ".tmp")))

    def test_unknown_state_version_refuses(self):
        with open(os.path.join(self.dir, pt.STATE_FILE), "w") as f:
            json.dump({"version": 99}, f)
        with self.assertRaises(SystemExit):
            pt.load_state(self.dir, "all")

    def test_csv_and_summary(self):
        for closed, p in (("2026-10-01T10:00:00Z", 2.0), ("2026-10-01T12:00:00Z", -1.0), ("2026-10-02T10:00:00Z", -0.5)):
            pt.append_trade(self.dir, dict({k: "" for k in pt.CSV_FIELDS}, closed_at=closed, pnl_usd=p, pnl_pct=p))
        s = pt.summarize(pt.read_trades(self.dir), open_count=2)
        self.assertEqual((s["closed"], s["open"], s["days"]), (3, 2, 2))
        self.assertAlmostEqual(s["net_usd"], 0.5)
        self.assertEqual(s["win_rate"], 33.3)
        self.assertEqual(s["positive_days_pct"], 50.0)

    def test_position_already_in_csv_is_dropped_on_load(self):
        # Killed after the close row was written, before the state was saved.
        st = pt.new_state("all")
        st["positions"] = {"s1": {"id": "s1"}, "s2": {"id": "s2"}}
        pt.save_state(self.dir, st, 0)
        pt.append_trade(self.dir, dict({k: "" for k in pt.CSV_FIELDS}, signal_id="s1",
                                       closed_at="2026-10-07T10:00:00Z", pnl_usd=1.0, pnl_pct=1.0))
        self.assertEqual(set(pt.load_state(self.dir, "all")["positions"]), {"s2"})

    def test_lock(self):
        self.assertIsNone(pt.acquire_lock(self.dir))
        with open(os.path.join(self.dir, pt.LOCK_FILE), "w") as f:
            f.write("999999999")  # dead pid → stale, taken over
        self.assertIsNone(pt.acquire_lock(self.dir))
        pt.release_lock(self.dir)
        self.assertFalse(os.path.exists(os.path.join(self.dir, pt.LOCK_FILE)))


class Cli(unittest.TestCase):
    def test_no_key_exits_2(self):
        out = io.StringIO()
        self.assertEqual(pt.run(["--once", "--state-dir", tempfile.mkdtemp()], out=out, env={}), pt.EXIT_ARGS)
        self.assertIn("SIGNALS_API_KEY", out.getvalue())

    def test_bad_args_exit_2(self):
        self.assertEqual(pt.run(["--preset", "nope"], out=io.StringIO(), env={}), pt.EXIT_ARGS)

    def test_http_base_refused_unless_local(self):
        out = io.StringIO()
        code = pt.run(["--selftest"], out=out, env={"SIGNALS_API_KEY": "k", "SIGNALS_API_BASE": "http://evil.example"})
        self.assertEqual(code, pt.EXIT_ARGS)

    def test_lock_race_message(self):
        out = io.StringIO()
        with mock.patch.object(pt, "acquire_lock", return_value=-1):
            code = pt.run(["--once", "--state-dir", tempfile.mkdtemp()], out=out, env={"SIGNALS_API_KEY": "k"})
        self.assertEqual(code, pt.EXIT_LOCKED)
        self.assertNotIn("pid -1", out.getvalue())
        self.assertIn("Try again", out.getvalue())

    def test_crash_after_lock_releases_it(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, pt.STATE_FILE), "w") as f:
            json.dump({"version": 99}, f)
        with self.assertRaises(SystemExit):  # bad state file
            pt.run(["--once", "--state-dir", d], out=io.StringIO(), env={"SIGNALS_API_KEY": "k"})
        self.assertFalse(os.path.exists(os.path.join(d, pt.LOCK_FILE)))

        class Unprintable(io.StringIO):  # e.g. a console code page that can't encode a character
            def write(self, s):
                raise UnicodeEncodeError("cp932", s, 0, 1, "illegal multibyte sequence")

        d = tempfile.mkdtemp()
        with self.assertRaises(UnicodeEncodeError):
            pt.run(["--once", "--state-dir", d], out=Unprintable(), env={"SIGNALS_API_KEY": "k"})
        self.assertFalse(os.path.exists(os.path.join(d, pt.LOCK_FILE)))

    def test_report_without_key(self):
        out = io.StringIO()
        self.assertEqual(pt.run(["--report", "--json", "--state-dir", tempfile.mkdtemp()], out=out, env={}), 0)
        self.assertEqual(json.loads(out.getvalue())["closed"], 0)

    def test_stdlib_only(self):
        import ast
        src = open(os.path.join(os.path.dirname(__file__), "..", "paper_trader.py")).read()
        mods = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".")[0])
        stdlib = {"argparse", "csv", "json", "os", "random", "re", "signal", "sys", "time", "urllib", "datetime",
                  "ctypes"}
        self.assertEqual(mods - stdlib, set())


if __name__ == "__main__":
    unittest.main()
