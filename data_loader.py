# data_loader.py - HYPERLIQUID SUPPORT
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from config import (
    EXCHANGE_ID, DEFAULT_TYPE,
    SYMBOL_SUFFIX_FILTER, CANDLE_LIMIT, ENABLE_CACHE
)

_cache = {}

def get_exchange_instance():
    # Hyperliquid tidak butuh API Key untuk public data
    exchange = getattr(ccxt, EXCHANGE_ID)({
        'options': {'defaultType': DEFAULT_TYPE},
        'enableRateLimit': True,
    })
    return exchange

def load_top_volume_symbols(limit=50):
    exchange = get_exchange_instance()
    try:
        print(f"📊 Mengambil Data Market dari {EXCHANGE_ID.upper()}...")
        tickers = exchange.fetch_tickers()
        candidates = []
        
        for symbol, data in tickers.items():
            # Hyperliquid symbols biasanya "BTC/USDC:USDC" atau "BTC/USDC"
            if SYMBOL_SUFFIX_FILTER not in symbol:
                continue
            
            vol_24h = data.get('quoteVolume', 0)
            if vol_24h is None: vol_24h = 0
            
            candidates.append({'symbol': symbol, 'volume_24h': vol_24h})
            
        sorted_candidates = sorted(candidates, key=lambda x: x['volume_24h'], reverse=True)
        final_symbols = [c['symbol'] for c in sorted_candidates[:limit]]
        
        print(f"✅ Screening {len(final_symbols)} koin teratas di Hyperliquid.")
        return final_symbols

    except Exception as e:
        print(f"❌ Error loading tickers: {e}")
        return []

def load_all_futures_symbols():
    return load_top_volume_symbols(limit=50)

def fetch_ohlcv(symbol, timeframe, limit):
    # (Kode fetch_ohlcv sama persis dengan sebelumnya, tidak perlu diubah)
    # Copy paste fungsi fetch_ohlcv dari file sebelumnya ke sini
    cache_key = f'{symbol}_{timeframe}_{limit}'
    if ENABLE_CACHE and cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if datetime.now() - cached_time < timedelta(minutes=1):
            return cached_data
    
    exchange = get_exchange_instance()
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit) 
        if ohlcv is None or len(ohlcv) < 30: return None
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if ENABLE_CACHE: _cache[cache_key] = (datetime.now(), df)
        return df
    except Exception as e:
        return None

def fetch_multi_timeframe_data(symbol):
    # (Sama seperti sebelumnya)
    from config import PRIMARY_TIMEFRAME, HTF_TIMEFRAME, LTF_TIMEFRAME
    data = {}
    data['htf'] = fetch_ohlcv(symbol, HTF_TIMEFRAME, CANDLE_LIMIT)
    data['primary'] = fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, CANDLE_LIMIT)
    data['ltf'] = fetch_ohlcv(symbol, LTF_TIMEFRAME, CANDLE_LIMIT)
    if data['primary'] is None: return None
    return data