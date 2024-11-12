import pandas as pd
import numpy as np

def calculate_moving_averages(data, short_window=5, long_window=20):
    """Calculate short and long moving averages."""
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()
    return data

def generate_signals(data, short_window=5, long_window=20):
    """Generate buy/sell signals based on moving average crossovers."""
    data['signal'] = 0
    data['signal'][short_window:] = np.where(data['short_ma'][short_window:] > data['long_ma'][short_window:], 1, 0)
    data['position'] = data['signal'].diff()
    return data
