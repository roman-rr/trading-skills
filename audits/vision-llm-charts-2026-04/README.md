# Vision LLMs for Trading Charts — Audit Artifacts (April 2026)

Sample chart renderings used in the audit ["Stop Using Vision LLMs to Read Trading Charts"](https://gist.github.com/roman-rr) — the exact images that frontier vision LLMs (Claude Opus 4.7, Claude Sonnet 4.6, Claude Haiku 4.5, Gemini 3 Flash Preview, Kimi K2.6, GLM 4.6V, Grok 4.1 Fast) analyzed during the test.

Each chart: bare candlesticks, 48 bars (4H) or 45 bars (1D), 1200×700 (4H) or 1200×500 (1D) px, horizontal S/R overlays (top-2 supports green + top-2 resistances red, 30% alpha dashed), anomaly markers on 4H only (orange bullish, blue bearish), chart title `{COIN} • {TF} • {timestamp UTC}`.

| File | What it shows |
|---|---|
| `BTC-1-4h.png` | April 7 2025 tariff-flush V-reversal on BTC. The ONE case Claude Sonnet 4.6 named correctly out of 230 calls. |
| `BTC-1-1d.png` | Same window, 1D macro context — the paired chart sent alongside the 4H primary. |
| `LINK-5-4h.png` | Ambiguous/descending setup labeled "Ascending Triangle/long" by our fixture generator. 5 of 6 models (correctly) read it as bearish — exposed a fixture-labeling issue we had to correct in the n=40 re-test. |
| `DOGE-4-4h.png` | Typical consolidation case. Models split between bearish flag, descending triangle, and abstain. |

These are the actual renders shipped to the vision LLMs during the audit. Nothing has been edited, upscaled, or re-encoded.
