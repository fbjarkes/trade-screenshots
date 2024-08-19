from dataclasses import dataclass
import json
import logging
from multiprocessing import Pool
import os
from typing import Dict, List, Optional, Union

import numpy as np
from trade_screenshots.plotter import Plotter
import trade_screenshots.utils as utils
from trade_screenshots import utils_ta
from trade_screenshots.common import VALID_TIME_FRAMES, weekday_to_string


import pandas as pd

logger = logging.getLogger(__name__)


VALID_TA =  ['EMA10', 'EMA20', 'EMA50', 'VWAP']

@dataclass
class SipConfig:
    start: str
    timeframe: str
    provider: str
    symbols_file: str
    symbol: str
    outdir: str
    transform: str
    rth_only: bool    
    paths: dict
    days_before: int = 3
    days_after: int = 0    
    gen_daily: bool = False    
    ta_indicators: List[str] = None
    #rth_ta: bool = True

def add_ta(sym, df, indicators, rth_only_ta=False):
    if not indicators:
        return df
    
    if rth_only_ta:
        df = utils_ta.add_ta(sym, df, indicators, start_time='09:30', end_time='16:00')
    else:
        df = utils_ta.add_ta(sym, df, indicators)
        if 'VWAP' in indicators:
            df = utils_ta.add_ta(sym, df, ['VWAP'], separate_by_day=True)
    return df
        
        


def get_dfs(config, first_date, last_date, timeframe, provider, paths, sym):
    daily_df = None
    # TODO: config.rth_only
    df = utils.get_dataframe(provider, sym, first_date, '', timeframe, path=paths[provider])
    if config.gen_daily:
        daily_df = utils.get_dataframe(provider, sym, first_date, '', 'day', path=paths[provider])

    print(f"{sym}: df start='{df.index[0]}' end='{df.index[-1]}'")
    if config.gen_daily:
        print(f"{sym}: daily_df start='{daily_df.index[0]}' end='{daily_df.index[-1]}'")
                
    if first_date < df.index[0] or last_date > df.index[-1]:
        raise ValueError(f"{sym}: Missing data for {first_date} - {last_date} ({timeframe}) (df={df.index[0]} - {df.index[-1]})")
    
    return df, daily_df
        

# TODO StocksInPlay class
def handle_sip(config: SipConfig):
    if config.symbol:
        symbol_dates = {config.symbol: [pd.Timestamp(config.start)]}
    else:
        symbol_dates = utils.parse_txt(config.symbols_file)
    timeframe = config.timeframe
    provider = config.provider
    outdir = config.outdir
    transform = config.transform
    days_before = config.days_before
    days_after = config.days_after
    paths = config.paths
    ta_indicators = config.ta_indicators
    
    if transform != '':
        timeframes_to_plot = transform.split(',')
        if not all(tf in VALID_TIME_FRAMES for tf in timeframes_to_plot):
            raise ValueError(f"Invalid timeframe in transform '{transform}'")
    else:
        timeframes_to_plot = [timeframe]
    
    for sym in symbol_dates.keys():
        try:
            dates_sorted = sorted(symbol_dates[sym])     
            first_date = dates_sorted[0] - pd.Timedelta(days=days_before)
            last_date = dates_sorted[-1] + pd.Timedelta(days=days_after)
            
            df, daily_df = get_dfs(config, first_date, last_date, timeframe, provider, paths, sym)

            for date in dates_sorted:
                # TODO: parallelize this loop              
                start_date, end_date = utils.get_plot_dates_weekend_adjusted(date, days_before, days_after)
                print(f"{sym}: creating intraday chart '{start_date}' to '{end_date}', for SIP date='{date}' ({weekday_to_string(date.weekday())})")

                df = df.sort_index() # !?
                chart_df = df.loc[f"{start_date}":f"{end_date}"]
                
                chart_df = add_ta(sym, chart_df, ta_indicators)
                
                # Daily/intraday levels:                
                # rth_0 = df.loc[f"{start_date} 09:30":f"{start_date} 15:45"]
                # mid = (rth_0['High'].max() + rth_0['Low'].min()) / 2
                # levels = {'today_mid': mid}            

                if timeframe == 'day':
                    create_daily_chart(outdir, sym, daily_df, date)
                else:
                    for tf in timeframes_to_plot:
                        create_intraday_chart(timeframe, outdir, ta_indicators, sym, date, chart_df, tf)                
                    if config.gen_daily:
                        create_daily_chart(outdir, sym, daily_df, date)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"{sym}: {e}. Skipping.") 


def create_intraday_chart(timeframe, outdir, ta_indicators, sym, date, chart_df, tf):
    chart_df = utils.transform_timeframe(chart_df, timeframe, tf)
    plotter = Plotter()                    
    fig = plotter.intraday_chart(chart_df, tf, sym, title=f"{sym} {date} ({tf})",                                                
                                                sip_start_marker={'text': f"SIP Start {date.strftime('%Y-%m-%d')}"},
                                                #levels=levels
                                                ta_indicators=ta_indicators
                                                )
    utils.write_file(fig, f"{outdir}/{sym}-{date.strftime('%Y-%m-%d')}-{tf}", 1600, 900)

def create_daily_chart(outdir, sym, daily_df, date):
    plotter = Plotter()
    daily_days_before = 100
    daily_days_after = 20
    start_date = date - pd.Timedelta(days=daily_days_before)
    end_date = date + pd.Timedelta(days=daily_days_after)
    daily_chart_df = daily_df.loc[f"{start_date}":f"{end_date}"]    
    fig = plotter.daily_chart(daily_chart_df, sym, title=f"{sym} {date.strftime('%Y-%m-%d')} (daily)", sip_date=date, sip_text='')
    utils.write_file(fig, f"{outdir}/{sym}-{date.strftime('%Y-%m-%d')}-daily", 1600, 900)


