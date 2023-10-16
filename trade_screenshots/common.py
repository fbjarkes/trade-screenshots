import traceback


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
    'Jlines': {'color': 'green'}
}

TIME_FRAMES = ['1min', '2min', '3min', '5min', '15min', '30min', '60min'] # Must be valid pandas freq. values

def try_process_symbol(fun, symbol):
    try:
        fun(symbol)
    except Exception as e:
        print(f"Error processing symbol {symbol}: {e}. Skipping.")
        traceback.print_exc()
        return None
