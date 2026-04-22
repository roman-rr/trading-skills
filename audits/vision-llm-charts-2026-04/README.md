# Vision LLMs for Trading Charts — Audit Artifacts (April 2026)

Sample chart renderings from the preprint **["Empirical Audit of Frontier Vision-Language Models for Candlestick-Chart Pattern Recognition"](https://doi.org/10.5281/zenodo.19697762)** — the exact images that frontier vision LLMs (Claude Opus 4.7, Claude Sonnet 4.6, Claude Haiku 4.5, Gemini 3 Flash Preview) analyzed during the test.

## Cite

> Antonov, R. (2026). *Empirical Audit of Frontier Vision-Language Models for Candlestick-Chart Pattern Recognition.* Zenodo. https://doi.org/10.5281/zenodo.19697762

- **DOI:** [10.5281/zenodo.19697762](https://doi.org/10.5281/zenodo.19697762)
- **Zenodo:** https://zenodo.org/records/19697762
- **ResearchGate:** https://www.researchgate.net/publication/404081852
- **Companion gist (prosecutor-style write-up):** https://gist.github.com/roman-rr/c1cd675f7c35b68ae5ac281c30080166
- **Reproducibility discussion (GitHub issue on QuantAgent repo):** https://github.com/Y-Research-SBU/QuantAgent/issues/21

## Render spec (as used in the audit)

- Bare candlesticks, node-canvas, 48 bars (4H) or 45 bars (1D), 1200×700 px (4H) or 1200×500 px (1D).
- Colors: up `#006340` green, down `#A02128` red, black wicks, white background.
- Horizontal S/R overlays: top-2 supports green + top-2 resistances red, 30% alpha dashed.
- Anomaly markers on 4H only: orange triangles bullish, blue triangles bearish.
- Chart title format: `{COIN} · {TF} · {timestamp UTC}`.

| File | What it shows |
|---|---|
| `BTC-1-4h.png` | April 7 2025 tariff-flush V-reversal on BTC. The one case Claude Sonnet 4.6 named correctly across 215 calls. |
| `BTC-1-1d.png` | Same window, 1D macro context — the paired chart sent alongside the 4H primary. |
| `LINK-5-4h.png` | Ambiguous/descending setup that every audited model (correctly) read as bearish, exposing a fixture-labeling issue that was corrected in the n=40 re-test. |
| `DOGE-4-4h.png` | Typical 4H consolidation case. Models split across bearish flag, descending triangle, and abstain. |

These are the actual renders shipped to the vision LLMs during the audit. Nothing has been edited, upscaled, or re-encoded.
