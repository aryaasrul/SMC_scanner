# entry_confirmation.py
import pandas as pd
from config import REQUIRE_ENGULFING, REQUIRE_VOLUME_CONF, REQUIRE_HTF_ALIGNMENT, VOLUME_SPIKE_MULTIPLIER

def confirm_entry_signal(df, poi, htf_structure=None):
    """Master confirmation function."""
    signals = []
    warnings = []
    confidence_score = 0
    
    pattern_result = check_price_action_pattern(df)
    if pattern_result['found']:
        signals.append(f"Price Action: {pattern_result['pattern']}")
        confidence_score += pattern_result['score']
    else:
        if REQUIRE_ENGULFING:
            warnings.append("No bullish pattern found")
    
    volume_result = check_volume_confirmation(df)
    if volume_result['confirmed']:
        signals.append(f"Volume Spike: {volume_result['ratio']}x")
        confidence_score += volume_result['score']
    else:
        if REQUIRE_VOLUME_CONF:
            warnings.append("No volume confirmation")
    
    htf_result = {'aligned': True, 'bias': 'N/A', 'score': 0}
    if htf_structure:
        htf_result = check_htf_alignment(htf_structure)
        if htf_result['aligned']:
            signals.append(f"HTF: {htf_result['bias']}")
            confidence_score += htf_result['score']
        else:
            if REQUIRE_HTF_ALIGNMENT:
                warnings.append(f"HTF not aligned: {htf_result['bias']}")
    
    momentum_result = check_momentum_shift(df)
    if momentum_result['positive']:
        signals.append(f"Momentum: {momentum_result['status']}")
        confidence_score += momentum_result['score']
    
    is_confirmed = True
    
    if REQUIRE_ENGULFING and not pattern_result['found']:
        is_confirmed = False
    
    if REQUIRE_VOLUME_CONF and not volume_result['confirmed']:
        is_confirmed = False
    
    if REQUIRE_HTF_ALIGNMENT and htf_structure and not htf_result['aligned']:
        is_confirmed = False
    
    return {
        'is_confirmed': is_confirmed,
        'confidence': round(confidence_score, 2),
        'signals': signals,
        'warnings': warnings,
        'details': {
            'pattern': pattern_result,
            'volume': volume_result,
            'htf': htf_result if htf_structure else None,
            'momentum': momentum_result
        }
    }

def check_price_action_pattern(df):
    """Deteksi candlestick patterns."""
    if len(df) < 2:
        return {'found': False, 'pattern': None, 'score': 0}
    
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]
    
    if check_bullish_engulfing(prev_candle, last_candle):
        return {'found': True, 'pattern': 'BULLISH_ENGULFING', 'score': 30}
    
    if check_hammer(last_candle):
        return {'found': True, 'pattern': 'HAMMER', 'score': 25}
    
    if check_bullish_marubozu(last_candle):
        return {'found': True, 'pattern': 'BULLISH_MARUBOZU', 'score': 20}
    
    if last_candle['close'] > last_candle['open']:
        return {'found': True, 'pattern': 'BULLISH_CANDLE', 'score': 10}
    
    return {'found': False, 'pattern': None, 'score': 0}

def check_bullish_engulfing(prev, current):
    """Check bullish engulfing."""
    prev_bearish = prev['close'] < prev['open']
    current_bullish = current['close'] > current['open']
    engulfs = current['open'] < prev['close'] and current['close'] > prev['open']
    return prev_bearish and current_bullish and engulfs

def check_hammer(candle):
    """Check hammer pattern."""
    body = abs(candle['close'] - candle['open'])
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    total_range = candle['high'] - candle['low']
    
    if total_range == 0:
        return False
    
    body_ratio = body / total_range
    lower_wick_ratio = lower_wick / total_range
    upper_wick_ratio = upper_wick / total_range
    
    return body_ratio < 0.3 and lower_wick_ratio > 0.6 and upper_wick_ratio < 0.2

def check_bullish_marubozu(candle):
    """Check bullish marubozu."""
    body = candle['close'] - candle['open']
    total_range = candle['high'] - candle['low']
    
    if total_range == 0 or body <= 0:
        return False
    
    body_ratio = body / total_range
    return body_ratio > 0.8

def check_volume_confirmation(df):
    """Check volume confirmation."""
    if len(df) < 20:
        return {'confirmed': False, 'ratio': 0, 'score': 0}
    
    avg_volume = df['volume'].iloc[-20:-1].mean()
    current_volume = df['volume'].iloc[-1]
    ratio = current_volume / avg_volume
    
    if ratio >= VOLUME_SPIKE_MULTIPLIER:
        return {'confirmed': True, 'ratio': round(ratio, 2), 'score': 25, 'level': 'STRONG'}
    elif ratio >= 1.2:
        return {'confirmed': True, 'ratio': round(ratio, 2), 'score': 15, 'level': 'MODERATE'}
    else:
        return {'confirmed': False, 'ratio': round(ratio, 2), 'score': 0, 'level': 'WEAK'}

def check_htf_alignment(htf_structure):
    """Check HTF alignment."""
    if htf_structure is None:
        return {'aligned': False, 'bias': 'UNKNOWN', 'score': 0}
    
    bias = htf_structure
    
    if bias == 'BULLISH':
        return {'aligned': True, 'bias': 'BULLISH', 'score': 25}
    elif bias == 'RANGE':
        return {'aligned': True, 'bias': 'RANGE', 'score': 15}
    else:
        return {'aligned': False, 'bias': 'BEARISH', 'score': 0}

def check_momentum_shift(df):
    """Check momentum shift."""
    if len(df) < 5:
        return {'positive': False, 'status': 'UNKNOWN', 'score': 0}
    
    last_5 = df.iloc[-5:].copy()
    closes = last_5['close'].values
    higher_closes = sum([closes[i] > closes[i-1] for i in range(1, len(closes))])
    bullish_count = (last_5['close'] > last_5['open']).sum()
    
    if higher_closes >= 3 and bullish_count >= 3:
        return {'positive': True, 'status': 'STRONG_MOMENTUM', 'score': 20, 'bullish_candles': int(bullish_count)}
    elif higher_closes >= 2 and bullish_count >= 2:
        return {'positive': True, 'status': 'BUILDING_MOMENTUM', 'score': 10, 'bullish_candles': int(bullish_count)}
    else:
        return {'positive': False, 'status': 'WEAK_MOMENTUM', 'score': 0, 'bullish_candles': int(bullish_count)}