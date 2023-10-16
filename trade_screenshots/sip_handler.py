import trade_screenshots.plots as plots
import trade_screenshots.utils as utils
from trade_screenshots import utils_ta
from trade_screenshots.common import weekday_to_string


import pandas as pd


def handle_sip(timeframe, symbols_file, filetype, outdir, paths, ta_params):
    symbol_dates = utils.parse_txt(symbols_file)
    for sym in symbol_dates.keys():
            # 1. get df from first to last date present including 3 extra days if first date is a Monday
        dates_sorted = sorted(symbol_dates[sym])
        first_date = dates_sorted[0] - pd.Timedelta(days=3)
        last_date = dates_sorted[-1]
        print(f"{sym}: getting df for {first_date} - {last_date}")
        df = utils.get_dataframe_alpaca(sym, timeframe, paths['alpaca-file'])
        print(f"{sym}: df start={df.index[0]} end={df.index[-1]}")

            # verify first/last dates are in df
        if first_date < df.index[0] or last_date > df.index[-1]:
            raise ValueError(f"{sym}: Missing data for {first_date} - {last_date} (df={df.index[0]} - {df.index[-1]})")

            # 3. plot chart for each date, including ah/pm,
        for date in dates_sorted:
            start_date = date - pd.Timedelta(days=3) if date.weekday() == 0 else date- pd.Timedelta(days=1)
            end_date = date + pd.DateOffset(days=1)
            print(f"{sym}: {date} ({weekday_to_string(date.weekday())}) creating chart using dates {start_date}-{end_date}")

            filtered_df = df.loc[f"{start_date}":f"{end_date}"]

            for tf in ['5min', '15min']:
                filtered_df = utils.transform_timeframe(filtered_df, '1min', tf)
                    # Applies to PM/AH
                filtered_df = utils_ta.add_ta(sym, filtered_df, ['EMA10', 'EMA20', 'EMA50'], start_time=None, end_time=None)
                fig = plots.generate_chart(filtered_df, tf, sym, title=f"{sym} {date} ({tf})",
                                               plot_indicators={key: ta_params[key] for key in ['EMA10', 'EMA20', 'EMA50']})
                utils.write_file(fig, f"{outdir}/{sym}-{date.strftime('%Y-%m-%d')}-{tf}", filetype, 1600, 900)