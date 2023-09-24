from finta import TA


def ema(df, period):
    df[f"EMA{period}"] = TA.EMA(df, period)
    return df

def vwap(df):
    df['VWAP'] = TA.VWAP(df)
    return df

def or_levels(df, or_times):
    df_or = df.between_time(or_times[0], or_times[1])
    return df_or['Low'].min(), df_or['High'].max()

def add_ta(symbol, df, ta):
    if 'VWAP' in ta:
        df = vwap(df)
    if 'EMA10' in ta:
        df = ema(df, 10)
    if 'EMA20' in ta:
        df = ema(df, 20)
    if 'EMA50' in ta:
        df = ema(df, 50)
    return df
