#!/usr/bin/env python
import os
import fire
from trade_screenshots.sip_handler import SipConfig, handle_sip
from dotenv import load_dotenv
load_dotenv()


PATHS = {'tv': os.getenv('TV', 'data'), 'alpaca-file': os.getenv('ALPACA_FILE_2016', 'data')}

def main(
    sip_file='sip.txt',
    start='',
    timeframe="day",  # 'day' or '<integer>min'
    provider="alpaca-file",
    symbol='',
    outdir='charts',
    days_before=1,
    days_after=20,
    daily_plot=True,
    transform='',
    chart_lib='plotly'
):
    """
    This function generates trade screenshots for a given set of symbols and timeframes.
    :param sip_file: File containing list of dates and symbols
    :param start: Stock in play date, e.g. '2023-12-06'
    :param timeframe: The timeframe for the trade screenshots, 'day' or '<integer>min'. Defaults to "day".
    :param provider: The provider for the trade data.
    :param symbol: The symbol, e.g. AAPL (overrides sip_file)
    :param outdir: The output directory for the generated trade screenshots.
    :param days_before: The number of days before SIP date to include in the chart
    :param days_after: The number of days after SIP date, use 0 for all available data (max 30 days for intraday timeframe)
    :param daily_plot: Generate daily plot (if SIP intraday timeframe)
    :param transform: Transform the original OHLC data into this timeframe
    :param chart_lib: Charting library, 'plotly' or 'mplfinance'
    """

    if symbol:
        config = SipConfig(
            start=start,
            symbol=symbol,
            timeframe=timeframe,
            symbols_file=None,
            provider=provider,
            outdir=outdir,
            transform=transform,
            rth_only=False,
            days_before=days_before,
            days_after=days_after,
            paths=PATHS,
            gen_daily=daily_plot,
            ta_indicators=['EMA10', 'VWAP'],
            chart_lib=chart_lib
        )
        handle_sip(config)
    elif sip_file:
        config = SipConfig(
            symbol='',
            start=start,
            timeframe=timeframe,
            symbols_file=sip_file,
            provider=provider,
            outdir=outdir,
            transform=transform,
            rth_only=False,
            days_before=days_before,
            days_after=days_after,
            paths=PATHS,
            gen_daily=daily_plot,
            chart_lib=chart_lib
        )
        handle_sip(config)
    else:
        raise ValueError("Missing symbol or sip_file")

if __name__ == "__main__":
    fire.Fire(main)
