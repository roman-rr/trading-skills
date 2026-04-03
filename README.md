# Trading Signals

![Trading Signals for AI Agents](https://signals.x70.ai/banner.jpg)

`17 triggers. 44 algorithms. 3 AI experts. Every signal backed by causal reasoning and verified against real prices.`

Live crypto trading signals for Claude Code, OpenAI Codex, Cursor, Windsurf & 30+ AI agents. Every signal includes entry, SL, TP, leverage, position size, and a full transmission chain showing exactly which data points led to the trade.

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

### MCP Server (Claude Desktop / Claude Code / Cursor)

```bash
claude mcp add trading-signals --transport http -- https://signals.x70.ai/mcp
```

Or add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "trading-signals": {
      "url": "https://signals.x70.ai/mcp"
    }
  }
}
```

Exposes 4 tools: `register`, `get_signals`, `get_signal`, `get_stats`.

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

| Coin | Dir | Conf | Entry | SL | TP | Lev | R/R | Type |
|------|-----|------|-------|----|----|-----|-----|------|
| BTC | Bull | 87% | $68,450 | $67,200 | $71,800 | 3x | 2.7 | momentum_shift |
| ETH | Bear | 82% | $3,840 | $3,920 | $3,680 | 2x | 2.0 | funding_anomaly |
| SOL | Bull | 79% | $142.50 | $138.00 | $152.00 | 2x | 2.1 | volume_spike |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/skill/register | No | Register & get API key |
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

## Links

- **Live signals**: [signals.x70.ai](https://signals.x70.ai)
- **Skills page**: [signals.x70.ai/skills](https://signals.x70.ai/skills)
- **MCP docs**: [signals.x70.ai/mcp-docs](https://signals.x70.ai/mcp-docs)
- **Smithery**: [smithery.ai/servers/roman-rr/trading-signals](https://smithery.ai/servers/roman-rr/trading-signals)

## Pricing

**FREE during beta** -- no charges, no credit card.

## Contributing

Issues, feature requests, and PRs are welcome. Please open an issue first to discuss changes.

## License

**Proprietary** -- Free API during beta. Paid license required for commercial redistribution. See [LICENSE.txt](LICENSE.txt).

## Author

**Roman Antonov** -- [github.com/roman-rr](https://github.com/roman-rr) | [roman-rr.github.io](https://roman-rr.github.io/) | romwtb@gmail.com
