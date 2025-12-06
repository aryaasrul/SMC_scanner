# indicators/liquidity_detector.py
import pandas as pd
from config import SWEEP_TOLERANCE_PERCENT, MIN_REJECTION_BODY, VOLUME_SPIKE_MULTIPLIER

def detect_liquidity_sweep(df, swing_low_val, lookback=20):
    """Deteksi liquidity sweep."""
    if len(df) < lookback + 5:
        return None
    
    recent_df = df.iloc[-(lookback + 5):].copy()
    
    equal_lows = find_equal_lows(recent_df)
    
    if not equal_lows:
        return None
    
    last_candles = df.iloc[-3:].copy()
    
    for _, candle in last_candles.iterrows():
        for eq_low in equal_lows:
            sweep_result = check_sweep_candle(
                candle, 
                eq_low['level'], 
                swing_low_val,
                df['volume'].iloc[-50:].mean()
            )
            
            if sweep_result:
                sweep_result['equal_low_touches'] = eq_low['touches']
                sweep_result['liquidity_level'] = eq_low['level']
                return sweep_result
    
    return None

def find_equal_lows(df, tolerance_percent=0.3):
    """Identifikasi equal lows."""
    if len(df) < 10:
        return []
    
    lows = df['low'].values
    equal_lows = []
    
    for i in range(len(lows)):
        level = lows[i]
        touches = [i]
        
        for j in range(len(lows)):
            if i != j:
                diff_percent = abs(lows[j] - level) / level * 100
                if diff_percent <= tolerance_percent:
                    touches.append(j)
        
        if len(touches) >= 2:
            equal_lows.append({
                'level': level,
                'touches': len(touches),
                'indices': touches
            })
    
    unique_levels = {}
    for el in equal_lows:
        level_key = round(el['level'], 6)
        if level_key not in unique_levels or el['touches'] > unique_levels[level_key]['touches']:
            unique_levels[level_key] = el
    
    result = list(unique_levels.values())
    return sorted(result, key=lambda x: x['touches'], reverse=True)

def check_sweep_candle(candle, equal_low_level, swing_low_val, avg_volume):
    """Cek apakah candle melakukan sweep."""
    tolerance = equal_low_level * (SWEEP_TOLERANCE_PERCENT / 100)
    
    is_swept = candle['low'] < (equal_low_level - tolerance)
    
    if not is_swept:
        return None
    
    is_rejection = candle['close'] > equal_low_level
    
    if not is_rejection:
        return None
    
    body_size = abs(candle['close'] - candle['open'])
    total_range = candle['high'] - candle['low']
    
    if total_range == 0:
        return None
    
    body_percent = (body_size / total_range) * 100
    has_strong_body = body_percent >= MIN_REJECTION_BODY
    
    volume_ratio = candle['volume'] / avg_volume
    has_volume_spike = volume_ratio >= VOLUME_SPIKE_MULTIPLIER
    
    sl_intact = candle['low'] > swing_low_val
    
    if not sl_intact:
        return None
    
    body_score = min(body_percent * 0.8, 40)
    volume_score = min(volume_ratio * 20, 40)
    binary_score = 0
    if has_strong_body:
        binary_score += 10
    if has_volume_spike:
        binary_score += 10
    
    strength = round(body_score + volume_score + binary_score, 2)
    
    return {
        'type': 'LIQUIDITY_SWEEP',
        'candle_index': candle.name,
        'time': candle['timestamp'],
        'swept_level': equal_low_level,
        'sweep_low': candle['low'],
        'rejection_close': candle['close'],
        'body_percent': round(body_percent, 2),
        'volume_ratio': round(volume_ratio, 2),
        'has_volume_spike': has_volume_spike,
        'strength': strength
    }

def detect_stop_hunt(df, swing_low_val):
    """Deteksi stop hunt pattern."""
    if len(df) < 5:
        return False
    
    last_5 = df.iloc[-5:].copy()
    
    for i in range(len(last_5) - 2):
        drop_candle = last_5.iloc[i]
        recovery_candle = last_5.iloc[i+1]
        
        drop_size = (drop_candle['open'] - drop_candle['close']) / drop_candle['open'] * 100
        recovery_size = (recovery_candle['close'] - recovery_candle['open']) / recovery_candle['open'] * 100
        
        if (drop_size > 1 and recovery_size > 1 and 
            drop_candle['low'] < swing_low_val * 1.005):
            
            avg_vol = df['volume'].iloc[-20:-2].mean()
            if recovery_candle['volume'] > avg_vol * 1.3:
                return True
    
    return False