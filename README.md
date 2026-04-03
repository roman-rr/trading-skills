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

The sentinel scans 50+ perpetual markets for anomalies across six orthogonal dimensions -- from order book microstructure to Deribit options flow. A signal fires only when 2+ groups agree.

| Group | Triggers | What It Detects |
|-------|----------|-----------------|
| **Volume & Liquidity** | `volume_spike` `liquidation_cascade` `cvd_divergence` `vpin_toxicity` | Unusual volume, mass liquidations, hidden directional flow, informed trading pressure |
| **Positioning** | `funding_extreme` `funding_velocity` `funding_reversal` `oi_divergence` `basis_spread` | Funding rate extremes, velocity shifts, post-crowding reversals, OI divergence, basis dislocation |
| **Price Dynamics** | `breakout_5m` `breakout_15m` `breakout_60m` | Multi-window breakout detection at different speeds |
| **Cross-Asset** | `beta_divergence` `oi_redistribution` | Alt decoupling from BTC, capital rotation between coins |
| **Microstructure** | `obi_imbalance` `trade_arrival_spike` | Order book structure and trade intensity for early signals |
| **Options-Derived** | `dvol_spike` `pc_ratio_shift` `iv_skew_shift` | Forward-looking signals from Deribit -- what smart money expects |

```
Anomalies (17 triggers) → Confluence (2+ groups) → Trend Phase (13 detectors) → Signal (3 experts merge)
```

## Multi-Expert Consensus

Three specialized AI experts analyze independently:

- **Technical** -- price action, TA indicators, multi-timeframe structure
- **Flow** -- derivatives, funding, OI, liquidation clusters, CVD
- **Regime** -- macro context, expectation gaps, cross-asset correlation

Signals require agreement. Conflicting views are flagged or filtered. Each expert uses Thompson sampling for model selection -- the system learns which models perform best per market condition.

## Research-Grounded -- 44 Methods, 53 Citations

Every algorithm is backed by peer-reviewed research from quantitative finance, statistics, and machine learning.

| Area | Methods | Key References |
|------|---------|----------------|
| **Position Sizing** | Kelly Criterion (half-Kelly), ATR normalization, Turtle Traders model | Kelly 1956, Thorp 2006, Faith 2007 |
| **Anomaly Detection** | CUSUM, Modified Z-score (MAD), EWMA beta, excess kurtosis, realized vol ratio, BH FDR | Page 1954, Iglewicz 1993, Andersen 2003 |
| **Technical Analysis** | RSI, MACD, Bollinger Bands, ATR, ADX, VWAP, OLS slope + R2, swing S/R, Pearson correlation | Wilder 1978, Appel 1979, Bollinger 2001 |
| **Multi-Expert AI** | MoE ensemble, Thompson sampling, weighted composite scoring, regime-adaptive weighting | Jacobs 1991, Thompson 1933, Chapelle 2011 |
| **Market Microstructure** | CVD via tick rule, funding contrarian, options expiry pin risk, order book imbalance | Lee & Ready 1991, Easley 2012, Avellaneda 2003 |
| **Risk Management** | Balance-based regime switching, profit factor, walk-forward validation, ISQ (MAUT) | Boyd 2017, Van Tharp 1998, Keeney 1976 |

## What You Get

| Feature | Description |
|---------|-------------|
| Live signals | Bullish/bearish with full trade setup -- entry, SL, TP, leverage, position size |
| Transmission chains | 2-4 causal reasoning steps per signal with specific data points |
| 50+ coins | Dynamically selected from top volume, funding, and OI on Hyperliquid perps |
| Confidence score | 0-100 AI conviction level per signal |
| Auto-verification | Every signal tracked against real prices -- TP/SL monitoring every minute |
| Paper trading P&L | Real trades on a virtual account with Kelly-optimal sizing |
| Dynamic risk control | Confidence-based leverage caps, ATR-calibrated SL, automatic regime detection |
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

Future: Free tier (60/min, 7d history) / Pro $29/mo (higher limits, 90d, websocket).

## Contributing

Issues, feature requests, and PRs are welcome. Please open an issue first to discuss changes.

## License

**Proprietary** -- Free API during beta. Paid license required for commercial redistribution. See [LICENSE.txt](LICENSE.txt).

## Author

**Roman Antonov** -- [github.com/roman-rr](https://github.com/roman-rr) | [roman-rr.github.io](https://roman-rr.github.io/) | romwtb@gmail.com
