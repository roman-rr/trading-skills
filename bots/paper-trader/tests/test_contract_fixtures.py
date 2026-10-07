"""The bot against real API response snapshots.

The fixtures are written by the Signals service's REST contract test
(tests/routes/skillRoutes.contract.test.js); `make sync-fixtures` copies them
here. If the API drops or renames a field the bot reads, this fails.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import paper_trader as pt  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def load(name):
    with open(os.path.join(FIX, name)) as f:
        return json.load(f)


class Contract(unittest.TestCase):
    def test_pro_list(self):
        body = load("signals-pro.json")
        self.assertEqual(pt.missing_fields(body, pt.REQUIRED_LIST), [])
        self.assertEqual(pt.get_path(body, "meta.plan")[0], "pro")
        for s in body["signals"]:
            self.assertEqual(pt.missing_fields(s, pt.REQUIRED_SIGNAL), [])
            self.assertFalse(pt.is_gated(s))
            pt.parse_ts(s["createdAt"])

    def test_free_list_has_printable_upgrade(self):
        body = load("signals-free.json")
        self.assertEqual(pt.missing_fields(body, pt.REQUIRED_LIST), [])
        for s in body["signals"]:
            self.assertEqual(pt.missing_fields(s, pt.REQUIRED_SIGNAL), [])
            self.assertTrue(pt.is_gated(s))
            self.assertIsNotNone(pt.num(s["livePrice"]))  # open positions can still be priced
        self.assertIn("/api/go/upgrade?src=", body["upgrade"]["upgradeUrl"])
        self.assertTrue(body["upgrade"]["title"])

    def test_free_detail(self):
        body = load("signal-detail-free.json")
        self.assertEqual(pt.missing_fields(body, pt.REQUIRED_DETAIL), [])
        self.assertEqual(pt.missing_fields(body["signal"], pt.REQUIRED_SIGNAL), [])


if __name__ == "__main__":
    unittest.main()
