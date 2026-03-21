# Trading Signals

Live AI crypto trading signals for **Claude Code**, **OpenAI Codex**, and AI coding agents.

Production-grade signal API powered by advanced AI models. Automated verification tracks every signal against real market prices.

**FREE during beta.** Star this repo to support continued development.

## Install

### Claude Code Plugin (recommended)

```bash
/plugin install roman-rr/trading-skills
```

### npx (Claude Code, Codex, Cursor, Windsurf, etc.)

```bash
npx skills add roman-rr/trading-skills
```

### OpenAI Codex CLI

See [agents/openai.yaml](trading-signals/agents/openai.yaml) for agent configuration.

### Manual

```bash
# Claude Code
git clone https://github.com/roman-rr/trading-skills.git
cp -r trading-skills/trading-signals ~/.claude/skills/trading-signals

# OpenAI Codex CLI
cp -r trading-skills/trading-signals ~/.codex/skills/trading-signals
```

## Example Prompts

Once installed, ask your AI agent:

- *"Get me the latest crypto trading signals"*
- *"Show me today's highest-confidence BTC and ETH signals"*
- *"What's the 30-day hit rate for these trading signals?"*
- *"Build me a Python script that fetches crypto signals and alerts me on Telegram"*
- *"Show me verified signals from the last week — what hit TP?"*

## What You Get

| Feature | Description |
|---------|-------------|
| Live signals | Bullish/bearish crypto signals with full trade setups |
| Entry / SL / TP | Exact price levels for every trade |
| Confidence | 0-100 AI conviction level per signal |
| Leverage | Suggested 1-10x leverage with position sizing |
| Verification | Every signal tracked against real market prices |
| ROI tracking | Leverage-adjusted profit/loss per signal |
| Performance stats | Hit rate, cumulative ROI, breakdown by direction |
| 20+ coins | BTC, ETH, SOL, and more |

## Available Skills

| Skill | Description |
|-------|-------------|
| [trading-signals](trading-signals/SKILL.md) | Live AI crypto trading signals API with full trade setups and verification |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/skill/register | No | Register & get API key |
| GET | /api/skill/signals | API key | List signals (active/verified/all) |
| GET | /api/skill/signals/:id | API key | Single signal detail |
| GET | /api/skill/stats | API key | Performance statistics |

## Signal Preview

| Coin | Dir | Conf | Entry | SL | TP | Lev | R/R | Type |
|------|-----|------|-------|----|----|-----|-----|------|
| BTC | Bull | 87% | $68,450 | $67,200 | $71,800 | 3x | 2.7 | momentum_shift |
| ETH | Bear | 82% | $3,840 | $3,920 | $3,680 | 2x | 2.0 | funding_anomaly |
| SOL | Bull | 79% | $142.50 | $138.00 | $152.00 | 2x | 2.1 | volume_spike |

## Why Use Trading Signals?

- **Battle-tested in production** — real signals from a live trading platform, not a demo
- **Every signal verified** — automated tracking against actual market prices
- **Transparent track record** — public dashboard with full history, wins and losses
- **Multi-expert consensus** — signals only fire when multiple AI perspectives agree
- **Adaptive risk management** — the system adjusts based on recent performance
- **15+ real-time data sources** — funding rates, order books, whale trades, on-chain data, news
- **24/7 operation** — signals generated around the clock

## Live Dashboard

Track real-time performance: **https://aelita.x70.ai/signals/dashboard**

## Contributing

Issues, feature requests, and PRs are welcome. Please open an issue first to discuss changes.

## Pricing

**FREE during beta** — no charges, no credit card.

Future: Free tier (60/min, 7d history) / Pro $29/mo (higher limits, 90d, websocket).

## License

**Proprietary** — Free API during beta. Paid license required for commercial redistribution. See [LICENSE.txt](LICENSE.txt).

## Author

**Roman Antonov** — [github.com/roman-rr](https://github.com/roman-rr) | [roman-rr.github.io](https://roman-rr.github.io/) | romwtb@gmail.com
