"""A scenario-driven stand-in for the Signals REST API (tests only).

A scenario is a list of frames; the Nth GET /api/skill/signals returns frame N
(the last frame repeats). A frame is either {"status": 429, "headers": {...}}
for an error (add "body": "<html>..." to send a raw text/html body instead of
JSON), or {"plan": "pro"|"free", "signals": [...], "details": {id: sig}}.
Every request is recorded (path, query, headers) for assertions.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

KEY = "ask_test_key_000000000000000000000"
UPGRADE = {"title": "Free plan — you see coin + direction. Pro unlocks the trade levels.",
           "upgradeUrl": "https://signals.x70.ai/api/go/upgrade?src=bot&kid=0123456789abcdef01234567"}


def signal(sid, coin="SOL", direction="bearish", entry=100.0, stop=104.0, target=96.0, live=100.0,
           created="2026-10-07T10:00:00.000Z", status="pending", tp_hit=False, sl_hit=False, plan="pro"):
    gated = plan != "pro"
    return {
        "id": sid, "coin": coin, "direction": direction, "confidence": 70,
        "entryPrice": None if gated else entry, "stopLoss": None if gated else stop,
        "takeProfit": None if gated else target, "leverage": None if gated else 3,
        "livePrice": live, "createdAt": created, "requiresSubscription": gated,
        "verification": {"status": status, "takeProfitHit": tp_hit, "stopLossHit": sl_hit},
    }


class FakeApi(object):
    def __init__(self, frames, key=KEY):
        self.frames, self.key, self.requests, self.list_calls = frames, key, [], 0
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):  # noqa: A002 — silence request logs
                pass

            def do_GET(self):
                u = urlparse(self.path)
                api.requests.append({"path": u.path, "query": parse_qs(u.query), "headers": dict(self.headers)})
                if self.headers.get("X-Api-Key") != api.key:
                    return self._send(401, {"error": "Invalid API key"})
                if u.path == "/api/skill/signals":
                    frame = api.frames[min(api.list_calls, len(api.frames) - 1)]
                    api.list_calls += 1
                    if "status" in frame:
                        return self._send(frame["status"], frame.get("body", {"error": "x"}), frame.get("headers"))
                    body = {"success": True, "signals": frame.get("signals", []),
                            "meta": {"plan": frame.get("plan", "pro")}}
                    if frame.get("plan", "pro") != "pro":
                        body["upgrade"] = UPGRADE
                    if frame.get("drop"):
                        for s in body["signals"]:
                            s.pop(frame["drop"], None)
                    return self._send(200, body)
                if u.path.startswith("/api/skill/signals/"):
                    sid = u.path.rsplit("/", 1)[1]
                    frame = api.frames[min(max(api.list_calls - 1, 0), len(api.frames) - 1)]
                    det = (frame.get("details") or {}).get(sid)
                    if det is None:
                        return self._send(404, {"error": "Signal not found"})
                    return self._send(200, {"success": True, "signal": det})
                return self._send(404, {"error": "nope"})

            def _send(self, code, body, headers=None):
                raw = isinstance(body, str)
                data = body.encode() if raw else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "text/html" if raw else "application/json")
                for k, v in (headers or {}).items():
                    self.send_header(k, str(v))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = "http://127.0.0.1:%d" % self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
