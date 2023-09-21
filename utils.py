import json
import pandas as pd

def load_json_data(symbol: str, path: str):
    with open(path) as f:
        json_data = json.load(f)       
        return json_data.get(symbol)

def process_json_data(data: dict, symbol: str):
    if data:        
        df = pd.DataFrame(data, columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df.set_index('DateTime', inplace=True)
        # TODO: add freq?
        # Convert to Wall Street time since all trades have start/dates in Wall Street time
        df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
        #TODO: remove extended hours?
        df.name = symbol
        return df
    else:
        print(f"Symbol {symbol} not found in the json")
    
        
def get_dataframe_alpaca(start, timeframe, symbol, path):
    file_path = f"{path}/{timeframe}/{symbol}.json"
    print(f"{symbol}: parsing alpaca file data '{file_path}'")     
    data = load_json_data(symbol, file_path)    
    return process_json_data(data, symbol)
    
    
def get_dataframe_tv(start, timeframe, symbol, path):
    file_path = f"{path}/{timeframe}/{symbol}.csv"
    print(f"{symbol}: parsing tradingview data '{file_path}'")   
    try:
        df = pd.read_csv(file_path, index_col='time', parse_dates=False, usecols=['time', 'open', 'high', 'low', 'close', 'Volume'])
        df.index = pd.to_datetime(df.index, unit='s', utc=True).tz_convert('America/New_York').tz_localize(None)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)      
        df.name = symbol
        return df
    except Exception as e:
        print(f"Error parsing csv '{path}': {e}")
    
    return pd.DataFrame()


def download_dataframe_alpaca(start, timeframe, symbol):
    print(f"Downloading Alpaca data for {symbol} timeframe={timeframe} and start={start}")
    return pd.DataFrame()