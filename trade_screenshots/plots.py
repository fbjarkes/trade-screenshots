from functools import partial
from typing import Any, Dict, Optional
import functools
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import trade_screenshots.utils_ta as utils_ta
#TODO: need separate generate chart functions?


def create_trade_chart(trade, df, indicators):
    """
    Create chart with dates based on trade data and add buy/sell markers
    """
    ...
    
def create_chart(df, title, indicators):
    """
    Create chart with dates based on df
    """
    ...


# TODO: either expose Trade type dataclass or just use basic data type or dict
def trade_chart(trade, df, tf, title, plot_indicators, config):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])

    candlestick = go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=trade.symbol)
    volume = go.Bar(x=df.index, y=df['Volume'], name='Volume', marker=dict(color='blue'))

    ta_lines = []
    for ta in plot_indicators:
        line = go.Scatter(
            x=df.index,
            y=df[ta],
            name=ta,
            line=dict(color=config[ta]['color']),
        )
        ta_lines.append(line)

    fig.add_trace(candlestick, row=1, col=1)
    for line in ta_lines:
        fig.add_trace(line, row=1, col=1)
    fig.add_trace(volume, row=2, col=1)

    if trade.value < 0:
        v_align = -100
    else:
        v_align = 100

    fig.add_annotation(
        x=trade.start_dt, y=trade.entry_price, text=f"Entry ({trade.value:.0f})", showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)
    )
    fig.add_annotation(
        x=trade.end_dt, y=trade.exit_price, text=f"Exit ({trade.pnl:.1f})", showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)
    )

    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=title)
    # fig.update_layout(xaxis_type='date', xaxis=dict(dtick=180*60*1000))
    dt_all = pd.date_range(start=df.index[0], end=df.index[-1], freq=tf)
    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in df.index]
    # dt_breaks = pd.to_datetime(['2023-09-29 17:00:00', '2023-09-29 20:00:00', '2023-09-29 23:00:00', '2023-09-30 02:00:00', '2023-09-30 05:00:00',
    #                            '2023-09-30 08:00:00', '2023-09-30 11:00:00', '2023-09-30 14:00:00', '2023-09-30 17:00:00', '2023-09-30 20:00:00',
    #                            '2023-09-30 23:00:00', '2023-10-01 02:00:00', '2023-10-01 05:00:00', '2023-10-01 08:00:00', '2023-10-01 11:00:00', '2023-10-01 14:00:00'])
    minutes = int(tf[:-3]) # TODO: handle other than 'min'?
    fig.update_xaxes(rangebreaks=[dict(dvalue=minutes * 60 * 1000, values=dt_breaks)]) # dvalue in ms?

    return fig

#TODO: add with dates as strings and df: generate_daily_chart(df, '2023-01-01', '2023-12-31')
def daily_chart(df: pd.DataFrame, symbol: str, title:str, sip_marker: Optional[pd.Timestamp] = None):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol,
    )
    volume = go.Bar(x=df.index, y=df['Volume'], name='Volume', marker=dict(color='blue'))
    fig.add_trace(candlestick, row=1, col=1)    
    fig.add_trace(volume, row=2, col=1)
    
    annotations = []
    
    if sip_marker is not None:
        # remove hours/min from pd.datetime
        marker_day = pd.to_datetime(sip_marker.date())
        y_pos = df['Low'].min() + 1.5 * ((df['Close'][marker_day] - df['Low'].min()) / 2)          
        annotations.append(dict(x=marker_day, y=y_pos, text=f"SIP {sip_marker}", ay=100, showarrow=True, arrowhead=1, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)))    
    
    if annotations:
        fig.update_layout(annotations=annotations)
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=title)
    
    # Remove weekends from fig using rangebreaks
    dt_all = pd.date_range(start=df.index[0], end=df.index[-1], freq='1D')
    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in df.index]    
    fig.update_xaxes(rangebreaks=[dict(dvalue=1 * 24 * 60 * 60 * 1000, values=dt_breaks)])
    
    return fig


# TODO: plot indicators dict?
def intraday_chart(df: pd.DataFrame, tf: str, symbol: str, title: str, plot_indicators: Any = None, marker: Optional[Dict[str, Any]] = None, levels: Optional[Dict[str, Any]] = None):
    premarket_activity = df.index[0].time() < pd.Timestamp(f"{df.index[0].date()} 09:30").time()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])

    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol, # TODO: needed?
    )
    volume = go.Bar(x=df.index, y=df['Volume'], name='Volume', marker=dict(color='blue'))

    ta_lines = []
    if plot_indicators:
        for ta in plot_indicators.keys():
            line = go.Scatter(
                x=df.index,
                y=df[ta],
                name=ta,
                line=dict(color=plot_indicators[ta]['color']),
            )
            ta_lines.append(line)

    fig.add_trace(candlestick, row=1, col=1)
    for line in ta_lines:
        fig.add_trace(line, row=1, col=1)
    fig.add_trace(volume, row=2, col=1)

    shapes = []
    annotations = []
    
    if marker is not None:
        y_pos = marker.get('y_pos', df['Low'].min())
        x_pos = marker.get('x_pos', df.index[0])
        annotations.append(dict(x=x_pos, y=y_pos, text=marker['text'], ay=-10, showarrow=False, arrowhead=1, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)))    
    
    if premarket_activity:
        # TODO: RTH start/end markers y0 should bet LOD not low of chart and same for highs
        shapes.append(dict(x0=pd.Timestamp(f"{df.index[0].date()} 09:30"), x1=pd.Timestamp(f"{df.index[0].date()} 09:30"), y0=df['Low'].min(), y1=df['High'].max(), line_dash='dot', opacity=0.5))        
        if tf == '15min':
            shapes.append(dict(x0=pd.Timestamp(f"{df.index[0].date()} 15:45"), x1=pd.Timestamp(f"{df.index[0].date()} 15:45"), y0=df['Low'].min(), y1=df['High'].max(), line_dash='dot', opacity=0.5))  
    
    if levels is not None:        
        if levels['yday_mid']:
            # yesterday mid, assuming M15
            x_pos_yday_mid_0 = df.index[0]
            x_pos_yday_mid_1 = df.index[25]
            shapes.append(dict(x0=x_pos_yday_mid_0, x1=x_pos_yday_mid_1, y0=levels['yday_mid']['y_pos'], y1=levels['yday_mid']['y_pos'], line_dash='longdash', line_color='blue', opacity=0.3))
            annotations.append(dict(x=x_pos_yday_mid_0, y=levels['yday_mid']['y_pos'], xref='x', yref='y', showarrow=False, xanchor='left', text='yday_mid'))
        if levels['today_mid']:    
            x_pos_today_mid_0 = df.index[26]
            x_pos_today_mid_1 = df.index[52]            
            shapes.append(dict(x0=x_pos_today_mid_0, x1=x_pos_today_mid_1, y0=levels['today_mid'], y1=levels['today_mid'], line_dash='longdash', line_color='blue', opacity=0.3))
            annotations.append(dict(x=x_pos_today_mid_0, y=levels['today_mid'], xref='x', yref='y', showarrow=False, xanchor='left', text='today_mid'))
        if levels['close_1']:
            x_pos_close_0 = df.index[0]
            x_pos_close_1 = df.index[-1]
            shapes.append(dict(x0=x_pos_close_0, x1=x_pos_close_1, y0=levels['close_1'], y1=levels['close_1'], line_dash='dot', line_color='green', opacity=0.4))
            annotations.append(dict(x=x_pos_close_0, y=levels['close_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='close_1'))
        if levels['low_1']:
            x_pos_low_0 = df.index[0]
            x_pos_low_1 = df.index[-1]
            shapes.append(dict(x0=x_pos_low_0, x1=x_pos_low_1, y0=levels['low_1'], y1=levels['low_1'], line_dash='longdash', line_color='green', opacity=0.3))
            annotations.append(dict(x=x_pos_low_0, y=levels['low_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='low_1'))
        if levels['high_1']:
            x_pos_high_0 = df.index[0]
            x_pos_high_1 = df.index[-1]
            shapes.append(dict(x0=x_pos_high_0, x1=x_pos_high_1, y0=levels['high_1'], y1=levels['high_1'], line_dash='longdash', line_color='green', opacity=0.3))
            annotations.append(dict(x=x_pos_high_0, y=levels['high_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='high_1'))
        if levels['eth_high']:
            x_pos_eth_high_0 = df.index[0]
            x_pos_eth_high_1 = df.index[-1]
            shapes.append(dict(x0=x_pos_eth_high_0, x1=x_pos_eth_high_1, y0=levels['eth_high'], y1=levels['eth_high'], line_dash='longdash', line_color='blue', opacity=0.2))
            annotations.append(dict(x=x_pos_eth_high_0, y=levels['eth_high'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_high'))
        if levels['eth_low']:
            x_pos_eth_low_0 = df.index[0]
            x_pos_eth_low_1 = df.index[-1]
            shapes.append(dict(x0=x_pos_eth_low_0, x1=x_pos_eth_low_1, y0=levels['eth_low'], y1=levels['eth_low'], line_dash='longdash', line_color='blue', opacity=0.2))
            annotations.append(dict(x=x_pos_eth_low_0, y=levels['eth_low'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_low'))
    
    # TODO: add back again in better way if needed
    # if or_times:
    #     lowest, highest = utils_ta.or_levels(df, or_times)
    #     # TODO: a more simple way to select 10:30? e.g. bar 12?
    #     shapes.append(dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=lowest, y1=lowest, line_dash='dash', opacity=0.5))
    #     shapes.append(dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=highest, y1=highest, line_dash='dash', opacity=0.5))
    #     # fig.update_layout(shapes=[
    #     #     dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=lowest, y1=lowest, line_dash='dash', opacity=0.5),
    #     #     dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=highest, y1=highest, line_dash='dash', opacity=0.5)
    #     # ])

    if shapes:
        fig.update_layout(shapes=shapes)
    if annotations:
        fig.update_layout(annotations=annotations)
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=title)
    
    dt_all = pd.date_range(start=df.index[0], end=df.index[-1], freq=tf)
    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in df.index]
    if 'min' in tf:
        minutes = int(tf[:-3]) # TODO: handle other than 'min'?
    else:
        minutes = 24 * 60 
    fig.update_xaxes(rangebreaks=[dict(dvalue=minutes * 60 * 1000, values=dt_breaks)])
    
    return fig