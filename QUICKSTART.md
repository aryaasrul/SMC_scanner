# 🚀 Quick Start - 5 Minutes Setup

## Step 1: Install Python & Dependencies

```bash
# Check Python (must be 3.8+)
python --version

# Install
pip install -r requirements.txt
```

## Step 2: Create Folder Structure

```bash
mkdir smc_scanner
cd smc_scanner
mkdir indicators
touch indicators/__init__.py  # IMPORTANT!
```

## Step 3: Copy All Files

Copy these 12 files ke folder:

**Core (6 files):**
1. config.py
2. data_loader.py
3. main.py
4. smc_logic.py
5. entry_confirmation.py
6. risk_manager.py

**Indicators (5 files):**
7. indicators/__init__.py
8. indicators/structure_detector.py
9. indicators/poi_detector.py
10. indicators/liquidity_detector.py
11. indicators/volume_analyzer.py

**Docs:**
12. requirements.txt

## Step 4: Test

```bash
python -c "import ccxt, pandas, numpy; print('✅ OK!')"
```

## Step 5: Run!

```bash
python main.py
```

---

## 🎯 Quick Config

### Conservative (Pemula)
```python
# config.py
PRIMARY_TIMEFRAME = '4h'
MAX_RISK_PERCENT = 2.0
MIN_RR_RATIO = 3.0
REQUIRE_ENGULFING = True
```

### Aggressive (Advanced)
```python
PRIMARY_TIMEFRAME = '1h'
MAX_RISK_PERCENT = 3.0
MIN_RR_RATIO = 2.0
REQUIRE_ENGULFING = False
```

---

## 🧪 Quick Test

Edit `main.py` bottom:
```python
if __name__ == "__main__":
    run_quick_scan(['BTC/USDT', 'ETH/USDT'])
```

---

## 🐛 Common Issues

### "No module 'indicators'"
**Fix**: Create `indicators/__init__.py`
```bash
touch indicators/__init__.py
```

### "No symbols found"
**Fix**: Check EXCHANGE_ID in config.py
```python
EXCHANGE_ID = 'mexc'  # lowercase!
```

### Rate limit error
**Fix**: Increase delay
```python
SCAN_DELAY_SECONDS = 0.5
```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed
- [ ] `indicators/__init__.py` created
- [ ] All 12 files copied
- [ ] Test run successful

**Ready to trade! 🚀**

Remember: Always verify on TradingView before entry!