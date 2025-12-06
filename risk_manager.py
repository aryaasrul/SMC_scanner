# risk_manager.py
from config import MAX_RISK_PERCENT, MIN_RR_RATIO, TARGET_LEVELS

def calculate_risk_reward(entry_price, stop_loss, swing_high, poi_high=None):
    """Calculate risk:reward profile."""
    if entry_price <= 0 or stop_loss <= 0:
        return None
    
    risk_amount = entry_price - stop_loss
    risk_percent = (risk_amount / entry_price) * 100
    
    if risk_percent > MAX_RISK_PERCENT:
        return {
            'valid': False,
            'reason': f'Risk too high: {risk_percent:.2f}% (max: {MAX_RISK_PERCENT}%)',
            'risk_percent': round(risk_percent, 2)
        }
    
    targets = {}
    
    for r in TARGET_LEVELS:
        target_price = entry_price + (risk_amount * r)
        targets[f'{r}R'] = {
            'price': round(target_price, 8),
            'profit_percent': round((target_price - entry_price) / entry_price * 100, 2),
            'rr_ratio': r
        }
    
    targets['SWING_HIGH'] = {
        'price': round(swing_high, 8),
        'profit_percent': round((swing_high - entry_price) / entry_price * 100, 2),
        'rr_ratio': round((swing_high - entry_price) / risk_amount, 2)
    }
    
    if poi_high:
        targets['POI_HIGH'] = {
            'price': round(poi_high, 8),
            'profit_percent': round((poi_high - entry_price) / entry_price * 100, 2),
            'rr_ratio': round((poi_high - entry_price) / risk_amount, 2)
        }
    
    realistic_targets = {k: v for k, v in targets.items() 
                        if v['price'] <= swing_high and v['rr_ratio'] >= MIN_RR_RATIO}
    
    if realistic_targets:
        best_target = max(realistic_targets.items(), key=lambda x: x[1]['price'])
    else:
        best_target = None
    
    return {
        'valid': True,
        'entry': round(entry_price, 8),
        'stop_loss': round(stop_loss, 8),
        'risk_amount': round(risk_amount, 8),
        'risk_percent': round(risk_percent, 2),
        'targets': targets,
        'best_target': best_target,
        'min_rr_met': any(t['rr_ratio'] >= MIN_RR_RATIO for t in targets.values())
    }

def validate_setup_risk(setup_data):
    """Validasi keseluruhan risk."""
    issues = []
    score = 100
    
    entry = setup_data.get('entry_price')
    sl = setup_data.get('stop_loss')
    swing_high = setup_data.get('swing_high')
    
    if not all([entry, sl, swing_high]):
        return {'valid': False, 'issues': ['Missing required price levels'], 'score': 0}
    
    risk_percent = ((entry - sl) / entry) * 100
    
    if risk_percent > MAX_RISK_PERCENT:
        issues.append(f'Risk too high: {risk_percent:.2f}% (max: {MAX_RISK_PERCENT}%)')
        score -= 40
    elif risk_percent < 0.5:
        issues.append('SL too tight (< 0.5%), might get stopped out easily')
        score -= 20
    
    potential_reward = swing_high - entry
    risk = entry - sl
    
    if risk > 0:
        rr_ratio = potential_reward / risk
        
        if rr_ratio < MIN_RR_RATIO:
            issues.append(f'RR ratio too low: {rr_ratio:.2f} (min: {MIN_RR_RATIO})')
            score -= 30
    else:
        issues.append('Invalid risk calculation (SL above entry)')
        score -= 50
    
    swing_low = setup_data.get('swing_low')
    if swing_low:
        sl_buffer_percent = ((swing_low - sl) / swing_low) * 100
        
        if sl_buffer_percent < 0.1:
            issues.append('SL too close to swing low (likely to get swept)')
            score -= 15
    
    return {
        'valid': len(issues) == 0 or score >= 50,
        'issues': issues,
        'score': max(score, 0),
        'risk_percent': round(risk_percent, 2),
        'rr_ratio': round(rr_ratio, 2) if risk > 0 else 0
    }