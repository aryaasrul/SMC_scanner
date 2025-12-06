# data_loader.py - Enhanced with Multi-Timeframe & Caching
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from config import (
    EXCHANGE_ID, DEFAULT_TYPE, API_KEY, SECRET_KEY,
    SYMBOL_LIST, SYMBOL_SUFFIX_FILTER, CANDLE_LIMIT,
    PRIMARY_TIMEFRAME, HTF_TIMEFRAME, LTF_TIMEFRAME,
    ENABLE_CACHE
)

# Simple cache untuk menghindari re-fetch
_cache = {}
_cache_timeout = timedelta(minutes=5)

def get_exchange_instance():
    """Menginisialisasi koneksi exchange menggunakan ccxt."""
    exchange = getattr(ccxt, EXCHANGE_ID)({
        'options': {'defaultType': DEFAULT_TYPE},
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'enableRateLimit': True,
    })
    return exchange

def load_all_futures_symbols():
    """Mengambil daftar SEMUA pair futures dari exchange."""
    
    if SYMBOL_LIST is not None:
        print(f"📋 Menggunakan symbol list manual: {len(SYMBOL_LIST)} pairs")
        return SYMBOL_LIST
        
    cache_key = f'{EXCHANGE_ID}_futures_list'
    
    if ENABLE_CACHE and cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if datetime.now() - cached_time < _cache_timeout:
            print(f"📦 Menggunakan cached symbols: {len(cached_data)} pairs")
            return cached_data
    
    exchange = get_exchange_instance()
    try:
        print(f"🔄 Loading markets from {EXCHANGE_ID.upper()}...")
        markets = exchange.load_markets()
        futures_symbols = []
        
        for symbol, market in markets.items():
            is_futures_swap = market.get('swap') is True or market.get('future') is True 
            is_usdt_pair = symbol.endswith(SYMBOL_SUFFIX_FILTER)
            
            if market['active'] and is_futures_swap and is_usdt_pair: 
                futures_symbols.append(symbol)
        
        if len(futures_symbols) > 0:
            print(f"✅ Ditemukan {len(futures_symbols)} pair Futures {SYMBOL_SUFFIX_FILTER}")
            
            if ENABLE_CACHE:
                _cache[cache_key] = (datetime.now(), futures_symbols)
            
            return futures_symbols
        else:
            print("❌ GAGAL menemukan pair Futures yang valid.")
            return []

    except Exception as e:
        print(f"❌ ERROR: Gagal memuat markets. {str(e)}")
        return []

def fetch_ohlcv(symbol, timeframe, limit):
    """Fetch OHLCV data dengan caching."""
    
    cache_key = f'{symbol}_{timeframe}_{limit}'
    
    if ENABLE_CACHE and cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if datetime.now() - cached_time < timedelta(minutes=1):
            return cached_data
    
    exchange = get_exchange_instance()
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit) 
        
        if ohlcv is None or len(ohlcv) < 30:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if ENABLE_CACHE:
            _cache[cache_key] = (datetime.now(), df)
        
        return df
        
    except Exception as e:
        return None

def fetch_multi_timeframe_data(symbol):
    """
    Fetch data dari multiple timeframes sekaligus.
    Returns: dict dengan key 'htf', 'primary', 'ltf'
    """
    data = {}
    
    data['htf'] = fetch_ohlcv(symbol, HTF_TIMEFRAME, CANDLE_LIMIT)
    data['primary'] = fetch_ohlcv(symbol, PRIMARY_TIMEFRAME, CANDLE_LIMIT)
    data['ltf'] = fetch_ohlcv(symbol, LTF_TIMEFRAME, CANDLE_LIMIT)
    
    if data['primary'] is None:
        return None
        
    return data

def clear_cache():
    """Clear semua cache - useful untuk testing."""
    global _cache
    _cache = {}
    print("🗑️  Cache cleared")