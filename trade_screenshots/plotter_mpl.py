import logging
import os
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from trade_screenshots.plotter import TA_PARAMS

logger = logging.getLogger(__name__)


class MplPlotter:
    """
    mplfinance/matplotlib based alternative to the plotly Plotter.
    Renders PNGs natively (no kaleido/browser needed) and is noticeably faster for batch generation.
    Same intraday_chart/daily_chart interface as Plotter, save() writes the figure to <filename>.png.
    """

    def __init__(self, plot_config: Optional[Dict[str, Any]] = None, style: str = 'yahoo'):
        self.style = style
        self.ta_config = {**TA_PARAMS}
        if plot_config:
            self.ta_config.update(plot_config.get('ta_config', {}))

    def _make_fig(self, df: pd.DataFrame, symbol: str, title: str, ta_indicators: Optional[List[str]] = None, show_nontrading=False):
        addplots = []
        for ta in ta_indicators or []:
            if ta in df.columns:
                color = self.ta_config.get(ta, {}).get('color', 'black')
                addplots.append(mpf.make_addplot(df[ta], color=color, width=1.0))
            else:
                print(f"Indicator {ta} not found in df (columns={df.columns})")

        fig, axes = mpf.plot(
            df,
            type='candle',
            style=self.style,
            volume=True,
            addplot=addplots,
            title=title,
            returnfig=True,
            figsize=(16, 9),
            panel_ratios=(4, 1),
            xrotation=0,
            datetime_format='%Y-%m-%d %H:%M' if getattr(df.index, 'freqstr', None) or df.attrs.get('timeframe', '') != 'day' else '%Y-%m-%d',
            show_nontrading=show_nontrading,
            warn_too_much_data=len(df) + 1,
        )
        return fig, axes

    def intraday_chart(self, df: pd.DataFrame, tf: str, symbol: str, title: str,
                       sip_start_marker: Optional[Dict[str, Any]] = None,
                       levels: Optional[Dict[str, Any]] = None,
                       ta_indicators: Optional[List[str]] = None):
        fig, axes = self._make_fig(df, symbol, title, ta_indicators)
        ax = axes[0]

        if sip_start_marker is not None:
            x_pos = sip_start_marker.get('x_pos', df.index[0])
            y_pos = sip_start_marker.get('y_pos', df['Low'].min())
            # mplfinance plots against bar number, not datetime, unless show_nontrading is used
            x_idx = df.index.get_indexer([pd.Timestamp(x_pos)], method='nearest')[0]
            ax.annotate(sip_start_marker['text'], xy=(x_idx, y_pos), xytext=(x_idx, y_pos * 0.98),
                        fontsize=11, ha='left', arrowprops=dict(arrowstyle='->', lw=1.2))

        if levels:
            for name, y in levels.items():
                ax.axhline(y=y, linestyle='--', linewidth=0.8, alpha=0.4)
                ax.annotate(name, xy=(0, y), fontsize=8, ha='left', va='bottom')

        return fig

    def daily_chart(self, df: pd.DataFrame, symbol: str, title: str,
                    from_date='', to_date='',
                    sip_date: Optional[pd.Timestamp] = None,
                    sip_text=''):
        if from_date and to_date:
            df = df[from_date:to_date]

        fig, axes = self._make_fig(df, symbol, title)
        ax = axes[0]

        if sip_date is not None:
            sip_date_str = f"{sip_date}"[:10]
            x_idx = df.index.get_indexer([pd.Timestamp(sip_date_str)], method='nearest')[0]
            ax.axvline(x=x_idx, linestyle=':', linewidth=1.0, alpha=0.6, color='purple')
            txt = f"{sip_date_str}: {sip_text}" if sip_text else f"SIP {sip_date_str}"
            ax.annotate(txt, xy=(x_idx, df['Low'].min()), fontsize=11, ha='center', va='bottom', color='purple')

        return fig

    def save(self, fig, filename: str, width: int = 1600, height: int = 900, verbose=0) -> str:
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        dpi = 100
        fig.set_size_inches(width / dpi, height / dpi)
        fig.savefig(f"{filename}.png", dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        if verbose > 0:
            print(f"Wrote '{filename}.png'")
        return f"{filename}.png"
