# Set up the Signals paper-trading bot

Paste this into Claude Code, Codex, Cursor or any coding agent that can run
shell commands. It sets up a bot that **paper-trades** Signals
(https://signals.x70.ai): simulated positions only, no real orders, no
exchange account.

---

You are setting up the Signals paper-trading bot for me. Follow these rules:

- My API key is in the environment variable `SIGNALS_API_KEY`. Never print it,
  echo it, or write it to a file.
- Work only inside `./signals-paper-trader/`. Install nothing — the bot needs
  only Python 3.8+ and its standard library.
- Don't add cron jobs, launch agents, services or shell-profile changes unless
  I ask.

Steps (on Windows, use the PowerShell form given after a step):

1. Check `python3 --version` is 3.8 or newer. If Python is missing, tell me and stop.
   Windows: try `py -3 --version`, then `python --version`, and use whichever
   works wherever a later step says `py -3` or `python`.
2. `mkdir -p signals-paper-trader && cd signals-paper-trader`
   Windows: `mkdir -Force signals-paper-trader | Out-Null; cd signals-paper-trader`
3. Download the bot to a file (never pipe it into Python):
   `curl -fsSLo paper_trader.py https://raw.githubusercontent.com/roman-rr/trading-skills/paper-trader-v1.0.1/bots/paper-trader/paper_trader.py`
   Windows: the same command with `curl.exe` instead of `curl` (in Windows
   PowerShell, plain `curl` is a different command).
4. Verify it before running anything:
   `python3 -c "import hashlib;print(hashlib.sha256(open('paper_trader.py','rb').read()).hexdigest())"`
   Windows: `(Get-FileHash paper_trader.py -Algorithm SHA256).Hash.ToLower()`
   It must print `36269398fe14cb96841e747321bb59372bc7ebe690784fd53ff7af8b417d7e30`. If it doesn't, delete the file, tell me, and stop.
5. If `SIGNALS_API_KEY` is not set, stop and ask me to set it (the key is at
   https://signals.x70.ai/dashboard/mcp-key) with
   `export SIGNALS_API_KEY=<my key>` (Windows: `$env:SIGNALS_API_KEY = "<my key>"`)
   and then start you again from that same terminal: a variable set in a
   terminal only reaches programs started from it afterwards, so an agent that
   is already running, or an app opened from the Dock or Start menu, won't see it.
6. Run `python3 paper_trader.py --selftest`.
   Windows: `py -3 paper_trader.py --selftest` (the exit code is in `$LASTEXITCODE`).
   - Exit code 1: the API couldn't be reached (network, SSL or server error) —
     show me the message. On macOS with Python from python.org,
     `CERTIFICATE_VERIFY_FAILED` means I need to run "Install Certificates.command"
     from the Python folder in Applications.
   - Exit code 3: the key was rejected — tell me.
   - Exit code 4: the API changed and the bot needs an update — tell me.
   - If it says the plan is **free**: explain that entry, stop-loss and
     take-profit are hidden on the free plan, so the bot can only watch, and
     ask whether to start it anyway.
7. Start it in the background:
   `nohup python3 paper_trader.py >> paper_trader.log 2>&1 &`
   (Windows PowerShell: `Start-Process python -ArgumentList 'paper_trader.py' -RedirectStandardOutput paper_trader.log -WindowStyle Hidden`)
8. Wait a few seconds, then show me the last lines of `paper_trader.log`.
9. Finish by telling me, in plain words:
   - it's paper trading only — no real orders;
   - how to watch it: `tail -f signals-paper-trader/paper_trader.log`
     (Windows: `Get-Content signals-paper-trader\paper_trader.log -Tail 20 -Wait`);
   - how to see results: `cd signals-paper-trader && python3 paper_trader.py --report`
     (Windows: `cd signals-paper-trader; py -3 paper_trader.py --report`);
   - how to stop it: `kill $(cat signals-paper-trader/paper_trader.lock)`
     (Windows: `Stop-Process -Id (Get-Content signals-paper-trader\paper_trader.lock)`);
   - that every trade is saved in `signals-paper-trader/paper_trades.csv`.
