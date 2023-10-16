from concurrent.futures import ProcessPoolExecutor
from functools import partial
import trade_screenshots.plots as plots
import trade_screenshots.utils as utils
from trade_screenshots import utils_ta
from trade_screenshots.common import PATHS, TA_PARAMS, try_process_symbol

# TODO: use partial decorator ? @functools.partial()
def process_symbol(symbol, start, timeframe, provider, filetype, start_time, end_time, outdir, days):
    if provider == 'tv':
        df = utils.get_dataframe_tv(start, timeframe, symbol, PATHS['tv'])
    elif provider == 'alpaca-file':
        df = utils.get_dataframe_alpaca(symbol, timeframe, PATHS['alpaca-file'])
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
    if days != 0:
        dfs = dfs[-days:]

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

        fig = plots.generate_chart(
            today,
            timeframe,
            symbol,
            title=f"{symbol} {date} ({timeframe})",
            plot_indicators={key: TA_PARAMS[key] for key in ['VWAP', 'EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER', 'Mid']},
            or_times=('09:30', '10:30'),
            daily_levels=levels,
        )

        utils.write_file(fig, f"{outdir}/{symbol}-{date}", filetype, 1600, 900)

    print("done")


def handle_symbols(start, timeframe, provider, symbols, filetype, outdir, days, start_time, end_time):
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
                process_symbol, start=start, timeframe=timeframe, provider=provider, filetype=filetype, start_time=start_time, end_time=end_time, outdir=outdir, days=days
            )
        try_func = partial(try_process_symbol, func)
        results = list(executor.map(try_func, symbols))