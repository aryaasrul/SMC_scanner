# smc_logic.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'indicators'))

from indicators.structure_detector import find_swing_points, detect_market_structure, check_discount_premium_zone, calculate_structure_strength
from indicators.poi_detector import find_best_poi
from indicators.liquidity_detector import detect_liquidity_sweep, detect_stop_hunt
from indicators.volume_analyzer import analyze_volume_profile, check_accumulation_distribution
from entry_confirmation import confirm_entry_signal
from risk_manager import calculate_risk_reward, validate_setup_risk
from config import FILTERS, SHOW_DETAILED_LOG

def detect_smc_setup(data_dict, symbol=None):
    """Master detection function."""
    df = data_dict.get('primary')
    htf_df = data_dict.get('htf')
    
    if df is None or len(df) < 50:
        return None
    
    swing_points = find_swing_points(df)
    
    if swing_points is None:
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: No valid swing structure")
        return None
    
    swing_low = swing_points['swing_low']
    swing_high = swing_points['swing_high']
    current_price = df['close'].iloc[-1]
    structure = detect_market_structure(df)
    
    zone_info = check_discount_premium_zone(current_price, swing_low['value'], swing_high['value'])
    
    if zone_info is None:
        return None
    
    if FILTERS['require_discount_zone'] and zone_info['zone'] != 'DISCOUNT':
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: Not in discount zone ({zone_info['zone']})")
        return None
    
    poi = find_best_poi(df, swing_low['index'], swing_high['index'], current_price)
    
    if poi is None:
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: No valid POI found")
        return None
    
    sweep = detect_liquidity_sweep(df, swing_low['value'])
    
    if FILTERS['require_liquidity_sweep'] and sweep is None:
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: No liquidity sweep detected")
        return None
    
    has_stop_hunt = detect_stop_hunt(df, swing_low['value'])
    
    volume_analysis = analyze_volume_profile(df, poi['low'], poi['high'])
    accumulation_status = check_accumulation_distribution(df)
    
    htf_structure = None
    if htf_df is not None and len(htf_df) >= 30:
        htf_structure = detect_market_structure(htf_df)
    
    confirmation = confirm_entry_signal(df, poi, htf_structure)
    
    if not confirmation['is_confirmed']:
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: Entry not confirmed - {', '.join(confirmation['warnings'])}")
        return None
    
    rr_analysis = calculate_risk_reward(current_price, swing_low['value'], swing_high['value'], poi['high'])
    
    if rr_analysis is None or not rr_analysis['valid']:
        if SHOW_DETAILED_LOG and symbol:
            reason = rr_analysis.get('reason', 'Unknown') if rr_analysis else 'Invalid calculation'
            print(f"  ⏭️  {symbol}: Risk analysis failed - {reason}")
        return None
    
    setup_validation = validate_setup_risk({
        'entry_price': current_price,
        'stop_loss': swing_low['value'],
        'swing_high': swing_high['value'],
        'swing_low': swing_low['value']
    })
    
    if not setup_validation['valid']:
        if SHOW_DETAILED_LOG and symbol:
            print(f"  ⏭️  {symbol}: Setup validation failed - {', '.join(setup_validation['issues'])}")
        return None
    
    overall_score = calculate_setup_score(
        calculate_structure_strength(df, swing_low['index'], swing_high['index']),
        poi['strength'],
        sweep['strength'] if sweep else 0,
        volume_analysis['current_volume'] / volume_analysis['avg_volume'] * 20,
        confirmation['confidence'],
        min(rr_analysis['targets']['2R']['rr_ratio'] * 10, 30)
    )
    
    return {
        'signal': 'BULLISH_SMC_CONFIRMED',
        'symbol': symbol,
        'timestamp': df['timestamp'].iloc[-1],
        'current_price': round(current_price, 8),
        'entry': round(current_price, 8),
        'stop_loss': round(swing_low['value'], 8),
        'swing_low': round(swing_low['value'], 8),
        'swing_high': round(swing_high['value'], 8),
        'poi': {
            'type': poi['type'],
            'low': round(poi['low'], 8),
            'high': round(poi['high'], 8),
            'strength': poi['strength'],
            'proximity': poi.get('proximity', 0)
        },
        'structure': {
            'trend': structure,
            'htf_trend': htf_structure if htf_structure else 'N/A',
            'zone': zone_info['zone'],
            'zone_percent': zone_info['percent']
        },
        'liquidity': {
            'sweep_detected': sweep is not None,
            'sweep_strength': sweep['strength'] if sweep else 0,
            'stop_hunt': has_stop_hunt,
            'swept_level': round(sweep['swept_level'], 8) if sweep else None
        },
        'volume': {
            'current_ratio': volume_analysis['volume_ratio'],
            'trend': volume_analysis['trend'],
            'poi_volume': volume_analysis['poi_volume_strength'],
            'accumulation': accumulation_status
        },
        'confirmation': {
            'confidence': confirmation['confidence'],
            'signals': confirmation['signals'],
            'pattern': confirmation['details']['pattern']['pattern']
        },
        'risk_reward': rr_analysis,
        'risk_percent': rr_analysis['risk_percent'],
        'best_target': rr_analysis['best_target'][0] if rr_analysis['best_target'] else 'N/A',
        'best_target_price': rr_analysis['best_target'][1]['price'] if rr_analysis['best_target'] else 0,
        'overall_score': overall_score,
        'setup_quality': get_quality_rating(overall_score)
    }

def calculate_setup_score(structure_score, poi_strength, sweep_strength, volume_score, confirmation_confidence, rr_score):
    """Calculate overall setup score."""
    weights = {'structure': 0.15, 'poi': 0.20, 'sweep': 0.15, 'volume': 0.15, 'confirmation': 0.25, 'rr': 0.10}
    
    score = (
        structure_score * weights['structure'] +
        poi_strength * weights['poi'] +
        sweep_strength * weights['sweep'] +
        min(volume_score, 100) * weights['volume'] +
        confirmation_confidence * weights['confirmation'] +
        min(rr_score, 100) * weights['rr']
    )
    
    return round(score, 2)

def get_quality_rating(score):
    """Convert score to quality rating."""
    if score >= 80:
        return 'EXCELLENT ⭐⭐⭐'
    elif score >= 65:
        return 'GOOD ⭐⭐'
    elif score >= 50:
        return 'FAIR ⭐'
    else:
        return 'WEAK'