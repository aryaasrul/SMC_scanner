# indicators/structure_detector.py
import pandas as pd
import numpy as np
from config import MIN_SWING_CANDLES, LOOKBACK_PERIOD

def find_swing_points(df, lookback=None):
    """Identifikasi Swing High dan Swing Low."""
    if lookback is None:
        lookback = LOOKBACK_PERIOD
    
    if len(df) < lookback:
        return None
    
    df_range = df.iloc[-lookback:].copy()
    
    swing_low_val = df_range['low'].min()
    swing_low_idx = df_range['low'].idxmin()
    
    df_after_low = df_range.loc[swing_low_idx:]
    
    if len(df_after_low) < MIN_SWING_CANDLES:
        return None
    
    swing_high_val = df_after_low['high'].max()
    swing_high_idx = df_after_low['high'].idxmax()
    
    if swing_high_idx <= swing_low_idx:
        return None
    
    return {
        'swing_low': {
            'value': swing_low_val,
            'index': swing_low_idx,
            'time': df.loc[swing_low_idx, 'timestamp']
        },
        'swing_high': {
            'value': swing_high_val,
            'index': swing_high_idx,
            'time': df.loc[swing_high_idx, 'timestamp']
        }
    }

def detect_market_structure(df):
    """Analisis struktur market: Uptrend, Downtrend, atau Range."""
    if len(df) < 30:
        return 'UNKNOWN'
    
    df_recent = df.iloc[-30:].copy()
    
    highs = df_recent['high'].values
    lows = df_recent['low'].values
    
    pivot_highs = []
    pivot_lows = []
    
    for i in range(5, len(df_recent)-5):
        if highs[i] == max(highs[i-5:i+6]):
            pivot_highs.append(highs[i])
        
        if lows[i] == min(lows[i-5:i+6]):
            pivot_lows.append(lows[i])
    
    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return 'RANGE'
    
    is_hh = pivot_highs[-1] > pivot_highs[-2]
    is_hl = pivot_lows[-1] > pivot_lows[-2]
    
    if is_hh and is_hl:
        return 'BULLISH'
    
    is_lh = pivot_highs[-1] < pivot_highs[-2]
    is_ll = pivot_lows[-1] < pivot_lows[-2]
    
    if is_lh and is_ll:
        return 'BEARISH'
    
    return 'RANGE'

def check_discount_premium_zone(current_price, swing_low, swing_high):
    """Menentukan zona discount/premium."""
    range_size = swing_high - swing_low
    
    if range_size == 0:
        return None
    
    price_in_range = current_price - swing_low
    percent_in_range = (price_in_range / range_size) * 100
    equilibrium = swing_low + (range_size * 0.5)
    
    if percent_in_range < 50:
        zone = 'DISCOUNT'
    elif percent_in_range > 50:
        zone = 'PREMIUM'
    else:
        zone = 'EQUILIBRIUM'
    
    return {
        'zone': zone,
        'percent': round(percent_in_range, 2),
        'equilibrium': equilibrium
    }

def calculate_structure_strength(df, swing_low_idx, swing_high_idx):
    """Hitung kekuatan struktur."""
    swing_low_val = df.loc[swing_low_idx, 'low']
    swing_high_val = df.loc[swing_high_idx, 'high']
    
    range_percent = ((swing_high_val - swing_low_val) / swing_low_val) * 100
    range_score = min(range_percent * 2, 40)
    
    num_candles = swing_high_idx - swing_low_idx
    momentum_score = max(30 - (num_candles * 0.5), 0)
    
    df_move = df.loc[swing_low_idx:swing_high_idx]
    num_up_candles = (df_move['close'] > df_move['open']).sum()
    clean_score = (num_up_candles / len(df_move)) * 30
    
    total_score = range_score + momentum_score + clean_score
    
    return round(min(total_score, 100), 2)