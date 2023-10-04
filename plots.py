from functools import partial
import functools
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import utils_ta


def generate_trade_chart(trade, df, tf, title, plot_indicators, config):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])

    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=trade.symbol
    )
    volume = go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker=dict(color='blue')
    )
    
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
    
    fig.add_annotation(x=trade.start_dt, y=trade.entry_price, text=f"Entry ({trade.value:.0f})", showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14))
    fig.add_annotation(x=trade.end_dt, y=trade.exit_price, text=f"Exit ({trade.pnl:.1f})", showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14))
        
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=title)
    #fig.update_layout(xaxis_type='date', xaxis=dict(dtick=180*60*1000))
    dt_all = pd.date_range(start=df.index[0],end=df.index[-1], freq = tf)
    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist() if not d in df.index]
    #dt_breaks = pd.to_datetime(['2023-09-29 17:00:00', '2023-09-29 20:00:00', '2023-09-29 23:00:00', '2023-09-30 02:00:00', '2023-09-30 05:00:00', 
    #                            '2023-09-30 08:00:00', '2023-09-30 11:00:00', '2023-09-30 14:00:00', '2023-09-30 17:00:00', '2023-09-30 20:00:00',
    #                            '2023-09-30 23:00:00', '2023-10-01 02:00:00', '2023-10-01 05:00:00', '2023-10-01 08:00:00', '2023-10-01 11:00:00', '2023-10-01 14:00:00'])
    minutes = int(tf[:-3])
    fig.update_xaxes(rangebreaks=[dict(dvalue=minutes*60*1000, values=dt_breaks)] )


    
    return fig



def generate_chart(df, symbol, title, plot_indicators=None, or_times=None, daily_levels=None):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])

    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol,
    )
    volume = go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker=dict(color='blue')
    )
    
    ta_lines = []
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
    if or_times:
        lowest, highest = utils_ta.or_levels(df, or_times)
        # TODO: a more simple way to select 10:30? e.g. bar 12?
        shapes.append(dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=lowest, y1=lowest, line_dash='dash', opacity=0.5))
        shapes.append(dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=highest, y1=highest, line_dash='dash', opacity=0.5))
        # fig.update_layout(shapes=[
        #     dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=lowest, y1=lowest, line_dash='dash', opacity=0.5),
        #     dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} {or_times[1]}"), y0=highest, y1=highest, line_dash='dash', opacity=0.5)
        # ])

    shapes.append(dict(x0=df.index[0], x1=df.index[-1], y0=daily_levels['close_1'], y1=daily_levels['close_1'], line_dash='dot', line_color='green', opacity=0.4))
    shapes.append(dict(x0=df.index[0], x1=df.index[-1], y0=daily_levels['low_1'], y1=daily_levels['low_1'], line_dash='longdash', line_color='green', opacity=0.3))
    shapes.append(dict(x0=df.index[0], x1=df.index[-1], y0=daily_levels['high_1'], y1=daily_levels['high_1'], line_dash='longdash', line_color='green', opacity=0.3))
    shapes.append(dict(x0=df.index[0], x1=df.index[-1], y0=daily_levels['eth_high'], y1=daily_levels['eth_high'], line_dash='longdash', line_color='blue', opacity=0.2))
    shapes.append(dict(x0=df.index[0], x1=df.index[-1], y0=daily_levels['eth_low'], y1=daily_levels['eth_low'], line_dash='longdash', line_color='blue', opacity=0.2))
    annotations = [
        dict(x=df.index[0], y=daily_levels['close_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='yclose'),
        dict(x=df.index[0], y=daily_levels['high_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='yhigh'),
        dict(x=df.index[0], y=daily_levels['low_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='ylow'),
        dict(x=df.index[0], y=daily_levels['eth_high'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_high'),
        dict(x=df.index[0], y=daily_levels['eth_low'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_low'),
    ]

    fig.update_layout(shapes=shapes, annotations=annotations)
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=title)

    return fig
