# flashcard-charts
Generate screenshots of intraday charts and trades, to flip through like flashcards

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the project fits together and
[TODO.md](TODO.md) for the improvement backlog.

## Setup

Requires [uv](https://docs.astral.sh/uv/). All dependencies (including
[python-utils](https://github.com/fbjarkes/python-utils)) are installed automatically on first run:

```sh
uv sync
```

## Usage

Generate charts for the symbols/dates listed in a SIP file:

```sh
uv run stocks-in-play.py sip.txt
```

PNGs are written to `charts/` (change with `--outdir`).

Data is read from `$TV` / `$ALPACA_FILE_2016` (set in `.env` or the environment), falling back to
`./data`, with the layout `<path>/<timeframe>/<SYMBOL>.json` — see `data/day/DIS.json` for an example.

Single symbol instead of a SIP file:

```sh
uv run stocks-in-play.py --symbol=DIS --start=2020-08-24
```

Charts are rendered with plotly by default; pass `--chart_lib=mplfinance` to use
mplfinance/matplotlib instead (faster, no kaleido/browser dependency).

SIP file format (`#` comments allowed):

```
2020-08-24: DIS
2020-10-21: DIS,AAPL
```
