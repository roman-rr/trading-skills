# Signals paper-trading bot

Try [Signals](https://signals.x70.ai) on paper before you trust it with money.
The bot polls the Signals API, opens a simulated position when a fresh signal
arrives, closes it at its stop-loss or take-profit (or when the signal
expires), and logs every trade — wins and losses — to a CSV you own.

- **Paper only.** It never places orders and needs no exchange account.
- **One file, no dependencies.** Python 3.8+ standard library.
- **Honest fills.** It opens at the live price it actually observed (not the
  signal's ideal entry), charges fees on both sides, fills a stop at the worse
  of the stop and the observed price, and a target exactly at the target —
  never better. Once the server has resolved a signal, its verdict decides the
  exit, not a price seen later: a stop-out books at the stop (also when both
  levels were hit), a target hit at the target, and an expired signal at the
  last live price the bot observed.
- **No unconfirmed wins.** With `--stop-cap` the bot's stop is tighter than the
  signal's own, and the server only judges the signal's stop. If the bot went
  more than two polls without seeing a price (asleep, offline, backing off) and
  the server then reports the target, the trade closes at the last price the
  bot saw, with exit reason `unverified`, instead of booking a win it can't confirm.

> Signals can be wrong, and past results don't predict future results. Paper
> results leave out things real trading has, such as slippage beyond the
> observed price, funding and liquidation.

## Quick start with an AI agent

Get a free API key at <https://signals.x70.ai/dashboard/mcp-key> (new accounts
get a 14-day Pro trial, no card), then:

```bash
export SIGNALS_API_KEY=<your key>       # Windows PowerShell: $env:SIGNALS_API_KEY = "<your key>"
```

then start Claude Code, Codex or Cursor from that same terminal (one that is
already running, or opened from the Dock or Start menu, won't see the key) and
paste [prompt.md](prompt.md). The agent downloads the bot, verifies its
checksum, checks your key and starts it in the background.

## Quick start by hand

```bash
mkdir signals-paper-trader && cd signals-paper-trader
curl -fsSLo paper_trader.py https://raw.githubusercontent.com/roman-rr/trading-skills/9a48ad8760bd3996e6f435de97db42301c69bf63/bots/paper-trader/paper_trader.py
python3 paper_trader.py --selftest          # checks the key and the API
nohup python3 paper_trader.py >> paper_trader.log 2>&1 &
python3 paper_trader.py --report            # results so far, any time
kill $(cat paper_trader.lock)               # stop
```

## What you see

```
OPEN  SOL    short @ 142.31 (signal entry 142.5) stop 148.2 target 136.1
OPEN  ETH    short @ 2566.5 (signal entry 2568.5) stop 2607.5 target 2550.0
CLOSE SOL    short target   @ 136.1  +4.27 USD (+4.27%)
CLOSE ETH    short stop     @ 2607.5  -1.69 USD (-1.69%)
Paper results so far: <n> closed | win rate <x>% | net $<y> (mean $<z> / trade) | open: <k>
```
(Illustrative lines — your results are whatever the signals do.)

On the **free plan**, entry, stop-loss and take-profit are hidden, so the bot
can't open new paper trades. It says so once, with an upgrade link, and keeps
tracking positions it already opened.

## Options

| Flag | Default | |
|---|---|---|
| `--interval` | 300 | seconds between polls (min 60; ±10% jitter) |
| `--notional` | 100 | USD per paper position |
| `--max-open` | 5 | max simultaneous positions |
| `--max-signal-age` | 30 | only open signals younger than this (minutes) |
| `--fee-bps` | 4.5 | fee per side, basis points |
| `--stop-cap` | off | keep the stop within N × the target distance |
| `--preset` | `all` | `all`, `trend-down`, `mid-confidence`, `btc-calm` |
| `--state-dir` | `.` | where state, CSV and lock live |
| `--once` / `--max-loops N` | | run one / N polls and exit |
| `--selftest` | | check key + API format, exit |
| `--report [--json]` | | results from the CSV, exit |

Presets are public API filters — the same ones the Signals MCP tools and REST
API accept — so you can reproduce anything the bot does. Confidence filters are
on a 0–1 scale (`0.70` is the `70` you see in a signal's `confidence` field);
the REST API also accepts 0–100.

One folder holds one preset: its CSV and `--report` are labelled with it, so
starting the bot there with a different `--preset` is refused. Use another
`--state-dir` to run a second preset.

The bot polls `GET /signals?sort=newest&limit=100`, so a fresh signal is always
in the page even when more than 100 are live.

| Preset | Filter |
|---|---|
| `all` | every signal |
| `trend-down` | `primaryTrigger=trend_trending_down`, `confidenceMin=0.70`, `skipDOW=Wednesday,Thursday,Saturday` |
| `mid-confidence` | `confidenceMin=0.62`, `confidenceMax=0.76` |
| `btc-calm` | `btcRet24hMax=1.5` (skip when BTC is up more than 1.5% in 24h) |

## Files

`paper_state.json` (open positions, written atomically), `paper_trades.csv`
(one row per closed trade; `exit_reason` is `target`, `stop`, `expired`,
`unverified` or `vanished` — the signal disappeared or its detail stayed
unreadable for 12 polls), `paper_trader.lock` (PID of the running bot — a
second copy in the same folder exits instead of double-trading).

## Exit codes

`0` ok · `1` network, SSL or server error during `--selftest` (on macOS with
Python from python.org, `CERTIFICATE_VERIFY_FAILED` means running "Install
Certificates.command" from the Python folder in Applications) ·
`2` bad arguments or no API key · `3` API key rejected (401) ·
`4` the API response format changed — update the bot · `5` already running here

## Development

```bash
make bot-test          # unit + fake-API + contract tests on every local python3.x
make sync-fixtures     # refresh tests/fixtures from the Signals service repo
```
