from finta import TA
import pandas as pd


def ema(df, period):
    df[f"EMA{period}"] = TA.EMA(df, period)
    return df


def vwap(df):
    df['VWAP'] = TA.VWAP(df)
    return df

def mid(df):
    # Assume df is 1 intraday, RTH only    
    max_high_values = [df['High'].iloc[0]]
    min_low_values = [df['Low'].iloc[0]]
    for index, row in df.iloc[1:].iterrows():
        max_high_values.append(max(max_high_values[-1], row['High']))
        min_low_values.append(min(min_low_values[-1], row['Low']))

    mid = (pd.Series(max_high_values, index=df.index) + pd.Series(min_low_values, index=df.index)) / 2
    df['Mid'] = mid
    return df

def or_levels(df, or_times):
    df_or = df.between_time(or_times[0], or_times[1])
    return df_or['Low'].min(), df_or['High'].max()

def bbands(df):
    bb = TA.BBANDS(df, period=20, std_multiplier=2.0)
    df['BB_UPPER'] = bb['BB_UPPER']
    df['BB_LOWER'] = bb['BB_LOWER']    
    return df

def add_ta(symbol, df, ta):
    # check if any row with time < 09:30 is present:
    if df.index[0].time() < pd.to_datetime('09:30').time():
        print("Warning: applying TA with AH/PM present")
    if 'VWAP' in ta:
        df = vwap(df)
    if 'EMA10' in ta:
        df = ema(df, 10)
    if 'EMA20' in ta:
        df = ema(df, 20)
    if 'EMA50' in ta:
        df = ema(df, 50)
    if 'BB' in ta:
        df = bbands(df)
    return df
