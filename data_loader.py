# data_loader.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from config import (
    EXCHANGE_ID, DEFAULT_TYPE, API_KEY, SECRET_KEY,
    CANDLE_LIMIT, PRIMARY_TIMEFRAME, HTF_TIMEFRAME, LTF_TIMEFRAME,
    ENABLE_CACHE, ENABLE_WHALE_FILTER, TOP_VOLUME_COUNT, SKIP_TOP_MARKETCAP
)

_cache = {}
_cache_timeout = timedelta(minutes=5)

def get_exchange_instance():
    """Inisialisasi exchange."""
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    exchange = exchange_class({
        'options': {'defaultType': 'linear' if EXCHANGE_ID == 'bybit' else DEFAULT_TYPE},
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
    })
    return exchange

def get_whale_candidates():
    """
    Logika Screening ala 'Step 1':
    1. Ambil semua ticker.
    2. Urutkan berdasarkan Quote Volume (USDT) 24H.
    3. Hapus Top Cap (BTC, ETH, dll).
    4. Ambil Top 30 sisanya.
    """
    exchange = get_exchange_instance()
    print(f"🌊 Mengambil data Volume 24H dari {EXCHANGE_ID.upper()}...")
    
    try:
        # 1. Fetch Tickers (Sekali request dapat data volume semua koin)
        tickers = exchange.fetch_tickers()
        
        # Filter hanya pair USDT Futures
        valid_tickers = []
        for symbol, data in tickers.items():
            # Bybit format: BTC/USDT:USDT. Kita cari yang berakhiran USDT
            if '/USDT' in symbol and data['quoteVolume'] is not None:
                valid_tickers.append({
                    'symbol': symbol,
                    'volume_usdt': data['quoteVolume'], # Ini Volume dalam USDT (24h)
                    'close': data['close']
                })
        
        # 2. Sortir dari Volume Terbesar ke Terkecil
        valid_tickers.sort(key=lambda x: x['volume_usdt'], reverse=True)
        
        # 3. Filtering
        final_list = []
        skipped_count = 0
        
        print("\n📊 TOP VOLUME RANKING (Screening):")
        rank = 1
        
        for t in valid_tickers:
            sym_clean = t['symbol'].split(':')[0] # Bersihkan :USDT jika ada
            
            # Cek apakah masuk daftar skip (BTC, ETH, dll)
            if sym_clean in SKIP_TOP_MARKETCAP:
                skipped_count += 1
                continue
            
            # Format volume ke Juta/Miliar
            vol_display = f"${t['volume_usdt']/1_000_000:.1f}M"
            
            final_list.append(t['symbol'])
            print(f"  #{rank:<2} {sym_clean:<10} | Vol: {vol_display}")
            
            rank += 1
            if len(final_list) >= TOP_VOLUME_COUNT:
                break
                
        print(f"\n✅ Selesai! Mengambil {len(final_list)} koin (Skip {skipped_count} koin Top Cap).")
        return final_list

    except Exception as e:
        print(f"❌ Error fetching tickers: {e}")
        return []

def load_all_futures_symbols():
    """Wrapper: Pilih mau mode Whale atau Semua."""
    if ENABLE_WHALE_FILTER:
        return get_whale_candidates()
    
    # ... (Logika lama fetch all symbols jika needed, disederhanakan disini)
    exchange = get_exchange_instance()
    markets = exchange.load_markets()
    return [s for s in markets if '/USDT' in s and markets[s]['active']]

def fetch_ohlcv(symbol, timeframe, limit):
    """Fetch OHLCV standar."""
    cache_key = f'{symbol}_{timeframe}_{limit}'
    if ENABLE_CACHE and cache_key in _cache:
        t, d = _cache[cache_key]
        if datetime.now() - t < timedelta(minutes=1): return d
    
    exchange = get_exchange_instance()
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 30: return None
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if ENABLE_CACHE: _cache[cache_key] = (datetime.now(), df)
        return df
    except Exception as e:
        print(f"❌ Error {symbol}: {e}")
        return None

def fetch_multi_timeframe_data(symbol):
    """Fetch HTF, Primary, LTF."""
    data = {}
    data['primary'] = fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, CANDLE_LIMIT)
    if data['primary'] is None: return None
    
    data['htf'] = fetch_ohlcv(symbol, HTF_TIMEFRAME, CANDLE_LIMIT)
    # data['ltf'] = fetch_ohlcv(symbol, LTF_TIMEFRAME, CANDLE_LIMIT) # Optional, hemat request
    return data