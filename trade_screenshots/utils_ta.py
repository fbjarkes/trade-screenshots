from finta import TA
import pandas as pd
from typing import List, Tuple


def ema(df: pd.DataFrame, period: int) -> pd.DataFrame:
    df[f"EMA{period}"] = TA.EMA(df, period)
    return df


def vwap(df: pd.DataFrame) -> pd.DataFrame:
    df['VWAP'] = TA.VWAP(df)
    return df


def mid(df: pd.DataFrame) -> pd.DataFrame:
    # Assume df is 1 intraday, RTH only
    max_high_values = [df['High'].iloc[0]]
    min_low_values = [df['Low'].iloc[0]]
    for index, row in df.iloc[1:].iterrows():
        max_high_values.append(max(max_high_values[-1], row['High']))
        min_low_values.append(min(min_low_values[-1], row['Low']))

    mid = (pd.Series(max_high_values, index=df.index) + pd.Series(min_low_values, index=df.index)) / 2
    df['Mid'] = mid
    return df


def or_levels(df: pd.DataFrame, or_times: Tuple[str, str]) -> Tuple[float, float]:
    df_or = df.between_time(or_times[0], or_times[1])
    return df_or['Low'].min(), df_or['High'].max()


def bbands(df: pd.DataFrame) -> pd.DataFrame:
    bb = TA.BBANDS(df, period=20, std_multiplier=2.0)
    df['BB_UPPER'] = bb['BB_UPPER']
    df['BB_LOWER'] = bb['BB_LOWER']
    return df


def add_ta(symbol: str, df: pd.DataFrame, ta: List[str], start_time: str, end_time: str) -> pd.DataFrame:
    if start_time and end_time:
        df_ta = df.between_time(start_time, end_time, inclusive='left').copy()
    else:
        df_ta = df
    if 'VWAP' in ta:
        df_ta = vwap(df_ta)
    if 'EMA10' in ta:
        df_ta = ema(df_ta, 10)
    if 'EMA20' in ta:
        df_ta = ema(df_ta, 20)
    if 'EMA50' in ta:
        df_ta = ema(df_ta, 50)
    if 'BB' in ta:
        df_ta = bbands(df_ta)
    if start_time and end_time:
        return df_ta.combine_first(df)
    else:
        return df_ta
