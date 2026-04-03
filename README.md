# Trading Signals


![Trading Signals for AI Agents](https://signals.x70.ai/banner.jpg)

`Live AI crypto trading signals for Claude Code, OpenAI Codex, and AI coding agents.`

Production-grade signal API powered by 33 research-grounded algorithms. Every signal includes full trade setup, causal reasoning chain, and automated verification against real market prices.

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

## Intelligence, Not Guesswork

Every signal is backed by a multi-dimensional analysis pipeline that processes funding rates, order flow, technical structure, and market microstructure simultaneously.

### Multi-Expert Consensus

Three specialized AI experts analyze independently: Technical (price action, TA indicators), Flow (derivatives, funding, OI), and Regime (macro context, expectation gaps). Signals require agreement -- conflicting views are flagged or filtered.

### Transmission Chains

Every signal includes 2-4 causal reasoning steps. See exactly which data points led to the trade -- from funding rate extremes to liquidation clusters to MACD crossovers.

### Paper Trading P&L

Every signal is a real trade on a virtual account. The system auto-tightens risk when drawdown increases. Kelly Criterion (half-Kelly) provides mathematically optimal position sizing as advisory data.

### Dynamic Risk Control

Confidence-based leverage caps, ATR-calibrated stop losses, and automatic regime detection. Balance-based regimes (CAPITAL_PROTECT, STEADY_GROWTH, AGGRESSIVE_GROWTH) control risk magnitude without restricting trade direction.

### Market Sentinel

Continuous anomaly detection across funding rates, volume spikes, OI divergence, CVD, and liquidation clusters. CUSUM change-point detection, Modified Z-score, kurtosis analysis, and Benjamini-Hochberg FDR control. Event-driven, not scheduled.

### Auto-Verification

Every signal is verified at the AI-chosen timeframe. TP/SL monitoring runs every minute via WebSocket + polling. Rules engine resolves remaining signals.

## How It Works

1. **Market Anomaly Detected** -- The sentinel monitors 58+ coins across 14 trigger strategies
2. **17-Dimension Data Prefetch** -- Funding, order books, trades, TA indicators, news, smart money -- all in parallel
3. **Multi-Expert AI Analysis** -- Technical + Flow experts run in parallel with independent model selection (Thompson sampling)
4. **Consensus & Risk Gate** -- Experts must agree. Confidence is weighted. Risk regime enforces leverage, sizing, and SL floors
5. **Signal Delivered** -- Complete trade setup: entry, SL, TP, leverage, position size, and the full reasoning chain

## Scientific Foundation -- 33 Research-Grounded Methods

Every algorithm is backed by peer-reviewed research. 39 academic citations.

| Area | Methods | Key References |
|------|---------|----------------|
| **Position Sizing** | Kelly Criterion (half-Kelly), ATR normalization, Turtle Traders model | Kelly 1956, Thorp 2006, Faith 2007 |
| **Anomaly Detection** | CUSUM, Modified Z-score (MAD), EWMA beta, excess kurtosis, realized vol ratio, BH FDR | Page 1954, Iglewicz 1993, Andersen 2003 |
| **Technical Analysis** | RSI, MACD, Bollinger Bands, ATR, ADX, VWAP, OLS slope + R2, swing S/R, Pearson correlation | Wilder 1978, Appel 1979, Bollinger 2001 |
| **Multi-Expert AI** | MoE ensemble, Thompson sampling, weighted composite scoring, regime-adaptive weighting | Jacobs 1991, Thompson 1933, Chapelle 2011 |
| **Market Microstructure** | CVD via tick rule, funding contrarian, options expiry pin risk, order book imbalance | Lee & Ready 1991, Easley 2012 |
| **Risk Management** | Balance-based regime switching, profit factor, walk-forward validation, ISQ (MAUT) | Boyd 2017, Van Tharp 1998, Keeney 1976 |

## What You Get

| Feature | Description |
|---------|-------------|
| Live signals | Bullish/bearish crypto signals with full trade setups (entry, SL, TP, leverage) |
| Transmission chains | 2-4 causal reasoning steps per signal with specific data points |
| 50+ coins | Dynamically selected from top volume, funding, and OI on Hyperliquid perps |
| Confidence score | 0-100 AI conviction level per signal |
| Auto-verification | Every signal tracked against real market prices (TP/SL monitoring every minute) |
| ROI tracking | Leverage-adjusted profit/loss per signal |
| Performance stats | Hit rate, cumulative ROI, profit factor, breakdown by direction/coin/model |
| Risk regimes | Automatic tightening when drawdown increases (CAPITAL_PROTECT, STEADY_GROWTH, etc.) |

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

## Example Prompts

Once installed, ask your AI agent:

- *"Get me the latest crypto trading signals"*
- *"Show me today's highest-confidence BTC and ETH signals"*
- *"What's the 30-day hit rate for these trading signals?"*
- *"Build me a Python script that fetches crypto signals and alerts me on Telegram"*
- *"Show me verified signals from the last week -- what hit TP?"*

## Available Skills

| Skill | Description |
|-------|-------------|
| [trading-signals](trading-signals/SKILL.md) | Live AI crypto trading signals API with full trade setups and verification |

## Links

- **Live signals**: [signals.x70.ai](https://signals.x70.ai)
- **MCP docs**: [signals.x70.ai/mcp-docs](https://signals.x70.ai/mcp-docs)
- **Skills page**: [signals.x70.ai/skills](https://signals.x70.ai/skills)
- **Smithery**: [smithery.ai/servers/roman-rr/trading-signals](https://smithery.ai/servers/roman-rr/trading-signals)

## Pricing

**FREE during beta** -- no charges, no credit card.

Future: Free tier (60/min, 7d history) / Pro $29/mo (higher limits, 90d, websocket).

## Contributing

Issues, feature requests, and PRs are welcome. Please open an issue first to discuss changes.

## License

**Proprietary** -- Free API during beta. Paid license required for commercial redistribution. See [LICENSE.txt](LICENSE.txt).

## Author

**Roman Antonov** -- [github.com/roman-rr](https://github.com/roman-rr) | [roman-rr.github.io](https://roman-rr.github.io/) | romwtb@gmail.com
