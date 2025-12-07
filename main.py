# main.py - FIXED FOR USD DISPLAY
import time
from datetime import datetime
from config import PRIMARY_TIMEFRAME, SCAN_DELAY_SECONDS, SCAN_INTERVAL_MINUTES
from data_loader import fetch_multi_timeframe_data, load_all_futures_symbols
from smc_logic import detect_smc_setup
import paper_trader 

def run_scanner_loop():
    print("\n" + "="*50)
    print("🤖 SMC AUTO-BOT STARTED (HYPERLIQUID + PAPER TRADING)")
    print("="*50)
    
    while True:
        try:
            # 1. Update Paper Trading Positions (Cek SL/TP)
            logs = paper_trader.update_positions()
            summary = paper_trader.get_portfolio_summary()
            
            if logs:
                print("\n🔔 UPDATE TRADING:")
                for log in logs: print(f"  {log}")
            
            # --- BAGIAN INI YANG DIPERBAIKI ---
            # Menampilkan Balance Real & PnL dalam USD
            balance = summary['balance']
            profit = summary['total_profit_usd']
            active = summary['active_trades']
            
            print(f"\n💼 PORTFOLIO: {active} Active | Balance: ${balance:,.2f} | Total PnL: ${profit:+,.2f}")
            # ----------------------------------
            
            # Jika slot trade penuh, skip scanning
            if active >= 3: 
                print("⚠️ Max posisi tercapai. Menunggu trade close...")
                wait_minutes(5)
                continue

            # 2. Mulai Scanning Market
            print(f"\n🔍 Scanning Market... ({datetime.now().strftime('%H:%M')})")
            symbols_to_scan = load_all_futures_symbols()
            
            for symbol in symbols_to_scan:
                data = fetch_multi_timeframe_data(symbol)
                if data is None: continue
                
                setup = detect_smc_setup(data, symbol) # Kirim symbol ke detector
                
                if setup:
                    print(f"✅ SETUP FOUND: {symbol} (Score: {setup['overall_score']})")
                    
                    # AUTO ENTRY ke Paper Trader
                    success, msg = paper_trader.open_position(setup)
                    if success:
                        print(f"🚀 EXECUTED: {msg}")
                    else:
                        print(f"⚠️ SKIP: {msg}")
                
                time.sleep(SCAN_DELAY_SECONDS)
            
            # 3. Istirahat sebelum scan berikutnya
            print(f"\n💤 Selesai scan. Tidur {SCAN_INTERVAL_MINUTES} menit...")
            wait_minutes(SCAN_INTERVAL_MINUTES)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot dihentikan manual.")
            break
        except Exception as e:
            print(f"\n❌ Error di main loop: {e}")
            wait_minutes(1)

def wait_minutes(minutes):
    """Fungsi sleep yang bisa di-interrupt dan tampilkan countdown"""
    try:
        total_seconds = minutes * 60
        for i in range(total_seconds, 0, -1):
            # Update posisi paper trade setiap 1 menit (60 detik) sambil nunggu
            # Agar SL/TP tetap terpantau meski sedang fase 'tidur'
            if i % 60 == 0 and i != total_seconds:
                 paper_trader.update_positions()
                 
            m, s = divmod(i, 60)
            print(f"\r⏳ Next scan in {m}m {s}s... ", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        raise

if __name__ == "__main__":
    run_scanner_loop()