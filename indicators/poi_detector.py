# indicators/poi_detector.py
import pandas as pd
from config import MIN_OB_BODY_PERCENT, OB_PROXIMITY_PERCENT, FVG_MIN_SIZE_PERCENT, FVG_PROXIMITY_PERCENT

def identify_order_block(df, swing_low_idx, swing_high_idx):
    """Identifikasi Bullish Order Block."""
    if swing_low_idx not in df.index or swing_high_idx not in df.index:
        return None
    
    impulse_df = df.loc[swing_low_idx:swing_high_idx].copy()
    
    if len(impulse_df) < 3:
        return None
    
    bearish_candles = impulse_df[impulse_df['open'] > impulse_df['close']].copy()
    
    if bearish_candles.empty:
        return None
    
    bearish_candles['body_percent'] = (
        (bearish_candles['open'] - bearish_candles['close']) / 
        (bearish_candles['high'] - bearish_candles['low'])
    ) * 100
    
    valid_obs = bearish_candles[bearish_candles['body_percent'] >= MIN_OB_BODY_PERCENT]
    
    if valid_obs.empty:
        return None
    
    ob_candle = valid_obs.iloc[-1]
    
    avg_volume = df['volume'].iloc[-50:].mean()
    volume_ratio = ob_candle['volume'] / avg_volume
    
    body_percent = ((ob_candle['open'] - ob_candle['close']) / 
                    (ob_candle['high'] - ob_candle['low'])) * 100
    body_score = min(body_percent, 60)
    volume_score = min(volume_ratio * 20, 40)
    
    return {
        'type': 'ORDER_BLOCK',
        'low': ob_candle['low'],
        'high': ob_candle['high'],
        'index': ob_candle.name,
        'time': ob_candle['timestamp'],
        'body_percent': round(body_percent, 2),
        'volume_ratio': round(volume_ratio, 2),
        'strength': round(body_score + volume_score, 2)
    }

def detect_fair_value_gaps(df, swing_low_idx, swing_high_idx):
    """Deteksi Fair Value Gap."""
    if swing_low_idx not in df.index or swing_high_idx not in df.index:
        return []
    
    impulse_df = df.loc[swing_low_idx:swing_high_idx].copy()
    
    if len(impulse_df) < 5:
        return []
    
    fvgs = []
    
    for i in range(len(impulse_df) - 2):
        candle1 = impulse_df.iloc[i]
        candle2 = impulse_df.iloc[i+1]
        candle3 = impulse_df.iloc[i+2]
        
        if candle3['low'] > candle1['high']:
            gap_size = candle3['low'] - candle1['high']
            gap_percent = (gap_size / candle1['high']) * 100
            
            if gap_percent >= FVG_MIN_SIZE_PERCENT:
                fvg_low = candle1['high']
                fvg_high = candle3['low']
                
                df_after = df.loc[candle3.name:].iloc[1:]
                
                is_unfilled = True
                if not df_after.empty:
                    filled_candles = df_after[df_after['low'] <= fvg_high]
                    is_unfilled = filled_candles.empty
                
                gap_score = min(gap_percent * 20, 70)
                unfilled_score = 30 if is_unfilled else 0
                
                fvgs.append({
                    'type': 'FVG',
                    'low': fvg_low,
                    'high': fvg_high,
                    'index': candle2.name,
                    'time': candle2['timestamp'],
                    'gap_percent': round(gap_percent, 3),
                    'is_unfilled': is_unfilled,
                    'strength': round(gap_score + unfilled_score, 2)
                })
    
    unfilled_fvgs = [fvg for fvg in fvgs if fvg['is_unfilled']]
    return sorted(unfilled_fvgs, key=lambda x: x['strength'], reverse=True)

def find_best_poi(df, swing_low_idx, swing_high_idx, current_price):
    """Pilih POI terbaik."""
    ob = identify_order_block(df, swing_low_idx, swing_high_idx)
    fvgs = detect_fair_value_gaps(df, swing_low_idx, swing_high_idx)
    
    candidates = []
    
    if ob:
        ob_proximity = abs(current_price - ob['high']) / current_price * 100
        if ob_proximity <= OB_PROXIMITY_PERCENT:
            ob['proximity'] = ob_proximity
            candidates.append(ob)
    
    for fvg in fvgs:
        fvg_proximity = abs(current_price - fvg['low']) / current_price * 100
        if fvg_proximity <= FVG_PROXIMITY_PERCENT:
            fvg['proximity'] = fvg_proximity
            candidates.append(fvg)
    
    if not candidates:
        return None
    
    for poi in candidates:
        poi['score'] = poi['strength'] / (poi['proximity'] + 1)
    
    best_poi = max(candidates, key=lambda x: x['score'])
    
    return best_poi