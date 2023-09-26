import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os
import fire
import utils
import utils_ta
import plots

PATHS = {'tv': '~/Bardata/tradingview', 'alpaca-file': '~/Bardata/alpaca-v2'}

TA_PARAMS = {'VWAP': {'color': 'yellow'}, 'EMA10': {'color': 'lightblue'}, 
             'EMA20': {'color': 'blue'}, 
             'EMA50': {'color': 'darkblue'}, 
             'BB_UPPER': {'color': 'lightgrey'}, 
             'BB_LOWER': {'color': 'lightgrey'}, 
             'DAILY_LEVEL': {'days': 1}}


def main(
    start="2023-01-01", # TODO: start date needed?
    timeframe="5min",
    provider="tv",
    symbols="AAPL",
    trading_hour='09:30-16:00', # Assume OHLC data is in market time for symbol in question
    filetype="png",
    outdir='images',
    trades=None, #TODO: process trades.csv
):
    if isinstance(symbols, tuple):
        symbols = list(symbols)        
    elif ',' in symbols:
        symbols = symbols.split(',')
    else:
        symbols = [symbols]
    
    start_time, end_time = trading_hour.split("-")

    if not os.path.exists(outdir):
        raise Exception(f"Output directory '{outdir}' does not exist")
    
    #for symbol in symbols:
    # try: 
    #         process_symbol(symbol, start=start, timeframe=timeframe, provider=provider, trades=trades, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir)
    #     except Exception as e:
    #         print(f"Error processing symbol {symbol}: {e}. Skipping.")
    with ThreadPoolExecutor() as executor:
        #func = partial(process_symbol, start=start, timeframe=timeframe, provider=provider, trades=trades, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir)
        def func(symbol):
            try:
                return process_symbol(symbol, start=start, timeframe=timeframe, provider=provider, trades=trades, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir)
            except Exception as e:                
                print(f"Error processing symbol {symbol}: {e}. Skipping.")
                traceback.print_exc()
                return None
        
        results = list(executor.map(func, symbols))
    
    # TODO: async write files from results here



def process_symbol(symbol, start, timeframe, provider, trades, filetype, start_time, end_time, outdir):
    if provider == 'tv':
        df = utils.get_dataframe_tv(start, timeframe, symbol, PATHS['tv'])
    elif provider == 'alpaca-file':
        df = utils.get_dataframe_alpaca(start, timeframe, symbol, PATHS['alpaca-file'])
    elif provider == 'alpaca':
        df = utils.download_dataframe_alpaca(start, timeframe, symbol)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    if df.empty:
        raise Exception(f"Empty DataFrame for symbol {symbol}")

    print(f"{symbol}: Applying TA to {len(df)} rows")

    df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'])

    print(f"{symbol}: Splitting data into days")
    dfs = utils.split(df, start_time, end_time)

    print(f"{symbol}: generating images for {len(dfs)} days")
    dfs = dfs[-5:]
    for i in range(1, len(dfs)):
        today = dfs[i]
        yday = dfs[i - 1]
        date = today.index.date[0]
        levels = {'close_1': yday['Close'].iloc[-1], 'high_1': yday['High'].max(), 'low_1': yday['Low'].min()}
        utils_ta.vwap(today) # Add VWAP on intraday df
        fig = plots.generate_chart(
            today,
            symbol,
            f"{date}-{symbol}",
            plot_indicators={key: TA_PARAMS[key] for key in ['VWAP', 'EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER']},
            or_times=('09:30', '10:30'),
            daily_levels=levels,
        )
        utils.write_file(fig, f"{outdir}/{symbol}-{date}", filetype, 1600, 900)

    print("done")


if __name__ == "__main__":
    fire.Fire(main)
