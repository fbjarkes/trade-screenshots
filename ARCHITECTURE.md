# Architecture

Generates PNG "flashcard" chart screenshots from **local OHLC data files** — no network calls.
Two use cases: charts around *stocks-in-play* (SIP) dates, and charts of individual *trades*.

## Entry points

| Script | Status | Purpose |
|---|---|---|
| `stocks-in-play.py` | **working** | Charts around SIP dates from a sip file or a single `--symbol`/`--start` |
| `trade-screenshots.py` | **bit-rotted** | Charts per trade from a trades CSV (see Known issues) |

Both use `fire.Fire(main)`, so every parameter of `main()` is a CLI flag; the first positional
arg of `stocks-in-play.py` is the sip file:

```sh
uv run stocks-in-play.py sip.txt                     # PoC, works out of the box
uv run stocks-in-play.py --symbol=DIS --start=2020-08-24
uv run stocks-in-play.py sip.txt --chart_lib=mplfinance
```

## Data flow (SIP, the working path)

```
sip.txt ─▶ utils.parse_txt ─▶ {symbol: [dates]}
                                    │  per symbol
                                    ▼
              utils.get_dataframe (from python-utils, provider-dispatched)
                 e.g. alpaca-file: data/day/DIS.json ─▶ DataFrame
                                    │  per SIP date
                                    ▼
              slice [date - days_before, date + days_after]  (weekend-adjusted)
                                    ▼
              sip_handler.add_ta  (EMA/VWAP via utils_ta, only if ta_indicators set)
                                    ▼
              get_plotter(chart_lib) ─▶ Plotter (plotly) | MplPlotter (mplfinance)
                 .intraday_chart() / .daily_chart() ─▶ fig
                 .save(fig, path, 1600, 900) ─▶ charts/SYMBOL-YYYY-MM-DD-<tf>.png
```

With `timeframe=day` only the daily chart is produced. With an intraday timeframe, one chart per
timeframe in `--transform` (comma-separated list) plus optionally a daily chart (`--daily_plot`).

## Modules (`trade_screenshots/`)

| File | Responsibility |
|---|---|
| `sip_handler.py` | `SipConfig` dataclass + `handle_sip()` orchestration; `get_plotter()` selects chart lib |
| `plotter.py` | `Plotter` — plotly figures: `intraday_chart`, `daily_chart`, `trade_chart`, `save`. `TA_PARAMS` (indicator colors) and `TRADE_BARS_INCLUDED` (bars before/after per timeframe) live here |
| `plotter_mpl.py` | `MplPlotter` — mplfinance/matplotlib equivalent (`intraday_chart`, `daily_chart`, `save`). No kaleido/browser needed, faster for batches |
| `utils.py` | Local helpers (`parse_txt`, `parse_trades`, `write_file`, `get_plot_dates_weekend_adjusted`, `split`) **plus re-exports** of all data-loading functions from the `python-utils` git dependency — call sites use `utils.<fn>` and don't care which repo a function lives in |
| `utils_ta.py` | Indicator computation via `finta` (`EMA10/20/50`, `VWAP`, `BB`); `add_ta` can compute per-day (VWAP) or on RTH-filtered rows only |
| `common.py` | `VALID_TIME_FRAMES` (allowed `--transform` values), misc helpers |
| `symbols_handler.py` | Day-by-day chart generation with levels/OR markers — **bit-rotted**, see below |
| `trades_handler.py` | Per-trade charts from CSV — **bit-rotted**, see below |

## Data providers and file layout

`utils.get_dataframe(provider, symbol, start, end, timeframe, path=...)` dispatches on provider:

- `alpaca-file`: `<path>/<timeframe>/<SYMBOL>.json` — JSON `{ "<SYMBOL>": [{DateTime, Open, High, Low, Close, Volume}, ...] }`, UTC timestamps. Example fixture: `data/day/DIS.json` (DIS daily 2016–2024).
- `tv`: `<path>/<timeframe>/<SYMBOL>.csv` — TradingView export, epoch-seconds `time` column.
- `ib`: `<path>/<timeframe>/<SYMBOL>.csv` — Interactive Brokers export, `Date` index.

Paths come from `.env` / environment (`TV`, `ALPACA_FILE_2016`), falling back to `./data`
(see `PATHS` in `stocks-in-play.py`).

**DataFrame conventions** (everything downstream assumes these):
- `DatetimeIndex`, tz-naive, converted to America/New_York wall time
- Columns `Open, High, Low, Close, Volume` (capitalized)
- `df.attrs = {'symbol': ..., 'timeframe': ...}` — e.g. `filter_rth` and the plotters read `attrs['timeframe']`

## Charting

Two interchangeable plotters selected by `--chart_lib` (`plotly` default, `mplfinance`).
Shared interface: `intraday_chart(df, tf, symbol, title, sip_start_marker, levels, ta_indicators)`,
`daily_chart(df, symbol, title, sip_date, sip_text)`, `save(fig, filename, width, height)`.

- **plotly**: PNG export goes through kaleido. Pinned `plotly<6` + `kaleido==0.2.1` — kaleido ≥1.0
  requires a separately installed Chrome; 0.2.1 bundles chromium. Rangebreaks hide closed-market
  gaps. plotly figs could also be exported as interactive HTML (`fig.write_html`) — see TODO.md.
- **mplfinance**: renders PNG natively via matplotlib (`Agg` backend). Plots by bar index, so
  datetime annotations must be translated with `df.index.get_indexer(...)` (see `plotter_mpl.py`).

## Dependencies / tooling

- **uv** project: `pyproject.toml` (PEP 621) + `uv.lock`. `uv sync` / `uv run <script>`.
- [`python-utils`](https://github.com/fbjarkes/python-utils) is a **git dependency**
  (`[tool.uv.sources]`); it provides `python_utils.pandas` (data loading/transform) and
  `python_utils.functional.pipe`. Update with `uv lock --upgrade-package python-utils`.
  It transitively pulls `alpaca-py` (only needed for the not-yet-wired `alpaca` live provider).
- dev group: `black`, `ruff` (line-length 180): `uv run ruff check .`

## Known issues / bit-rot (as of 2026-07)

Pre-existing breakage kept for reference — the SIP path does not touch any of it:

- `symbols_handler.py` and `trades_handler.py` call `utils.get_dataframe_alpaca()` and
  `utils.get_dataframe_tv(start, tf, sym, path)` (old signature) — neither exists anymore.
- `symbols_handler.process_symbol` passes `plot_indicators=`, `or_times=`, `daily_levels=` kwargs
  to `Plotter.intraday_chart()`, which accepts none of them; also calls
  `utils.write_file(fig, path, filetype, w, h)` with an extra `filetype` arg.
- `Plotter.trade_chart` reads `trade.long_short`, `trade.quantity`, `trade.comment` which the
  `utils.Trade` dataclass doesn't define.
- `sip.txt` matches the `*.txt` gitignore rule; it's force-added. New sip files need `git add -f`.
