# smc_logic.py - MAPPING EDITION
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'indicators'))

from indicators.structure_detector import find_swing_points, check_discount_premium_zone, calculate_structure_strength
from indicators.poi_detector import find_best_poi
from indicators.liquidity_detector import detect_liquidity_sweep
from config import FILTERS

def detect_smc_setup(data_dict, symbol=None):
    """
    Fungsi ini tidak lagi mencari 'Sinyal Entry', tapi melakukan 'Market Mapping'.
    Output: Peta struktur market (Trend, Range, POI, Lokasi Harga).
    """
    df = data_dict.get('primary')
    
    if df is None or len(df) < 50: return None
    
    # 1. Cari Struktur Swing (High & Low Terakhir)
    swing_points = find_swing_points(df)
    if swing_points is None: return None # Skip kalau market choppy/sideways parah
    
    swing_low = swing_points['swing_low']
    swing_high = swing_points['swing_high']
    current_price = df['close'].iloc[-1]
    
    # 2. Tentukan Bias Trend
    # Jika Swing Low baru terbentuk SETELAH Swing High -> Kita anggap dia mau naik (HL terbentuk)
    # Jika Swing High baru terbentuk SETELAH Swing Low -> Kita anggap dia mau turun (LH terbentuk)
    if swing_low['index'] > swing_high['index']:
        trend = 'BULLISH' # Struktur Higher High / Higher Low
        range_top = current_price # Asumsi temporary high
        range_bot = swing_low['value']
    else:
        trend = 'BEARISH' # Struktur Lower Low / Lower High
        range_top = swing_high['value']
        range_bot = current_price # Asumsi temporary low
        
    # Kalau strukturnya jelek (range terlalu sempit), skip
    if abs(range_top - range_bot) / range_bot < 0.005: # Range < 0.5%
        return None

    # 3. Cek Posisi Harga (Mapping)
    zone_info = check_discount_premium_zone(current_price, range_bot, range_top)
    
    # 4. Cari POI (Order Block)
    # Kita cari candle imbalance di area swing
    poi = find_best_poi(df, swing_low['index'], swing_high['index'], current_price)
    
    # 5. Cek Sweep (Hanya info, bukan syarat)
    sweep = detect_liquidity_sweep(df, range_bot if trend == 'BULLISH' else range_top)

    # 6. Susun Laporan (Mapping)
    # Status: Apa yang harus dilakukan user?
    status = "WAIT"
    action_msg = ""
    
    if trend == 'BULLISH':
        if zone_info['zone'] == 'PREMIUM':
            action_msg = "Harga di Pucuk (Premium). Tunggu koreksi."
        elif zone_info['zone'] == 'DISCOUNT':
            if poi and abs(current_price - poi['high'])/current_price < 0.01:
                status = "ALERT"
                action_msg = "🔥 Harga di Area POI! Cari Entry."
            else:
                action_msg = "Sudah Diskon. Tunggu masuk POI."
    
    # Return Data Mapping Lengkap
    return {
        'symbol': symbol,
        'trend': trend,
        'current_price': current_price,
        'range_low': range_bot,
        'range_high': range_top,
        'zone': zone_info['zone'], # Premium / Discount
        'poi_price': poi['high'] if poi else 0, # Area pantau
        'is_swept': sweep is not None,
        'status': status,
        'message': action_msg,
        'structure_score': calculate_structure_strength(df, swing_low['index'], swing_high['index'])
    }