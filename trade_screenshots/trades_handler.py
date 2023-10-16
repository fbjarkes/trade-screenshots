from trade_screenshots.common import PATHS, TA_PARAMS
import trade_screenshots.plots as plots
import trade_screenshots.utils as utils
import trade_screenshots.utils_ta as utils_ta


import pandas as pd

def handle_trades(start, timeframe, trades_file, filetype, outdir, days, start_time, end_time):
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