from setuptools import setup, find_packages

setup(
    name='trade_screenshots',
    version='0.1.0',
    description='A library for generating screenshot like trade charts with custom data, e.g., with Tradingview or Alpaca data',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'plotly',
        'fire',
        'finta'
    ],
)