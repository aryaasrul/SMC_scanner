# indicators/volume_analyzer.py
import pandas as pd
import numpy as np
from config import VOLUME_SPIKE_MULTIPLIER, POI_VOLUME_MULTIPLIER

def analyze_volume_profile(df, poi_low=None, poi_high=None):
    """Analisis volume profile."""
    if len(df) < 20:
        return None
    
    recent_df = df.iloc[-20:].copy()
    
    avg_volume = recent_df['volume'].mean()
    current_volume = df['volume'].iloc[-1]
    
    volumes = recent_df['volume'].values
    x = np.arange(len(volumes))
    slope = np.polyfit(x, volumes, 1)[0]
    
    volume_trend = 'INCREASING' if slope > 0 else 'DECREASING'
    
    volume_spikes = detect_volume_spikes(recent_df, avg_volume)
    
    poi_volume_strength = None
    if poi_low is not None and poi_high is not None:
        poi_volume_strength = check_poi_volume(df, poi_low, poi_high)
    
    divergence = detect_volume_divergence(recent_df)
    
    return {
        'avg_volume': round(avg_volume, 2),
        'current_volume': round(current_volume, 2),
        'volume_ratio': round(current_volume / avg_volume, 2),
        'trend': volume_trend,
        'slope': round(slope, 4),
        'spikes_count': len(volume_spikes),
        'recent_spikes': volume_spikes[-3:] if volume_spikes else [],
        'poi_volume_strength': poi_volume_strength,
        'has_divergence': divergence['has_divergence'],
        'divergence_type': divergence['type']
    }

def detect_volume_spikes(df, avg_volume):
    """Deteksi volume spike."""
    spikes = []
    
    for idx, row in df.iterrows():
        if row['volume'] > avg_volume * VOLUME_SPIKE_MULTIPLIER:
            spikes.append({
                'index': idx,
                'time': row['timestamp'],
                'volume': row['volume'],
                'ratio': round(row['volume'] / avg_volume, 2),
                'candle_type': 'BULLISH' if row['close'] > row['open'] else 'BEARISH'
            })
    
    return spikes

def check_poi_volume(df, poi_low, poi_high):
    """Check volume di POI."""
    poi_candles = df[
        (df['low'] >= poi_low * 0.99) & 
        (df['high'] <= poi_high * 1.01)
    ]
    
    if poi_candles.empty:
        return {
            'has_volume': False,
            'strength': 0,
            'ratio': 0
        }
    
    poi_total_volume = poi_candles['volume'].sum()
    avg_volume = df['volume'].iloc[-50:].mean()
    avg_candle_volume = poi_total_volume / len(poi_candles)
    
    volume_ratio = avg_candle_volume / avg_volume
    
    has_significant_volume = volume_ratio >= POI_VOLUME_MULTIPLIER
    
    strength = min(volume_ratio * 50, 100)
    
    return {
        'has_volume': has_significant_volume,
        'strength': round(strength, 2),
        'ratio': round(volume_ratio, 2),
        'candles_count': len(poi_candles),
        'level': 'STRONG' if volume_ratio >= 1.5 else 'MODERATE' if volume_ratio >= 1.2 else 'WEAK'
    }

def detect_volume_divergence(df):
    """Deteksi volume divergence."""
    if len(df) < 10:
        return {'has_divergence': False, 'type': 'NONE'}
    
    recent = df.iloc[-10:].copy()
    
    price_lows = recent.nsmallest(2, 'low')
    
    if len(price_lows) < 2:
        return {'has_divergence': False, 'type': 'NONE'}
    
    first_low = price_lows.iloc[0]
    second_low = price_lows.iloc[1]
    
    if second_low['low'] < first_low['low'] and second_low['volume'] > first_low['volume']:
        price_diff_percent = abs(second_low['low'] - first_low['low']) / first_low['low'] * 100
        volume_diff_percent = abs(second_low['volume'] - first_low['volume']) / first_low['volume'] * 100
        
        score = min((price_diff_percent + volume_diff_percent) * 5, 100)
        
        return {
            'has_divergence': True,
            'type': 'BULLISH',
            'strength': round(score, 2)
        }
    
    return {'has_divergence': False, 'type': 'NONE'}

def check_accumulation_distribution(df, lookback=20):
    """Simple A/D indicator."""
    if len(df) < lookback:
        return 'NEUTRAL'
    
    recent = df.iloc[-lookback:].copy()
    
    # Menghindari warning Division by Zero
    high_low_range = recent['high'] - recent['low']
    high_low_range = high_low_range.replace(0, 0.000001) # Safety check
    
    recent['mf_multiplier'] = (
        (recent['close'] - recent['low']) - (recent['high'] - recent['close'])
    ) / high_low_range
    
    # PERBAIKAN WARNING PANDAS DI SINI:
    recent['mf_multiplier'] = recent['mf_multiplier'].fillna(0)
    
    recent['mf_volume'] = recent['mf_multiplier'] * recent['volume']
    
    ad_line = recent['mf_volume'].cumsum()
    
    if ad_line.iloc[-1] > ad_line.iloc[0] * 1.1:
        return 'ACCUMULATION'
    elif ad_line.iloc[-1] < ad_line.iloc[0] * 0.9:
        return 'DISTRIBUTION'
    else:
        return 'NEUTRAL'