#!/usr/bin/env python
import time
import traceback
import os
import fire
from trade_screenshots.sip_handler import SipConfig, handle_sip
from trade_screenshots.symbols_handler import create_charts_day_by_day, create_charts
from trade_screenshots.trades_handler import handle_trades
from dotenv import load_dotenv
load_dotenv()


#PATHS = {'tv': '~/Bardata/tradingview', 'alpaca-file': '/Users/fbjarkes/Bardata/alpaca-v2', 'alpaca-file-2016': '/Users/fbjarkes/Bardata/alpaca-v2/2016-2023'}
PATHS = {'tv': os.getenv('TV'), 'alpaca-file': os.getenv('ALPACA_FILE_2016')}

def main(
    start='',    
    #start='2024-03-14',                
    timeframe="60min",  # only allow '<integer>min'
    provider="alpaca-file",
    symbol='',
    #symbol='SOUN',    
    sip_file='eps.txt',
    outdir='.',    
    days_before=1,
    days_after=20,
    daily_plot=True,
    transform=''
):
    """
    This function generates trade screenshots for a given set of symbols and timeframes.
    :param start: Stock in play date, e.g. '2023-12-06'
    :param timeframe: The timeframe for the trade screenshots. Only allows '<integer>min'. Defaults to "1min".
    :param provider: The provider for the trade data.
    :param symbol: The symbol, e.g. AAPL (overrides sip_file)
    :param sip_file: File containing list of dates and symbols
    :param trading_hour: The trading hour for the trade screenshots. Assumes OHLC data is in market time for symbol in question.
    :param outdir: The output directory for the generated trade screenshots.
    :param days: The number of days after SIP date, use 0 for all available data (max 30 days for intraday timeframe)
    :param daily_plot: Generate daily plot (if SIP intraday timeframe)
    :param transform: Transform the original OHLC data into this timeframe
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
            ta_indicators=['EMA10', 'VWAP']
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
            gen_daily=daily_plot            
        )
        handle_sip(config)
    else:
        raise ValueError("Missing symbol or sip_file")

if __name__ == "__main__":
    fire.Fire(main)

