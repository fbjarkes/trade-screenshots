# TODO / Improvement backlog

Each item is written to be picked up cold in a new session. Read `ARCHITECTURE.md` first.
Verify any change with the PoC: `uv run stocks-in-play.py sip.txt` (3 PNGs in `charts/`).

## 1. Interactive HTML chart output (zoom/pan) — top priority

Plotly figures are already interactive; only the export step throws that away by rasterizing
to PNG. Smallest useful version:

- Add `--filetype=png|html|both` (default `png`) to `stocks-in-play.py`, thread it through
  `SipConfig` into `create_intraday_chart`/`create_daily_chart`.
- In `Plotter.save()`: for html, `fig.write_html(f"{filename}.html", include_plotlyjs='cdn')`
  (~3 KB/file; use `include_plotlyjs=True` for offline self-contained ~4 MB files).
  Zoom/pan/hover then work in any browser with no extra code.
- `MplPlotter` can't do interactive html — raise or fall back to plotly for html output.

Optional second step, the actual "flashcard viewer": generate `charts/index.html` that lists all
generated charts and flips through them with arrow keys (that's the core use case of this repo).
Plain vanilla JS, no build step: embed the file list as a JSON array at generation time
(collected in `handle_sip`), one `<iframe>` (html charts) or `<img>` (png), left/right key
handler, filename + counter overlay. Keep it a single self-contained file written by a new
`trade_screenshots/gallery.py`.

## 2. Fix or delete the trades flow (`trade-screenshots.py`)

Currently broken (see "Known issues" in ARCHITECTURE.md). If fixing:

- Replace `utils.get_dataframe_alpaca(sym, tf, path)` calls in `trades_handler.py` /
  `symbols_handler.py` with `utils.get_dataframe(provider, sym, start, end, tf, path=...)`.
- Extend `utils.Trade` with `long_short`, `quantity`, `comment` (or derive: `long_short` from
  sign of `value`) and make `parse_trades` fill them; `Plotter.trade_chart` needs them.
- `utils.write_file` is called with a `filetype` positional in both handlers — drop that arg or
  add a real `filetype` parameter to `write_file`/`save`.
- Add a small `trades.csv` fixture + a DIS intraday data file so the flow is testable.
- A sample trades CSV format needs documenting — `parse_trades` assumes columns
  `[?, ?, symbol, entry_date, exit_date, pnl, value, entry_price, exit_price]`.

If not worth fixing, delete `trade-screenshots.py`, `trades_handler.py`, `symbols_handler.py`,
`Plotter.trade_chart`, `utils.parse_trades`/`split` — that's roughly half the codebase.

## 3. Intraday PoC data + test coverage

- Add e.g. `data/60min/DIS.json` (a few weeks around the sip.txt dates is enough) so the
  intraday path (`--timeframe=60min`, `--transform`, RTH markers, VWAP-per-day) is exercisable.
- Add pytest + a smoke test: run `handle_sip` against the fixtures into a tmp outdir, assert the
  expected PNG filenames exist and are nonempty. Unit-test `parse_txt`,
  `get_plot_dates_weekend_adjusted` (weekday edge cases look suspicious — Tue with
  `days_before=1` doesn't skip the weekend) and `transform_timeframe` round-trips.

## 4. Replace finta with plain pandas

`finta` is unmaintained (last release 2021). Only `EMA`, `VWAP`, `BBANDS` are used and all are
one-liners in pandas — implement directly in `utils_ta.py`:
`close.ewm(span=n, adjust=False).mean()`; VWAP = `(tp*vol).cumsum()/vol.cumsum()` with
`tp=(H+L+C)/3`; BB = rolling mean ± 2*rolling std. Then drop the `finta` dependency.
Keep column names (`EMA10`, `VWAP`, `BB_UPPER`, `BB_LOWER`) — plotter colors key off them.

## 5. CLI/config cleanup

- Single entry point with fire subcommands (`sip`, `trades`, `symbols`) or
  `[project.scripts]` console script (`uv run trade-screenshots sip ...`); needs module rename
  since dashes in `stocks-in-play.py` prevent imports.
- `SipConfig` duplication in `stocks-in-play.py` (two nearly identical ctor calls) — collapse.
- Replace `print` with `logging` + `--verbose`; add `tqdm` progress for many-symbol runs.
- `ta_indicators` is only set for `--symbol` mode, not sip-file mode — make it a CLI flag.

## 6. Performance (only matters for big sip files)

- One `Plotter` per run instead of per date; parallelize the per-symbol loop
  (`multiprocessing`, like `get_dataframes` already does; kaleido is the bottleneck for plotly —
  mplfinance path parallelizes cleanly).
- `get_dfs` loads the full history per symbol then slices per date — fine for daily, wasteful
  for 1min data; pass start/end into `get_dataframe`.

## 7. Live Alpaca data provider

`utils.download_dataframe_alpaca` is a stub. `python-utils` already has
`python_utils.alpaca.get_dataframe_alpaca(timeframe, symbol, start, end, rth_only)` using
`alpaca-py` (already installed transitively) — wire provider name `alpaca` through
`stocks-in-play.py` `PATHS`-less, needs `ALPACA_API_KEY`/`ALPACA_SECRET_KEY` env vars.

## 8. Misc small fixes

- `kaleido==0.2.1` pin (and `plotly<6`) is a workaround; kaleido ≥1.0 needs Chrome installed —
  revisit, or make mplfinance the default and drop kaleido entirely.
- `Plotter.intraday_chart` RTH end time table only covers 1/5/15/30/60min; `b` is unbound for
  other timeframes (2min, 3min) → NameError when data starts pre-market.
- `df = df.sort_index()` inside the per-date loop in `handle_sip` re-sorts repeatedly — hoist.
- `VALID_TA` in `sip_handler.py` is defined but never enforced against `ta_indicators`.
- Dark-mode chart theme option (`plotly_dark` template / mplfinance `nightclouds` style).
