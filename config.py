# config.py - Enhanced Configuration

# --- Pengaturan Exchange ---
EXCHANGE_ID = 'hyperliquid'
DEFAULT_TYPE = 'future'

# --- Pengaturan Trading ---
PRIMARY_TIMEFRAME = '5m'      # Timeframe untuk entry
HTF_TIMEFRAME = '1h'          # Higher Timeframe untuk konfirmasi bias
LTF_TIMEFRAME = '1m'         # Lower Timeframe untuk fine-tune entry

CANDLE_LIMIT = 200            # Jumlah candle untuk analisis

# --- Daftar Simbol ---
SYMBOL_LIST = None            # None = scan semua, atau ['BTC/USDT', 'ETH/USDT']
SYMBOL_SUFFIX_FILTER = 'USDC'

# --- API Keys ---
API_KEY = ''
SECRET_KEY = ''

# =======================================
# PENGATURAN STRATEGI SMC
# =======================================

# --- Structure Detection ---
MIN_SWING_CANDLES = 5        # Min candles untuk swing high/low
LOOKBACK_PERIOD = 50          # Berapa candle kebelakang untuk analisis

# --- POI/Order Block Settings ---
OB_PROXIMITY_PERCENT = 0.5    # Harga harus dalam 2% dari OB untuk valid
MIN_OB_BODY_PERCENT = 20      # OB harus punya body minimal 30% dari range

# --- Fair Value Gap (FVG) Settings ---
FVG_MIN_SIZE_PERCENT = 0.3    # FVG minimal 0.3% dari harga untuk valid
FVG_PROXIMITY_PERCENT = 0.5   # Harga dalam 1.5% dari FVG = valid

# --- Liquidity Sweep Settings ---
SWEEP_TOLERANCE_PERCENT = 0.1 # Sweep valid jika tembus 0.2% di bawah low
MIN_REJECTION_BODY = 30       # Rejection candle harus punya body 50%+

# --- Volume Analysis ---
VOLUME_SPIKE_MULTIPLIER = 1.2 # Volume 1.5x dari average = spike
POI_VOLUME_MULTIPLIER = 1.1   # POI harus punya volume 1.3x average

# --- Entry Confirmation ---
REQUIRE_ENGULFING = False      # Butuh bullish engulfing untuk entry?
REQUIRE_VOLUME_CONF = True    # Butuh volume confirmation?
REQUIRE_HTF_ALIGNMENT = True  # Butuh HTF bullish untuk entry?

# --- Risk Management ---
MAX_RISK_PERCENT = 2.0        # Max risk per trade (dari entry ke SL)
MIN_RR_RATIO = 2.0            # Min Risk:Reward ratio
TARGET_LEVELS = [1.5, 2, 3]  # R multiples untuk target

# --- Multi-Timeframe Filters ---
HTF_TREND_PERIOD = 20         # Period untuk deteksi HTF trend
MIN_HTF_HL_COUNT = 2          # Minimal 2 Higher Low untuk confirm uptrend

# --- Wave Structure (Simplified) ---
WAVE_DETECTION_ENABLED = False  # Advanced feature, set False dulu
MIN_WAVE_SIZE_PERCENT = 2.0     # Min size untuk wave yang valid

# --- Output Settings ---
SHOW_DETAILED_LOG = True      # Print detail setiap symbol
ALERT_ONLY_CONFIRMED = True   # Hanya alert setup yang sudah confirmed
MAX_RESULTS_DISPLAY = 20      # Max hasil yang ditampilkan

# --- Performance ---
SCAN_DELAY_SECONDS = 1.0      # Delay antar request (avoid rate limit)
ENABLE_CACHE = True           # Cache data untuk speed up

# --- Loop & Automation Setting ---
SCAN_INTERVAL_MINUTES = 5     # Bot akan scan tiap 60 menit
MAX_OPEN_POSITIONS = 3        # Max posisi terbuka bersamaan

# --- Paper Trading ---
INITIAL_CAPITAL = 1000        # Modal bohongan untuk paper trading
RISK_PER_TRADE = 1.0          # Risiko 1% per trade

# --- Pengaturan Trading ---
LEVERAGE = 10                 # Leverage untuk trading futures
MARGIN_MODE = 'isolated'      # 'isolated' atau 'cross'


# =======================================
# FILTER KUALITAS (ADVANCED)
# =======================================

FILTERS = {
    'require_fvg_or_ob': True,        # Setup harus punya FVG ATAU OB
    'require_liquidity_sweep': True,   # Harus ada sweep sebelum entry
    'require_discount_zone': False,     # Harga harus di discount (<50% range)
    'require_structure_intact': True,  # SL tidak boleh tertembus
    'min_candles_after_low': 2,       # Min 5 candles setelah swing low
}