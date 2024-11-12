import pandas as pd
import numpy as np

def identify_trend(data, short_window=5, long_window=20):
    """
    Identify the current market trend based on moving averages.
    
    :param data: A pandas DataFrame with a 'close' column.
    :param short_window: The window size for the short-term moving average.
    :param long_window: The window size for the long-term moving average.
    :return: A string indicating the trend ('Uptrend', 'Downtrend', or 'Sideways').
    """
    data['short_ma'] = data['close'].rolling(window=short_window).mean()
    data['long_ma'] = data['close'].rolling(window=long_window).mean()

    latest_short_ma = data['short_ma'].iloc[-1]
    latest_long_ma = data['long_ma'].iloc[-1]

    if pd.isna(latest_short_ma) or pd.isna(latest_long_ma):
        return 'Insufficient Data'

    if latest_short_ma > latest_long_ma:
        return 'Uptrend'
    elif latest_short_ma < latest_long_ma:
        return 'Downtrend'
    else:
        return 'Sideways'

def identify_break_of_structure(data):
    """
    Identify Break of Structure (BoS) in the given data.
    
    :param data: A pandas DataFrame with a 'close' column.
    :return: A list of indices where BoS is identified.
    """
    bos_indices = []
    # Ensure there are at least 3 data points to compare
    if len(data) < 3:
        return bos_indices

    for i in range(2, len(data)):
        # Previous trend
        prev_trend = identify_trend(data.iloc[i-2:i], short_window=5, long_window=20)
        current_trend = identify_trend(data.iloc[i-1:i+1], short_window=5, long_window=20)

        # Check for trend reversal
        if prev_trend == 'Uptrend' and current_trend == 'Downtrend':
            bos_indices.append(i)
        elif prev_trend == 'Downtrend' and current_trend == 'Uptrend':
            bos_indices.append(i)

    return bos_indices

def identify_trend_reversal(data):
    """
    Identify trend reversals with BoS confirmations.
    
    :param data: A pandas DataFrame with a 'close' column.
    :return: A list of dictionaries with reversal details.
    """
    reversals = []
    bos_indices = identify_break_of_structure(data)

    for idx in bos_indices:
        reversal_type = 'Bullish Reversal' if identify_trend(data.iloc[idx-1:idx+1]) == 'Uptrend' else 'Bearish Reversal'
        reversal_price = data['close'].iloc[idx]
        reversal_time = data['timestamp'].iloc[idx]

        reversals.append({
            'index': idx,
            'type': reversal_type,
            'price': reversal_price,
            'timestamp': reversal_time
        })

    return reversals

def calculate_moving_average(data, window_size):
    """
    Calculate moving average for the given window size.
    
    :param data: List or pandas Series of prices.
    :param window_size: The number of periods to calculate the moving average.
    :return: The moving average value.
    """
    if len(data) < window_size:
        return np.nan
    return np.mean(data[-window_size:])

def generate_trend_signals(data):
    """
    Generate trend signals based on moving averages and BoS.
    
    :param data: A pandas DataFrame with a 'close' column.
    :return: A dictionary with trend and reversal signals.
    """
    trend = identify_trend(data)
    reversals = identify_trend_reversal(data)

    return {
        'trend': trend,
        'reversals': reversals
    }
