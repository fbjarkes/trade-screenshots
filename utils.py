from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
import pandas as pd
import plotly.io as pio
from finta import TA
from typing import Any, List, Dict, Union


@dataclass
class Trade:
    symbol: str
    start_dt: str
    end_dt: str
    pnl: Decimal
    value: Decimal
    entry_price: Decimal
    exit_price: Decimal

def parse_trades(csv_file: str) -> List[Trade]:
    trades = []
    with open(csv_file) as f:
        for line in f.readlines()[1:]:
            row = line.split(',')
            try:
                # start_dt = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
                # end_dt = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S')
                trades.append(
                    Trade(symbol=row[2], start_dt=row[3], end_dt=row[4], pnl=Decimal(row[5]), value=Decimal(row[6]), entry_price=Decimal(row[7]), exit_price=Decimal(row[8]))
                )
            except Exception as e:
                print(f"Error parsing trade: {e}")
    return trades


def load_json_data(symbol: str, path: str) -> Union[Dict[str, List[Dict[str, Union[str, float]]]], None]:
    with open(path) as f:
        json_data = json.load(f)
        return json_data.get(symbol)


def process_json_data(data: Dict[str, List[Dict[str, Union[str, float]]]], symbol: str) -> Union[pd.DataFrame, None]:
    if data:
        df = pd.DataFrame(data, columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df.set_index('DateTime', inplace=True)
        # TODO: add freq?
        # Convert to Wall Street time since all trades have start/dates in Wall Street time
        df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
        # TODO: remove extended hours?
        df.name = symbol
        return df
    else:
        print(f"Symbol {symbol} not found in the json")


def get_dataframe_alpaca(symbol, timeframe, path):
    file_path = f"{path}/{timeframe}/{symbol}.json"
    print(f"{symbol}: parsing alpaca file data '{file_path}'")
    data = load_json_data(symbol, file_path)
    return process_json_data(data, symbol)


def get_dataframe_tv(start: str, timeframe: str, symbol: str, path: str) -> Union[pd.DataFrame, None]:
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


def download_dataframe_alpaca(start: str, timeframe: str, symbol: str) -> pd.DataFrame:
    print(f"Downloading Alpaca data for {symbol} timeframe={timeframe} and start={start}")
    return pd.DataFrame()


def split(df: pd.DataFrame, start_time: str, end_time: str, eth_values: Dict[str, Dict[str, Union[float, str]]]) -> List[pd.DataFrame]:
    start = pd.to_datetime(start_time).time()
    end = pd.to_datetime(end_time).time()

    dfs = []
    ah_df = None
    for date, group_df in df.groupby(df.index.date):
        filtered_df = group_df.between_time(start_time, end_time, inclusive='left')
        pm_df = group_df.between_time('04:00', start_time, inclusive='left')
        if not filtered_df.empty:
            dfs.append(filtered_df)
            if ah_df is not None:
                eth_df = pd.concat([ah_df, pm_df])
            else:
                eth_df = pm_df
            eth_values[date] = {'low': eth_df['Low'].min(), 'high': eth_df['High'].max()}

        ah_df = group_df.between_time(end_time, '20:00')
    return dfs


def write_file(fig: Any, filename: str, type: str, width: int, height: int) -> None:
    if type == "html":
        fig.write_html(f"{filename}.html")
        print(f"Wrote '{filename}.html'")
    elif type == "png":
        pio.write_image(fig, f"{filename}.png", width=width, height=height)
        print(f"Wrote '{filename}.png'")
    elif type == 'webp':
        pio.write_image(fig, f"{filename}.webp")
        print(f"Wrote '{filename}.webp'")
    elif type == 'svg':
        pio.write_image(fig, f"{filename}.svg")
        print(f"Wrote '{filename}.svg'")
    else:
        raise ValueError("Unsupported file type:", type)


def parse_txt(filename: str) -> Dict[str, pd.Timestamp]:
    with open(filename) as f:
        lines = f.readlines()
        sym_map = {}
        for line in lines:
            date, symbols = line.split(':')
            for sym in symbols.split(','):
                sym = sym.strip()
                if sym in sym_map:                    
                    sym_map[sym].append(pd.to_datetime(date))
                else:
                    sym_map[sym] = [pd.to_datetime(date)]
        return sym_map

def transform_timeframe(df: pd.DataFrame, timeframe:str, transform:str) -> pd.DataFrame:
    if timeframe == transform or df.empty:
        return df  # No need to transform
    conversion = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
    resampled = df.resample(f"{transform}").agg(conversion)
    return resampled.dropna()
