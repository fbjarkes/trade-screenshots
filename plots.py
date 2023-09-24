import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots

def generate_chart(df, symbol, filename, type='png', ta_params=None, width=1280, height=800):
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

    # Make chart clean
    fig.update_layout(showlegend=False)
    fig.update_layout(xaxis_rangeslider_visible=False)

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

    