# Trading Signals

![Trading Signals for AI Agents](https://signals.x70.ai/banner.jpg)

`17 triggers. 44 algorithms. 3 AI experts. Every signal backed by causal reasoning and verified against real prices.`

Live crypto trading signals for Claude Code, OpenAI Codex, Cursor, Windsurf & 30+ AI agents. Every signal comes with its reasoning — a transmission chain showing exactly which data points led to the trade — and is verified against real prices. **Pro** adds the trade levels: entry, stop-loss, take-profit, leverage and position size. See [Pricing](#pricing).

## Install

### Claude Code Plugin (recommended)

```bash
/plugin install roman-rr/trading-skills
```

### npx (Claude Code, Codex, Cursor, Windsurf, etc.)

```bash
npx skills add roman-rr/trading-skills
```

### MCP Server (Claude, Cursor, Codex, VS Code)

Works without a key (3-signal preview). For the full feed, get a free key at https://signals.x70.ai/mcp-signup?utm_content=github-readme — the [API Key page](https://signals.x70.ai/dashboard/mcp-key?utm_source=github&utm_medium=readme) has copy-paste setup for every client.

**Claude Code**

```bash
claude mcp add --transport http trading-signals https://signals.x70.ai/mcp
# with a key:
claude mcp add --transport http trading-signals https://signals.x70.ai/mcp --header "X-Api-Key: YOUR_KEY"
```

**Claude app (Desktop & claude.ai)** — Customize → Connectors → *Add custom connector*, URL `https://signals.x70.ai/mcp`. Connectors have no header field, so with a key use `https://signals.x70.ai/mcp?apiKey=YOUR_KEY`.

**Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "trading-signals": {
      "url": "https://signals.x70.ai/mcp",
      "headers": { "X-Api-Key": "YOUR_KEY" }
    }
  }
}
```

**Codex** (`~/.codex/config.toml`, key in env var `SIGNALS_API_KEY`)

```toml
[mcp_servers.trading-signals]
url = "https://signals.x70.ai/mcp"
bearer_token_env_var = "SIGNALS_API_KEY"
```

Tools: `get_signals`, `get_signal`, `get_signal_history`, `get_stats` (`register` is deprecated — keys come from the dashboard).

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

## Always Watching

**17 Triggers. 6 Groups. Every Minute.**

The sentinel continuously scans 50+ perpetual markets for anomalies across six orthogonal dimensions -- volume, positioning, price dynamics, cross-asset flows, microstructure, and options-derived signals. A signal fires only when multiple independent dimensions agree, filtering noise from genuine opportunities.

## Multi-Expert Consensus

Three specialized AI experts analyze every opportunity independently -- each with a different lens on market structure. Signals require agreement; conflicting views are flagged or filtered. The system continuously learns which analytical approaches perform best per market condition.

## Research-Grounded

**44 Scientific Methods. 53 Academic Citations.**

Every algorithm is grounded in peer-reviewed research from quantitative finance, statistics, and machine learning -- spanning position sizing, anomaly detection, technical analysis, market microstructure, and adaptive risk management.

## What You Get

| Feature | Description |
|---------|-------------|
| Live signals | Bullish/bearish with full trade setup -- entry, SL, TP, leverage, position size |
| Transmission chains | 2-4 causal reasoning steps per signal with specific data points |
| 50+ coins | Dynamically selected from top volume, funding, and OI on Hyperliquid perps |
| Confidence score | 0-100 AI conviction level per signal |
| Auto-verification | Every signal tracked against real prices -- TP/SL monitoring every minute |
| Paper trading P&L | Real trades on a virtual account with optimal position sizing |
| Dynamic risk control | Confidence-based leverage caps, volatility-calibrated SL, automatic regime detection |
| Performance stats | Hit rate, cumulative ROI, profit factor, breakdown by direction/coin/model |

## Signal Preview

Example rows — not live data. Entry, SL, TP and leverage are returned on Pro; the free plan returns coin, direction, confidence and the reasoning.

| Coin | Dir | Conf | Entry | SL | TP | Lev | R/R | Type |
|------|-----|------|-------|----|----|-----|-----|------|
| BTC | Bull | 87% | $68,450 | $67,200 | $71,800 | 3x | 2.7 | momentum_shift |
| ETH | Bear | 82% | $3,840 | $3,920 | $3,680 | 2x | 2.0 | funding_anomaly |
| SOL | Bull | 79% | $142.50 | $138.00 | $152.00 | 2x | 2.1 | volume_spike |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/skill/register | No | **Deprecated** — returns `signup_required`; get keys at /mcp-signup |
| GET | /api/skill/signals | API key | List signals (active/verified/all) |
| GET | /api/skill/signals/:id | API key | Single signal detail |
| GET | /api/skill/stats | API key | Performance statistics |

## Example Prompts

Once installed, ask your AI agent:

- *"Get me the latest crypto trading signals"*
- *"Show me today's highest-confidence BTC and ETH signals"*
- *"What's the 30-day hit rate for these trading signals?"*
- *"Build me a Python script that fetches crypto signals and alerts me on Telegram"*
- *"Show me verified signals from the last week -- what hit TP?"*

## Pricing

| | No key | Free key | Pro |
|---|---|---|---|
| Signals | 3-signal preview | every live signal — coin, direction, confidence, reasoning | everything in Free **+ entry, stop-loss, take-profit, leverage, position size** |
| History | — | 24 hours | 30 days |
| Rate limit | 30 calls/hour per IP | 300 calls/hour | effectively unlimited |
| Price | free | free | **$35/month** or $300/year |

New accounts get a **14-day Pro trial — no card**. Nothing is charged unless you subscribe. [Pricing & sign-up](https://signals.x70.ai/pricing?utm_source=github&utm_medium=readme)

## Contributing

Issues, feature requests, and PRs are welcome. Please open an issue first to discuss changes.

If this is useful, a ⭐ helps other people find it.

## License

**Proprietary** — the source is readable; a paid license is required for commercial redistribution. See [LICENSE.txt](LICENSE.txt).
