# main.py - MARKET MAPPER EDITION
import time
from datetime import datetime
from config import PRIMARY_TIMEFRAME, SCAN_DELAY_SECONDS, SCAN_INTERVAL_MINUTES
from data_loader import load_all_futures_symbols, fetch_multi_timeframe_data
from smc_logic import detect_smc_setup

def run_mapper():
    print("\n" + "="*80)
    print("🗺️  SMC MARKET MAPPER (Analyst Mode)".center(80))
    print("="*80)
    print(f"⏰ {datetime.now().strftime('%H:%M')} | TF: {PRIMARY_TIMEFRAME} | Exchange: BYBIT")
    
    # 1. Screening Awal (Whale Filter)
    symbols = load_all_futures_symbols() 
    if not symbols: return

    print(f"\n🔍 Mapping Struktur Market pada {len(symbols)} koin...\n")
    
    mapped_coins = []

    # 2. Mapping Loop
    for i, symbol in enumerate(symbols):
        try:
            clean_sym = symbol.split(':')[0]
            print(f"\rScanning {clean_sym:<10} ", end="", flush=True)
            
            data = fetch_multi_timeframe_data(symbol)
            if not data: continue

            # Panggil Logic Baru (Mapping)
            analysis = detect_smc_setup(data, symbol)
            
            if analysis:
                mapped_coins.append(analysis)
            
            time.sleep(SCAN_DELAY_SECONDS)
            
        except KeyboardInterrupt:
            raise
        except Exception:
            continue

    # 3. Tampilkan Dashboard Mapping
    print("\n\n" + "="*80)
    print(f"📊 HASIL MAPPING ({len(mapped_coins)} Koin Valid)".center(80))
    print("="*80)

    if not mapped_coins:
        print("Market lagi jelek (Choppy). Tidak ada struktur swing yang jelas.")
        return

    # Urutkan: Yang statusnya ALERT (Siap entry) taruh paling atas
    mapped_coins.sort(key=lambda x: (x['status'] != 'ALERT', x['structure_score']), reverse=False)

    # Header
    print(f"{'SYMBOL':<10} {'TREND':<8} {'PRICE':<10} {'ZONE':<10} {'POI AREA':<10} {'NOTES'}")
    print("-" * 80)

    for m in mapped_coins:
        sym = m['symbol'].split(':')[0]
        trend_icon = "📈" if m['trend'] == 'BULLISH' else "📉"
        
        # Warna teks (Logika sederhana via print formatting)
        status_icon = "⚡" if m['status'] == 'ALERT' else "⏳"
        
        print(f"{sym:<10} {trend_icon} {m['trend'][0:4]:<5} {m['current_price']:<10.4f} {m['zone']:<10} {m['poi_price']:<10.4f} {status_icon} {m['message']}")

    print("-" * 80)
    print("⚡ = Potensi Setup (Harga di Area Pantau)")
    print("⏳ = Waiting (Harga masih di Premium atau belum valid)")

if __name__ == "__main__":
    while True:
        try:
            run_mapper()
            print(f"\n💤 Refresh mapping dalam {SCAN_INTERVAL_MINUTES} menit...")
            time.sleep(SCAN_INTERVAL_MINUTES * 60)
        except KeyboardInterrupt:
            print("\n👋 Bye!")
            break