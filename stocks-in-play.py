#!/usr/bin/env python
import time
import traceback
import os
import fire
from trade_screenshots.sip_handler import SipConfig, handle_sip
from trade_screenshots.symbols_handler import create_charts_day_by_day, create_charts
from trade_screenshots.trades_handler import handle_trades


PATHS = {'tv': '~/Bardata/tradingview', 'alpaca-file': '/Users/fbjarkes/Bardata/alpaca-v2', 'alpaca-file-2016': '/Users/fbjarkes/Bardata/alpaca-v2/2016-2023'}

# TA_PARAMS = {
#     'VWAP': {'color': 'yellow'},
#     'EMA10': {'color': 'lightblue'},
#     'EMA20': {'color': 'blue'},
#     'EMA50': {'color': 'darkblue'},
#     'BB_UPPER': {'color': 'lightgrey'},
#     'BB_LOWER': {'color': 'lightgrey'},
#     'Mid': {'color': 'red'},
#     'DAILY_LEVEL': {'days': 1},
#     'Jlines': {'color': 'green'}
# }

def main(
    start,
    timeframe="15min",  # only allow '<integer>min'
    provider="alpaca-file",
    symbols=None,    
    sip_file='stocks_in_play.txt',
    outdir='',    
    days_before=1,
    days_after=3,
    daily_plot=False,
    transform=''
):
    """
    This function generates trade screenshots for a given set of symbols and timeframes.
    :param start: Stock in play date, e.g. '2023-12-06'
    :param timeframe: The timeframe for the trade screenshots. Only allows '<integer>min'. Defaults to "1min".
    :param provider: The provider for the trade data.
    :param symbols: The symbols as comma separated string, e.g. "AAPL,TSLA,NVDA' (overrides sip_file)
    :param sip_file: File containing list of dates and symbols
    :param trading_hour: The trading hour for the trade screenshots. Assumes OHLC data is in market time for symbol in question.
    :param outdir: The output directory for the generated trade screenshots.
    :param days: The number of days after SIP date, use 0 for all available data (max 30 days for intraday timeframe)
    :param daily_plot: Generate daily plot (if SIP intraday timeframe)
    :param transform: Transform the original OHLC data into this timeframe
    """

    if symbols:
        config = SipConfig(
            timeframe=timeframe,
            symbols_file=sip_file,
            provider=provider,
            outdir=outdir,
            transform=transform,
            days_before=days_before,
            days_after=days_after,
            paths=PATHS,
            gen_daily=daily_plot
        )
        handle_sip(config)
    elif sip_file:
        config = SipConfig(
            timeframe=timeframe,
            symbols_file=sip_file,
            provider=provider,
            outdir=outdir,
            transform=transform,
            days_before=days_before,
            days_after=days_after,
            paths=PATHS,
            gen_daily=daily_plot
        )
        handle_sip(config)
    else:
        raise ValueError("symbols, trades_file, or sip_file must be provided")

if __name__ == "__main__":
    fire.Fire(main)

