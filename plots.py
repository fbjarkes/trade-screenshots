import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import utils_ta

def generate_chart(df, symbol, filename, type='png', ta_params=None, or_times=None, daily_levels=None, width=1280, height=800):
    candlestick = go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol,
    )
    
    ta_lines = []    
    for ta in ta_params.keys():
        line = go.Scatter(
            x=df.index,
            y=df[ta],
            name=ta,
            line=dict(color=ta_params[ta]['color']),
        )
        ta_lines.append(line)
    
    fig = go.Figure(data=[candlestick] + ta_lines)
    
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
    annotations=[
        dict(x=df.index[0], y=daily_levels['close_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='yclose'),
        dict(x=df.index[0], y=daily_levels['high_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='yhigh'),
        dict(x=df.index[0], y=daily_levels['low_1'], xref='x', yref='y', showarrow=False, xanchor='left', text='ylow'),
        ]

    fig.update_layout(shapes=shapes, annotations=annotations)
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_layout(title=filename)
       

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

    