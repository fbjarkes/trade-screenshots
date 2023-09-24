import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import utils_ta

def generate_chart(df, symbol, filename, type='png', ta_params=None, or_levels=False, width=1280, height=800):
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
    
    if or_levels:
        lowest, highest = utils_ta.or_levels(df)
        # TODO: a more simple way to select 10:30? e.g. bar 12?
        fig.update_layout(shapes=[
            dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} 10:30"), y0=lowest, y1=lowest, line_dash='dash', opacity=0.3),
            dict(x0=df.index[0], x1=pd.Timestamp(f"{df.index[0].date()} 10:30"), y0=highest, y1=highest, line_dash='dash', opacity=0.3)
        ])
        
    # Make chart clean
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

    