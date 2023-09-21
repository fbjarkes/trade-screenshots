import fire
import utils

PATHS = {'tv': '~/Bardata/tradingview',
         'alpaca-file': '~/Bardata/alpaca-v2'}

def main(
    start="2023-01-01",
    timeframe="5min",
    provider="tv",
    symbols="AAPL",
    duration=None,
    filetype="png",
    trades=None,
):
    symbols = symbols.split(",")
    if duration:
        start_time, end_time = duration.split("-")
        # Process start_time and end_time here if needed

    # Call the processing function for each symbol
    for symbol in symbols:
        process_symbol(
            start=start,
            timeframe=timeframe,
            provider=provider,
            symbol=symbol,
            trades=trades,
            filetype=filetype,
        )

def process_symbol(start, timeframe, provider, symbol, trades, filetype):
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
    
    # Apply technical analysis using Finta
    print('Applying TA to ', df)

    # Split DataFrame into subsets for each trading day
    print('Splitting DataFrame into subsets for each trading day')

    # Generate and save candlestick charts using Plotly
print('Generating and saving candlestick charts using Plotly')

if __name__ == "__main__":
    fire.Fire(main)
