import time
import traceback
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import os
import fire
import utils
import utils_ta
import plots
import pandas as pd

PATHS = {'tv': '~/Bardata/tradingview', 'alpaca-file': '/Users/fbjarkes/Bardata/alpaca-v2'}

TA_PARAMS = {
    'VWAP': {'color': 'yellow'},
    'EMA10': {'color': 'lightblue'},
    'EMA20': {'color': 'blue'},
    'EMA50': {'color': 'darkblue'},
    'BB_UPPER': {'color': 'lightgrey'},
    'BB_LOWER': {'color': 'lightgrey'},
    'Mid': {'color': 'red'},
    'DAILY_LEVEL': {'days': 1},
}

TIME_FRAMES = ['1min', '2min', '3min', '5min', '15min', '30min', '60min'] # Must be valid pandas freq. values

def try_process_symbol(fun, symbol):
    try:
        fun(symbol)
    except Exception as e:
        print(f"Error processing symbol {symbol}: {e}. Skipping.")
        traceback.print_exc()
        return None

def weekday_to_string(weekday):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return days[weekday]

def main(
    start="2023-01-01",  # TODO: start date needed?
    timeframe="1min",  # only allow '<integer>min'
    provider="alpaca-file",
    symbols=None, #"2023-10-02_NVDA",
    trading_hour='09:30-16:00',  # Assume OHLC data is in market time for symbol in question
    filetype="png",
    outdir='images',
    # trades_file='trades.csv'
    trades_file=None,
    symbols_file='stocks_in_play.txt',
    days=0,
):
    if symbols and (trades_file or symbols_file):
        raise ValueError("symbols, trades_file, and symbols_file are mutually exclusive")
    
    if not os.path.exists(outdir):
        raise Exception(f"Output directory '{outdir}' does not exist")
    
    if trading_hour:
        start_time, end_time = trading_hour.split("-")
    else:
        start_time, end_time = None, None
    
    if symbols:
        if isinstance(symbols, tuple):
            symbols = list(symbols)
        elif ',' in symbols:
            symbols = symbols.split(',')
        else:
            symbols = [symbols]
        with ProcessPoolExecutor() as executor:
            # def func(symbol):
            #     try:
            #         return process_symbol(symbol, start=start, timeframe=timeframe, provider=provider, trades=trades, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir)
            #     except Exception as e:
            #         print(f"Error processing symbol {symbol}: {e}. Skipping.")
            #         traceback.print_exc()
            #         return None
            func = partial(
                process_symbol, start=start, timeframe=timeframe, provider=provider, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir
            )
            try_func = partial(try_process_symbol, func)
            results = list(executor.map(try_func, symbols))

    elif trades_file:
        trades = utils.parse_trades(trades_file)
        symbols = list(set([trade.symbol for trade in trades]))

        dfs_map = {}
        for symbol in symbols:
            df = utils.get_dataframe_tv(start, timeframe, symbol, PATHS['tv'])
            if df.empty:
                print(f"Empty DataFrame for symbol {symbol}. Skipping")
            else:
                print(f"{symbol}: Applying TA to {len(df)} rows")
                df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'], start_time, end_time)
                dfs_map[symbol] = df

        for trade in trades:
            df = dfs_map[trade.symbol]
            start_date = pd.to_datetime(trade.start_dt).date() - pd.Timedelta(days=days)
            end_date = pd.to_datetime(trade.end_dt).date() + pd.Timedelta(days=days)
            df = df.loc[f"{start_date}":f"{end_date}"]
            fig = plots.generate_trade_chart(
                trade,
                df,
                tf=timeframe,
                title=f"{trades_file}-{trade.symbol}-{trade.start_dt[0:10]}",
                plot_indicators=['EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER'],
                config=TA_PARAMS,
            )
            # format date like "2023-01-01_1500"
            suffix = trade.start_dt[:16].replace(' ', '_').replace(':', '')
            utils.write_file(fig, f"{outdir}/trades/{trade.symbol}-{suffix}", filetype, 1600, 900)     
    
    elif symbols_file:
        symbol_dates = utils.parse_txt(symbols_file)
        for sym in symbol_dates.keys():
            # 1. get df from first to last date present including 3 extra days if first date is a Monday
            dates_sorted = sorted(symbol_dates[sym])
            first_date = dates_sorted[0] - pd.Timedelta(days=3)
            last_date = dates_sorted[-1]
            print(f"{sym}: getting df for {first_date} - {last_date}")
            df = utils.get_dataframe_alpaca(sym, timeframe, PATHS['alpaca-file'])
            print(f"{sym}: df start={df.index[0]} end={df.index[-1]}")
            
            # TODO: verify first/last dates are in df        

            # 2. apply TA etc (also jlines or EMA50 only?)
            df = utils_ta.add_ta(sym, df, ['EMA10', 'EMA20', 'EMA50'], start_time=None, end_time=None) # Apply TA to AH/PM
            #TODO: TA missing
                        
            # 3. plot chart for each date, including ah/pm,
            for date in dates_sorted:                
                start_date = date - pd.Timedelta(days=3) if date.weekday() == 0 else date- pd.Timedelta(days=1)                       
                end_date = date + pd.DateOffset(days=1)
                print(f"{sym}: {date} ({weekday_to_string(date.weekday())}) creating chart using dates {start_date}-{end_date}")
                
                filtered_df = df.loc[f"{start_date}":f"{end_date}"]                
                
                for tf in ['5min', '15min']:
                    filtered_df = utils.transform_timeframe(filtered_df, '1min', tf)
                    fig = plots.generate_chart(filtered_df, tf, sym, title=f"{sym} {date} ({tf})")                    
                    utils.write_file(fig, f"{outdir}/{sym}-{date.strftime('%Y-%m-%d')}-{tf}", filetype, 1600, 900)
    else:
        raise ValueError("symbols, trades_file, or symbols_file must be provided")


# TODO: use partial decorator ? @functools.partial()
def process_symbol(symbol, start, timeframe, provider, filetype, start_time, end_time, outdir):
    if provider == 'tv':
        df = utils.get_dataframe_tv(start, timeframe, symbol, PATHS['tv'])
    elif provider == 'alpaca-file':
        df = utils.get_dataframe_alpaca(start, timeframe, symbol, PATHS['alpaca-file'])  # TODO: not implemented
    elif provider == 'alpaca':
        df = utils.download_dataframe_alpaca(start, timeframe, symbol)  # TODO: not implemented
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if df.empty:
        raise Exception(f"Empty DataFrame for symbol {symbol}")

    print(f"{symbol}: Applying TA to {len(df)} rows")

    # TODO: add mid,vwap, daily/ah/pm levels and store in dataframe as constant values? and write test for it?
    df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'], start_time, end_time)

    print(f"{symbol}: Splitting data into days")
    eth_values = {}
    dfs = utils.split(df, start_time, end_time, eth_values)
    
    dfs = dfs[-2:]
    print(f"{symbol}: generating images for {len(dfs)} days")    
    for i in range(1, len(dfs)):
        today = dfs[i]
        yday = dfs[i - 1]
        date = today.index.date[0]
        levels = {
            'close_1': yday['Close'].iloc[-1],
            'high_1': yday['High'].max(),
            'low_1': yday['Low'].min(),
            'eth_low': eth_values[date]['low'],
            'eth_high': eth_values[date]['high'],
        }

        utils_ta.vwap(today)
        utils_ta.mid(today)

        # TODO: option to plot 1-2 days before today (for stocks in play with specific dates)
        fig = plots.generate_chart(
            today,
            timeframe,
            symbol,
            f"{date}-{symbol}",
            plot_indicators={key: TA_PARAMS[key] for key in ['VWAP', 'EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER', 'Mid']},
            or_times=('09:30', '10:30'),
            daily_levels=levels,
        )

        utils.write_file(fig, f"{outdir}/{symbol}-{date}", filetype, 1600, 900)

    print("done")


if __name__ == "__main__":
    fire.Fire(main)
