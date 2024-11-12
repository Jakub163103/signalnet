import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

MODEL_PATH = 'models/trading_model.pkl'

def calculate_rsi(series, window=14):
    """
    Calculate Relative Strength Index (RSI).
    
    :param series: Pandas Series of prices.
    :param window: Window size for RSI calculation.
    :return: Pandas Series of RSI values.
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, span_short=12, span_long=26, span_signal=9):
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    :param series: Pandas Series of prices.
    :param span_short: Span for the short-term EMA.
    :param span_long: Span for the long-term EMA.
    :param span_signal: Span for the signal line EMA.
    :return: Pandas Series of MACD values.
    """
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=span_signal, adjust=False).mean()
    return macd - signal

def assign_signal(price_change, threshold=0.001):
    """
    Assign trading signal based on price change.
    
    :param price_change: Percentage change in price.
    :param threshold: Threshold to determine significant change.
    :return: 'Buy', 'Sell', or 'Hold'.
    """
    if price_change > threshold:
        return 'Buy'
    elif price_change < -threshold:
        return 'Sell'
    else:
        return 'Hold'

def preprocess_data(data):
    """
    Preprocess the raw price data and engineer features.
    
    :param data: Pandas DataFrame containing historical price data.
    :return: DataFrame with engineered features and target variable.
    """
    df = data.copy()
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Feature Engineering
    df['price_change'] = df['close'].pct_change()
    df['moving_avg_5'] = df['close'].rolling(window=5).mean()
    df['moving_avg_20'] = df['close'].rolling(window=20).mean()
    df['rsi_14'] = calculate_rsi(df['close'], window=14)
    df['macd'] = calculate_macd(df['close'])
    
    # Drop rows with NaN values
    df.dropna(inplace=True)
    
    # Define target variable: Buy, Sell, Hold
    df['signal'] = df['price_change'].apply(assign_signal)
    
    return df

def train_model(data):
    """
    Train the RandomForestClassifier model.
    
    :param data: Pandas DataFrame containing preprocessed data.
    :return: Trained RandomForestClassifier model.
    """
    df = preprocess_data(data)
    
    # Features and target
    X = df[['price_change', 'moving_avg_5', 'moving_avg_20', 'rsi_14', 'macd']]
    y = df['signal']
    
    # Encode target variable
    y_encoded = y.map({'Buy': 1, 'Sell': -1, 'Hold': 0})
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, shuffle=False
    )
    
    # Initialize and train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    print("Classification Report:\n", classification_report(y_test, y_pred))
    
    return model

def save_model(model):
    """
    Save the trained model to disk.
    
    :param model: Trained machine learning model.
    """
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

def load_model():
    """
    Load the trained model from disk.
    
    :return: Loaded machine learning model.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model file not found. Please train the model first.")
    model = joblib.load(MODEL_PATH)
    return model

def predict_signal(model, data):
    # Ensure the data has the correct feature names
    features = data[['price_change', 'moving_avg_5', 'moving_avg_20', 'rsi_14', 'macd']].values.reshape(1, -1)
    
    # Convert to DataFrame with the same columns as training data
    features_df = pd.DataFrame(features, columns=['price_change', 'moving_avg_5', 'moving_avg_20', 'rsi_14', 'macd'])
    
    prediction = model.predict(features_df)[0]
    
    # Map prediction back to label
    signal_map = {1: 'Buy', -1: 'Sell', 0: 'Hold'}
    return signal_map.get(prediction, 'Hold')

def fetch_historical_data(client, symbol='BTCUSDT', interval='1m', limit=1000):
    """
    Fetch historical kline data from Binance.
    
    :param client: Binance Client instance.
    :param symbol: Trading symbol.
    :param interval: Kline interval.
    :param limit: Number of data points.
    :return: Pandas DataFrame with historical data.
    """
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    data['close'] = data['close'].astype(float)
    return data

# Example usage:
if __name__ == "__main__":
    from binance.client import Client
    
    # Initialize Binance client with your API credentials
    binance_client = Client(api_key='your_api_key', api_secret='your_api_secret')
    
    # Fetch historical data
    historical_data = fetch_historical_data(binance_client, symbol='BTCUSDT', interval='1m', limit=1000)
    
    # Train the model
    trained_model = train_model(historical_data)
    
    # Save the model
    save_model(trained_model)
