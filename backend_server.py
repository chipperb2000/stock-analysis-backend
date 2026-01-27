"""
Stock Analysis Backend Server
Fetches real market data from Yahoo Finance and serves it via REST API
No CORS issues - runs locally on your machine
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def calculate_adx(df, period=14):
    """Calculate ADX indicator"""
    if len(df) < period * 2:
        return None
    
    high = df['High'].values
    low = df['Low'].values
    close = df['Close'].values
    
    plus_dm = []
    minus_dm = []
    tr = []
    
    for i in range(1, len(df)):
        high_diff = high[i] - high[i-1]
        low_diff = low[i-1] - low[i]
        
        plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
        minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
        
        true_range = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
        tr.append(true_range)
    
    smooth_plus_dm = sum(plus_dm[:period])
    smooth_minus_dm = sum(minus_dm[:period])
    smooth_tr = sum(tr[:period])
    
    for i in range(period, len(tr)):
        smooth_plus_dm = smooth_plus_dm - (smooth_plus_dm / period) + plus_dm[i]
        smooth_minus_dm = smooth_minus_dm - (smooth_minus_dm / period) + minus_dm[i]
        smooth_tr = smooth_tr - (smooth_tr / period) + tr[i]
    
    plus_di = (smooth_plus_dm / smooth_tr) * 100
    minus_di = (smooth_minus_dm / smooth_tr) * 100
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    
    return round(dx, 2)

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None
    
    multiplier = 2 / (period + 1)
    ema = np.mean(prices[:period])
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return round(ema, 2)

def calculate_variance(prices, period=504):
    """Calculate annualized volatility (variance)"""
    if len(prices) < 20:
        return None
    
    prices = prices[-min(period, len(prices)):]
    returns = np.diff(prices) / prices[:-1]
    
    variance = np.std(returns) * np.sqrt(252) * 100
    return round(variance, 2)

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    """Fetch stock data and calculate all indicators"""
    try:
        # Fetch 2 years of data
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty or len(df) < 200:
            return jsonify({'error': 'Insufficient data', 'ticker': ticker}), 404
        
        # Calculate indicators
        closes = df['Close'].values
        
        rsi = calculate_rsi(closes, 14)
        adx = calculate_adx(df, 14)
        variance = calculate_variance(closes, min(504, len(closes)))
        ema50 = calculate_ema(closes, 50)
        ema200 = calculate_ema(closes, 200)
        
        current_price = round(closes[-1], 2)
        volume = int(df['Volume'].values[-1])
        data_date = df.index[-1].strftime('%Y-%m-%d')
        
        ema_alignment = 'Bullish' if ema50 and ema200 and ema50 > ema200 else 'Bearish'
        
        result = {
            'ticker': ticker,
            'rsi': rsi,
            'adx': adx,
            'variance': variance,
            'ema50': ema50,
            'ema200': ema200,
            'emaAlignment': ema_alignment,
            'currentPrice': current_price,
            'volume': volume,
            'dataDate': data_date
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e), 'ticker': ticker}), 500

@app.route('/api/scan', methods=['POST'])
def scan_stocks():
    """Scan multiple stocks at once"""
    try:
        data = request.json
        tickers = data.get('tickers', [])
        
        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400
        
        results = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=730)
                
                df = stock.history(start=start_date, end=end_date)
                
                if df.empty or len(df) < 200:
                    continue
                
                closes = df['Close'].values
                
                rsi = calculate_rsi(closes, 14)
                adx = calculate_adx(df, 14)
                variance = calculate_variance(closes, min(504, len(closes)))
                ema50 = calculate_ema(closes, 50)
                ema200 = calculate_ema(closes, 200)
                
                current_price = round(closes[-1], 2)
                volume = int(df['Volume'].values[-1])
                data_date = df.index[-1].strftime('%Y-%m-%d')
                
                ema_alignment = 'Bullish' if ema50 and ema200 and ema50 > ema200 else 'Bearish'
                
                result = {
                    'ticker': ticker,
                    'rsi': rsi,
                    'adx': adx,
                    'variance': variance,
                    'ema50': ema50,
                    'ema200': ema200,
                    'emaAlignment': ema_alignment,
                    'currentPrice': current_price,
                    'volume': volume,
                    'dataDate': data_date
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"Error processing {ticker}: {str(e)}")
                continue
        
        return jsonify({'results': results, 'total': len(results)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Stock Analysis API is running'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("STOCK ANALYSIS BACKEND SERVER")
    print("=" * 60)
    print(f"Server starting on port {port}")
    print("\nAvailable endpoints:")
    print("  - GET  /api/health          - Check if server is running")
    print("  - GET  /api/stock/<ticker>  - Get data for single stock")
    print("  - POST /api/scan            - Scan multiple stocks")
    print("\nMake sure to install dependencies first:")
    print("  pip install flask flask-cors yfinance pandas numpy")
    print("=" * 60)
    
    # Use production settings if PORT env var exists (deployed)
    if 'PORT' in os.environ:
        app.run(host='0.0.0.0', port=port)
    else:
        # Local development
        app.run(debug=True, host='0.0.0.0', port=port)
