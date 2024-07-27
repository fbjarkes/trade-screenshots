from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import reduce
import json
import logging
from multiprocessing import Pool
import os
import pandas as pd
import plotly.io as pio
from finta import TA
from typing import Any, Callable, List, Dict, Optional, Tuple, Union


logger = logging.getLogger(__name__)



# TODO: either expose Trade type dataclass or just use basic data type or dict
@dataclass
class Trade:
    symbol: str
    entry_date: str
    exit_date: str
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
                    Trade(symbol=row[2], entry_date=row[3], exit_date=row[4], pnl=Decimal(row[5]), value=Decimal(row[6]), entry_price=Decimal(row[7]), exit_price=Decimal(row[8]))
                )
            except Exception as e:
                print(f"Error parsing trade: {e}")
    return trades

# #TODO: copy latest version to 'python-aux' repo and use here instead
# def load_json_data(symbol: str, path: str) -> Union[Dict[str, List[Dict[str, Union[str, float]]]], None]:
#     with open(path) as f:
#         json_data = json.load(f)
#         return json_data.get(symbol)

# def process_json_data(data: Dict[str, List[Dict[str, Union[str, float]]]], symbol: str) -> Union[pd.DataFrame, None]:
#     if data:
#         df = pd.DataFrame(data, columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
#         df.set_index('DateTime', inplace=True)
#         # TODO: add freq?
#         # Convert to Wall Street time since all trades have start/dates in Wall Street time
#         df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
#         # TODO: remove extended hours?
#         df.attrs['symbol'] = symbol
#         return df
#     else:
#         print(f"Symbol {symbol} not found in the json")


# def get_dataframe_alpaca(symbol, timeframe, path):
#     file_path = f"{path}/{timeframe}/{symbol}.json"
#     data = load_json_data(symbol, file_path)
#     return process_json_data(data, symbol)


# def get_dataframe_tv(start: str, timeframe: str, symbol: str, path: str) -> Union[pd.DataFrame, None]:
#     file_path = f"{path}/{timeframe}/{symbol}.csv"
#     try:
#         df = pd.read_csv(file_path, index_col='time', parse_dates=False, usecols=['time', 'open', 'high', 'low', 'close', 'Volume'])
#         df.index = pd.to_datetime(df.index, unit='s', utc=True).tz_convert('America/New_York').tz_localize(None)
#         df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
#         df.attrs['symbol'] = symbol
#         return df
#     except Exception as e:
#         print(f"Error parsing csv '{path}': {e}")

#     return pd.DataFrame()


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

#TODO: part of Plotter class? (not expose and utils functions from this lib?)
def write_file(fig: Any, filename: str, width: int, height: int, verbose=0) -> str:
    dirs = filename.split('/')
    if len(dirs) > 1:
        dir_path = '/'.join(dirs[:-1])
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
   
    pio.write_image(fig, f"{filename}.png", width=width, height=height)
    if verbose > 0:
        print(f"Wrote '{filename}.png'")
    
    return f"{filename}.png"


def get_plot_dates_weekend_adjusted(date: pd.Timestamp, days_before: int, days_after: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    if days_before == 0:
        start_date = date
    else:
        if date.weekday() == 0:
            start_date = date - pd.Timedelta(days=days_before+2)
        elif date.weekday() == 1:
            start_date = date - pd.Timedelta(days=days_before+(2 if days_before > 1 else 0))
        elif date.weekday() == 2:
            start_date = date - pd.Timedelta(days=days_before+(2 if days_before > 2 else 0))
        elif date.weekday() == 3:
            start_date = date - pd.Timedelta(days=days_before+(2 if days_before > 3 else 0))
        elif date.weekday() == 4:
            start_date = date - pd.Timedelta(days=days_before+(2 if days_before > 4 else 0))
    
    if days_after == 0:
        end_date = date + pd.Timedelta(days=1)
    else:
        end_date = date + pd.Timedelta(days=days_after)
    
    return start_date.normalize(), end_date.normalize()


def parse_txt(filename: str) -> Dict[str, pd.Timestamp]:
    """
    Example file content:
    2023-10-13:SPY,AAPL
    2023-10-12:META,NVDA
    ...
    """
    symbol_map = {}
    try:
        with open(filename) as f:
            for line in f:
                # if line does not contain ':':
                if line.startswith('#') or ':' not in line:
                    continue
                date, symbols = line.strip().split(':')
                for symbol in symbols.split(','):
                    symbol = symbol.strip()
                    if symbol:
                        symbol_map.setdefault(symbol, []).append(pd.to_datetime(date))
    except FileNotFoundError:
        raise FileNotFoundError(f'File {filename} not found')
    except Exception as e:
        raise RuntimeError(f'An error occurred while parsing the file: {str(e)}')
    return symbol_map

# def transform_timeframe(df: pd.DataFrame, timeframe:str, transform:str) -> pd.DataFrame:
#     # TODO: only allow resample from low to high?     
#     if timeframe == transform or df.empty:
#         return df  # No need to transform
#     conversion = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
#     resampled = df.resample(f"{transform}").agg(conversion)
#     return resampled.dropna()

# def filter_rth(df: pd.DataFrame, start='09:30', end='16:00') -> pd.DataFrame:
#     # Filter out start/end times from df
#     return df.between_time(start, end, inclusive='left')



################### https://github.com/fbjarkes/python-utils.git
def transform_timeframe(df: pd.DataFrame, timeframe: str, transform: str) -> pd.DataFrame:
    if timeframe == transform or df.empty:
        return df
    conversion = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
    if timeframe == 'day' and transform == 'month':
        resampled = df.resample('ME').agg(conversion)
    elif timeframe == 'day' and transform == 'week':
        resampled = df.resample('W').agg(conversion)
    else:
        resampled = df.resample(f"{transform}").agg(conversion)
    resampled.attrs['timeframe'] = transform
    return resampled.dropna()

def filter_rth(df: pd.DataFrame, start_time='09:30', end_time='16:00') -> pd.DataFrame:
    if start_time and end_time and not df.empty and df.attrs['timeframe'] not in ['day', 'week', 'month']:
        if df.attrs['timeframe'] == '60min':
            start_time = '09:00'
        return df.between_time(start_time, end_time, inclusive='left')
    else:
        return df


def filter_date(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    if start and end and not df.empty:
        df = df[start:end]
        return df
    if end and not df.empty:
        df = df[:end]
        return df
    return df


def get_dataframe_tv(timeframe: str, symbol: str, path: str, tz='America/New_York', include_all_columns: bool = True) -> Union[pd.DataFrame, None]:
    file_path = f"{path}/{timeframe}/{symbol}.csv"
    logger.debug(f"{symbol}: parsing tradingview data '{file_path}'")
    default_cols = ['time', 'open', 'high', 'low', 'close', 'Volume']
    try:
        if include_all_columns:
            df = pd.read_csv(file_path, index_col='time', parse_dates=False)
        else:
            df = pd.read_csv(file_path, index_col='time', parse_dates=False, usecols=default_cols)
        if tz:
            df.index = pd.to_datetime(df.index, unit='s', utc=True).tz_convert(tz).tz_localize(None)
        else:
            df.index = pd.to_datetime(df.index, unit='s', utc=True).tz_localize(None)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
        df.attrs = {'symbol': symbol, 'timeframe': timeframe}
        duplicates = df.index.duplicated(keep='first')
        dupe_count = duplicates.sum()
        if dupe_count > 0:
            # remove duplicate rows
            df = df[~duplicates]
        logger.debug(f"{symbol}: {len(df)} rows (start={df.index[0]}, end={df.index[-1]} dupes={dupe_count}) ")
        return df
    except Exception as e:
        logger.warning(f"Error parsing csv '{path}': {e}")

    return pd.DataFrame()

def get_dataframe_ib(timeframe: str, symbol: str, path: str, tz='America/New_York') -> Optional[pd.DataFrame]:
    p = os.path.expanduser(os.path.join(path, timeframe, f"{symbol}.csv"))
    try:
        df = pd.read_csv(p, dtype={'Open': np.float32, 'High': np.float32, 'Low': np.float32, 'Close': np.float32, 'Volume': np.float32}, parse_dates=True, index_col='Date')
        # TODO need to convert to TZ America/New_York ?
        df = df.sort_index()
        df.attrs = {'symbol': symbol, 'timeframe': timeframe}
        logger.debug(f"{symbol}: {len(df)} rows (start={df.index[0]}, end={df.index[-1]})")
        return df
    except Exception as e:
        logger.warning(f"Error parsing csv '{path}': {e}")
    return pd.DataFrame()


def load_json_data(symbol: str, path: str) -> Optional[Dict]:
    logger.debug(f"{symbol}: loading json data '{path}'")
    with open(path) as f:
        json_data = json.load(f)
        symbol_data = json_data.get(symbol)
        if not symbol_data:
            logger.warning(f"Missing symbol '{symbol}' in file '{path}'")
        else:
            return symbol_data
    return None


def json_to_dataframe(symbol: str, timeframe: str, data: Optional[Dict]) -> pd.DataFrame:
    if data is None:
        return pd.DataFrame(columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df = pd.DataFrame(data, columns=['DateTime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.set_index('DateTime', inplace=True)
    # Always assume Wall Street
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York').tz_localize(None)
    df = df.sort_index()  # TODO: Never needed before?!
    df.attrs = {'symbol': symbol, 'timeframe': timeframe}
    return df


def get_dataframe_alpaca_file(timeframe: str, symbol: str, path: str) -> Union[pd.DataFrame, None]:
    file_path = os.path.expanduser(f"{path}{os.sep}{timeframe}{os.sep}{symbol}.json")
    json_data = load_json_data(symbol, file_path)
    return json_to_dataframe(symbol, timeframe, json_data)


def get_dataframe(provider, symbol, start, end, timeframe, rth_only=False, path=None, transform='') -> pd.DataFrame:
    if not path:
        raise Exception(f"Missing path for provider '{provider}'")

    post_process = pipe(
        lambda df: transform_timeframe(df, timeframe, (transform if transform else timeframe)),
        lambda df: filter_rth(df) if rth_only else df,
        lambda df: filter_date(df, start, end),
    )
    if provider == 'tv':
        return post_process(get_dataframe_tv(timeframe=timeframe, symbol=symbol, path=path))
    elif provider == 'alpaca-file':
        return post_process(get_dataframe_alpaca_file(timeframe=timeframe, symbol=symbol, path=path))
    elif provider == 'ib':
        return post_process(get_dataframe_ib(timeframe=timeframe, symbol=symbol, path=path))
    else:
        raise Exception(f"Unknown provider '{provider}'")


def get_symbols(symbol_list):
    if symbol_list[0].startswith('/'):
        file = symbol_list[0]
        symbols = []
        with open(file) as f:
            symbols += [ticker.rstrip() for ticker in f.readlines() if not ticker.startswith('#')]
        symbols = list(set(symbols))  # NOTE: reorders elements
    else:
        symbols = list(set(symbol_list))  # NOTE: reorders elements
    return symbols


def get_dataframes(provider, symbol_list, start, end, timeframe, rth_only=False, path=None, transform='', process_workers=0) -> List[pd.DataFrame]:
    if not path:
        raise Exception(f"Missing path for provider '{provider}'")

    symbols = get_symbols(symbol_list)
    dfs = []

    if process_workers > 0:
        with Pool(process_workers) as pool:
            dfs = pool.starmap(get_dataframe, [(provider, symbol, start, end, timeframe, rth_only, path, transform) for symbol in symbols])
            dfs = [df for df in dfs if not df.empty]
    else:
        for symbol in symbols:
            df = get_dataframe(provider, symbol, start, end, timeframe, rth_only, path, transform)
            if not df.empty:
                dfs.append(df)
    return dfs


def pipe(*functions: Callable) -> Callable:
    return reduce(lambda f, g: lambda x: g(f(x)), functions)