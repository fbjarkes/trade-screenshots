import fire
import utils
import utils_ta
import plots

PATHS = {'tv': '~/Bardata/tradingview',
         'alpaca-file': '~/Bardata/alpaca-v2'}

TA_PARAMS = {
        'VWAP': {'color': 'yellow'},
        'EMA10':  {'color': 'lightblue'},
        'EMA20': {'color': 'blue'},
        'EMA50': {'color': 'darkblue'},
        'DAILY_LEVEL': {'days': 1},
        'OR_LEVELS': {'start': '09:30', 'end': '10:30'}
    }

def main(
    start="2023-01-01",
    timeframe="5min",
    provider="tv",
    symbols="AAPL",
    duration='09:30-16:00',
    filetype="png",
    trades=None,
):
    symbols = symbols.split(",")    
    start_time, end_time = duration.split("-")
    

    # Call the processing function for each symbol
    for symbol in symbols:
        process_symbol(
            start=start,
            timeframe=timeframe,
            provider=provider,
            symbol=symbol,
            trades=trades,
            filetype=filetype,
            start_time=start_time,
            end_time=end_time
        )

def process_symbol(start, timeframe, provider, symbol, trades, filetype, start_time, end_time):

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

    df = utils_ta.add_ta(symbol, df,  ['EMA10', 'EMA20', 'EMA50'])
    
    print(f"{symbol}: Splitting data into days")
    dfs = utils.split(df, start_time, end_time)

    print(f"{symbol}: generating images for {len(dfs)} days")
    t = dfs[-2:] # Only last two while debugging
    for intraday_df in t:        
        date = intraday_df.index.date[0]
        utils_ta.vwap(intraday_df)      
        plots.generate_chart(intraday_df, symbol, f"{date}-{symbol}", type='png', ta_params={key: TA_PARAMS[key] for key in  ['VWAP', 'EMA10', 'EMA20', 'EMA50']}, or_levels=True)
    
    print("done")

if __name__ == "__main__":
    fire.Fire(main)
