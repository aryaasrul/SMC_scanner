# 🚀 Enhanced SMC Market Scanner v2.0

Scanner crypto otomatis dengan **Smart Money Concepts (SMC)** lengkap!

## ✅ Fitur Lengkap

1. **Market Structure Detection** - Swing points, HH/HL, BOS
2. **POI Detection** - Order Blocks + Fair Value Gaps
3. **Liquidity Sweep** - Equal lows, sweep & rejection
4. **Volume Analysis** - Profile, spikes, A/D, divergence
5. **Entry Confirmation** - Pattern, volume, HTF, momentum
6. **Risk Management** - R:R, targets, position sizing
7. **Multi-Timeframe** - HTF + Primary + LTF analysis
8. **Quality Scoring** - 0-100 score untuk setiap setup

## 📁 File Structure

```
smc_scanner/
├── config.py                    # Konfigurasi utama
├── data_loader.py               # Data fetching
├── main.py                      # Program utama
├── smc_logic.py                 # Core detection
├── entry_confirmation.py        # Entry validation
├── risk_manager.py              # Risk calculator
└── indicators/
    ├── __init__.py              # Package init
    ├── structure_detector.py    # Structure
    ├── poi_detector.py          # POI & FVG
    ├── liquidity_detector.py    # Sweep
    └── volume_analyzer.py       # Volume
```

## 🔧 Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create indicators folder
mkdir indicators
touch indicators/__init__.py

# 3. Copy all files

# 4. Run!
python main.py
```

## ⚙️ Configuration

Edit `config.py`:

```python
# Timeframes
PRIMARY_TIMEFRAME = '1h'    # Entry TF
HTF_TIMEFRAME = '4h'        # Trend confirmation

# Risk Management
MAX_RISK_PERCENT = 3.0      # Max 3% risk
MIN_RR_RATIO = 2.0          # Min 1:2 RR

# Filters
REQUIRE_ENGULFING = True
REQUIRE_VOLUME_CONF = True
REQUIRE_HTF_ALIGNMENT = True
```

## 🚀 Usage

### Full Scan
```bash
python main.py
```

### Quick Test
Edit main.py:
```python
run_quick_scan(['BTC/USDT', 'ETH/USDT'])
```

## 📊 Output Example

```
🎯 SETUP #1: BTC/USDT
======================================
💰 PRICE LEVELS:
  Current: $42,150.50
  Entry: $42,150.50
  SL: $41,250.00
  
📍 POI (ORDER_BLOCK):
  Zone: $41,800 - $42,200
  Strength: 78/100
  
⭐ QUALITY: EXCELLENT ⭐⭐⭐ (87/100)
```

## 🎯 Score Interpretation

- **80-100**: EXCELLENT ⭐⭐⭐ - Strong BUY
- **65-79**: GOOD ⭐⭐ - Wait confirmation
- **50-64**: FAIR ⭐ - Use smaller size
- **<50**: WEAK - Skip

## ⚠️ Disclaimer

Tool ini untuk **ANALISIS**, bukan robot trading otomatis. Selalu lakukan verifikasi manual!

## 📞 Support

Jika ada issue, check:
1. Python 3.8+
2. All dependencies installed
3. `indicators/__init__.py` exists
4. No import errors

Happy Trading! 🚀