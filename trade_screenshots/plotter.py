from functools import partial
from typing import Any, Dict, List, Optional
import functools
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import trade_screenshots.utils_ta as utils_ta


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

class Plotter:
    """
    plot_config example:
    {'ta_config': 
        {'EMA200': {'color': 'blue'}},
        {'BB_UPPER': {'color': 'lightgrey'}},
        {'BB_LOWER': {'color': 'lightgrey'}}
    }
    """
    
    def __init__(self, plot_config: Optional[Dict[str, Any]] = None, init_ta=False):
        self.init_ta = init_ta    
        self.plot_config = plot_config if plot_config else {}
                    
    # TODO: sip_start_marker and levels dicts documentation?
    # sip_start_marker: {'text': <str>, 'x_pos': <pd.TimeStamp>, 'y_pos': <float>}
    # levels: {'yday_mid': <float>, 'today_mid': <float>, ...}
    def intraday_chart(self, df: pd.DataFrame, tf: str, symbol: str, title: str, 
                       sip_start_marker: Optional[Dict[str, Any]] = None, 
                       levels: Optional[Dict[str, Any]] = None,
                       ta_indicators: Optional[List[str]] = None): 
        add_rth_markers = df.index[0].time() < pd.Timestamp(f"{df.index[0].date()} 09:30").time()
    
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
        fig.add_trace(candlestick, row=1, col=1)
        fig.add_trace(volume, row=2, col=1)
        
        if ta_indicators:
            for ta in ta_indicators: 
                if ta in df.columns:
                    color = self.plot_config['ta_config'].get(ta, {}).get('color', 'black')
                    line = go.Scatter(
                        x=df.index,
                        y=df[ta],
                        name=ta,
                        line=dict(color=color),
                    )
                    fig.add_trace(line, row=1, col=1)
                else:
                    print(f"Indicator {ta} not found in df (columns={df.columns})")
        
        shapes = []
        annotations = []
        
        if sip_start_marker is not None:
            y_pos = sip_start_marker.get('y_pos', df['Low'].min())
            x_pos = sip_start_marker.get('x_pos', df.index[0])
            annotations.append(dict(x=x_pos, y=y_pos, text=sip_start_marker['text'], ay=-10, showarrow=False, arrowhead=1, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)))    
        
        if add_rth_markers:        
            #TODO: assuming M15
            a = f"{df.index[0].date()} 09:30"
            b = f"{df.index[0].date()} 15:45"
            y0 = df.loc[a:b]['Low'].min()
            y1 = df.loc[a:b]['High'].max()
            shapes.append(dict(x0=pd.Timestamp(a), x1=pd.Timestamp(a), y0=y0, y1=y1, line_dash='dot', opacity=0.5))        
            if tf == '15min':
                shapes.append(dict(x0=pd.Timestamp(b), x1=pd.Timestamp(b), y0=y0, y1=y1.max(), line_dash='dot', opacity=0.5))  
        
        if levels is not None:    
            #TODO: assuming M15 for intraday (e.g. 26 bars)        
            if 'yday_mid' in levels:
                # show mid during first day            
                x_pos_yday_mid_0 = df.index[0]
                x_pos_yday_mid_1 = df.index[25]
                shapes.append(dict(x0=x_pos_yday_mid_0, x1=x_pos_yday_mid_1, y0=levels['yday_mid'], y1=levels['yday_mid'], line_dash='longdash', line_color='blue', opacity=0.3))
                annotations.append(dict(x=x_pos_yday_mid_0, y=levels['yday_mid'], xref='x', yref='y', showarrow=False, xanchor='left', text='Yday Mid'))        
            if 'close_1' in levels:
                x_pos_close_0 = df.index[0]
                x_pos_close_1 = df.index[25]
                shapes.append(dict(x0=x_pos_close_0, x1=x_pos_close_1, y0=levels['close_1'], y1=levels['close_1'], line_dash='dot', line_color='green', opacity=0.4))
                annotations.append(dict(x=x_pos_close_0, y=levels['close_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='close_1'))
            if 'low_1' in levels:
                x_pos_low_0 = df.index[0]
                x_pos_low_1 = df.index[25]
                shapes.append(dict(x0=x_pos_low_0, x1=x_pos_low_1, y0=levels['low_1'], y1=levels['low_1'], line_dash='longdash', line_color='green', opacity=0.3))
                annotations.append(dict(x=x_pos_low_0, y=levels['low_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='low_1'))
            if 'high_1' in levels:
                x_pos_high_0 = df.index[0]
                x_pos_high_1 = df.index[25]
                shapes.append(dict(x0=x_pos_high_0, x1=x_pos_high_1, y0=levels['high_1'], y1=levels['high_1'], line_dash='longdash', line_color='green', opacity=0.3))
                annotations.append(dict(x=x_pos_high_0, y=levels['high_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='high_1'))
            if 'eth_high' in levels:
                x_pos_eth_high_0 = df.index[0]
                x_pos_eth_high_1 = df.index[25]
                shapes.append(dict(x0=x_pos_eth_high_0, x1=x_pos_eth_high_1, y0=levels['eth_high'], y1=levels['eth_high'], line_dash='longdash', line_color='blue', opacity=0.2))
                annotations.append(dict(x=x_pos_eth_high_0, y=levels['eth_high'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_high'))
            if 'eth_low' in levels:
                x_pos_eth_low_0 = df.index[0]
                x_pos_eth_low_1 = df.index[25]
                shapes.append(dict(x0=x_pos_eth_low_0, x1=x_pos_eth_low_1, y0=levels['eth_low'], y1=levels['eth_low'], line_dash='longdash', line_color='blue', opacity=0.2))
                annotations.append(dict(x=x_pos_eth_low_0, y=levels['eth_low'], xref='x', yref='y', showarrow=False, xanchor='left', text='eth_low'))
            if 'today_mid' in levels:    
                #x_pos_today_mid_0 = df.index[26]
                #x_pos_today_mid_1 = df.index[52]
                x_pos_today_mid_0 = f"{df.index[0].date()} 09:30"
                x_pos_today_mid_1 = f"{df.index[0].date()} 15:45"
                shapes.append(dict(x0=x_pos_today_mid_0, x1=x_pos_today_mid_1, y0=levels['today_mid'], y1=levels['today_mid'], line_dash='longdash', line_color='blue', opacity=0.2))
                annotations.append(dict(x=x_pos_today_mid_0, y=levels['today_mid'], xref='x', yref='y', showarrow=False, xanchor='left', text='Today Mid'))
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

    
    def trade_chart(self, trade, df, tf, title, plot_indicators):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])

        candlestick = go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=trade.symbol)
        volume = go.Bar(x=df.index, y=df['Volume'], name='Volume', marker=dict(color='blue'))

        ta_lines = []
        for ta in plot_indicators:
            line = go.Scatter(
                x=df.index,
                y=df[ta],
                name=ta,
                line=dict(color=self.plot_config['ta_config'].get(ta, {}).get('color', 'black')),
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

        entry_text = f"SHORT {trade.quantity}@{trade.entry_price} (val: {trade.value:.0f})" if trade.long_short is 'SHORT' else f"LONG {trade.quantity}@{trade.entry_price} ({trade.value:.0f})"
        exit_text = f"Exit {trade.quantity}@{trade.exit_price} (pnl: {trade.pnl:.1f})"
        #TODO: mark SL and target level?
        fig.add_annotation(
            x=trade.start_dt, y=trade.entry_price, text=entry_text, showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)
        )
        fig.add_annotation(
            x=trade.end_dt, y=trade.exit_price, text=exit_text, showarrow=True, arrowhead=1, ay=v_align, arrowwidth=1.5, arrowsize=1.5, font=dict(size=14)
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


    def daily_chart(self, df: pd.DataFrame, symbol: str, title:str,
                    from_date='', to_date='', 
                    sip_marker: Optional[pd.Timestamp] = None,
                    sip_text=''):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.8, 0.2])        
        if from_date and to_date:
            df = df[from_date:to_date]
        
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
            y_pos = df['Low'].min() + 1.0 * ((df['Close'][marker_day] - df['Low'].min()) / 2)
            txt = f"{sip_marker}:\n{sip_text}" if sip_text else f"SIP {sip_marker}"
            max_length = 50
            sentences = [txt[i:i+max_length] for i in range(0, len(txt), max_length)]
            formatted_text = '<br>'.join(sentences)
            font_size = 12
            annotations.append(dict(x=marker_day, y=y_pos, text=formatted_text, ay=100, showarrow=True, arrowhead=1, arrowwidth=1.5, arrowsize=1.5, font=dict(size=font_size)))
            
        
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



