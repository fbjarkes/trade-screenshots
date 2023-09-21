import fire
import utils

PATHS = {'tv': '~/Bardata/tradingview',
         'alpaca-file': '~/Bardata/alpaca-v2'}

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
    # Implement provider-specific data fetching here
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
    df = utils.add_ema(df, 10)
    df = utils.add_ema(df, 20)

    dfs = utils.split(df, start_time, end_time)
    print(f"{symbol}: generating images for {len(dfs)} days")
    


if __name__ == "__main__":
    fire.Fire(main)
