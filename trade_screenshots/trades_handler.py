import trade_screenshots.plots as plots
import trade_screenshots.utils as utils
import trade_screenshots.utils_ta as utils_ta


import pandas as pd

def handle_trades(start, timeframe, transform, provider, trades_file, filetype, outdir, days, start_time, end_time, paths, ta_params, rth=True):
    trades = utils.parse_trades(trades_file)
    symbols = list(set([trade.symbol for trade in trades]))

    dfs_map = {}
    for symbol in symbols:
        if provider == 'tv':
            df = utils.get_dataframe_tv(start, timeframe, symbol, paths['tv'])
        else:
            df = utils.get_dataframe_alpaca(symbol, timeframe, paths['alpaca-file'])
            if rth:
                df = utils.filter_rth(df)
        if df.empty:
            print(f"Empty DataFrame for symbol {symbol}. Skipping")
        else:
            if transform != '':
                print(f"{symbol}: transforming df from {timeframe} to {transform}")
                df = utils.transform_timeframe(df, timeframe, transform)
            print(f"{symbol}: Applying TA to {len(df)} rows")
            if rth:
                df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'])
            else: 
                df = utils_ta.add_ta(symbol, df, ['EMA10', 'EMA20', 'EMA50', 'BB'], start_time, end_time)
            dfs_map[symbol] = df

    # last 10 trades:
    #trades = trades[-10:]
    for trade in trades:
        df = dfs_map[trade.symbol]
        start_date = pd.to_datetime(trade.start_dt).date() - pd.Timedelta(days=days)
        end_date = pd.to_datetime(trade.end_dt).date() + pd.Timedelta(days=days)
        df = df.loc[f"{start_date}":f"{end_date}"]
        # TODO: add daily chart as context, new image or combine both into large image
        fig = plots.generate_trade_chart(
                trade,
                df,
                tf=timeframe,
                title=f"{trades_file}-{trade.symbol}-{trade.start_dt[0:10]}",
                plot_indicators=['EMA10', 'EMA20', 'EMA50', 'BB_UPPER', 'BB_LOWER'],
                config=ta_params,
            )
            # format date like "2023-01-01_1500"

        suffix = trade.start_dt[:16].replace(' ', '_').replace(':', '')
        utils.write_file(fig, f"{outdir}/trades/{trade.symbol}-{suffix}", filetype, 1600, 900)