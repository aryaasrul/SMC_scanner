# main.py
import time
from datetime import datetime
from config import PRIMARY_TIMEFRAME, HTF_TIMEFRAME, SCAN_DELAY_SECONDS, SHOW_DETAILED_LOG, MAX_RESULTS_DISPLAY
from data_loader import fetch_multi_timeframe_data, load_all_futures_symbols
from smc_logic import detect_smc_setup

def print_header():
    """Print scanner header."""
    print("\n" + "="*70)
    print("🚀 ENHANCED SMC MARKET SCANNER v2.0".center(70))
    print("="*70)
    print(f"📊 Primary TF: {PRIMARY_TIMEFRAME} | HTF: {HTF_TIMEFRAME}")
    print(f"⏰ Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

def print_setup_details(setup, index):
    """Print setup details."""
    print(f"\n{'='*70}")
    print(f"🎯 SETUP #{index}: {setup['symbol']}")
    print(f"{'='*70}")
    
    print(f"\n💰 PRICE LEVELS:")
    print(f"  Current Price: ${setup['current_price']:.6f}")
    print(f"  Entry Level:   ${setup['entry']:.6f}")
    print(f"  Stop Loss:     ${setup['stop_loss']:.6f}")
    print(f"  Swing High:    ${setup['swing_high']:.6f}")
    
    poi = setup['poi']
    print(f"\n📍 POINT OF INTEREST ({poi['type']}):")
    print(f"  Zone: ${poi['low']:.6f} - ${poi['high']:.6f}")
    print(f"  Strength: {poi['strength']}/100")
    print(f"  Distance: {poi['proximity']:.2f}%")
    
    struct = setup['structure']
    print(f"\n📈 MARKET STRUCTURE:")
    print(f"  Primary TF: {struct['trend']}")
    print(f"  HTF Trend:  {struct['htf_trend']}")
    print(f"  Zone: {struct['zone']} ({struct['zone_percent']:.1f}% of range)")
    
    liq = setup['liquidity']
    if liq['sweep_detected']:
        print(f"\n💧 LIQUIDITY SWEEP:")
        print(f"  Strength: {liq['sweep_strength']}/100")
        print(f"  Swept Level: ${liq['swept_level']:.6f}")
        if liq['stop_hunt']:
            print(f"  ⚠️  Stop Hunt Pattern Detected!")
    
    vol = setup['volume']
    print(f"\n📊 VOLUME ANALYSIS:")
    print(f"  Current Ratio: {vol['current_ratio']}x average")
    print(f"  Trend: {vol['trend']}")
    print(f"  Accumulation: {vol['accumulation']}")
    if vol['poi_volume']:
        print(f"  POI Volume: {vol['poi_volume']['strength']}/100 ({vol['poi_volume']['level']})")
    
    conf = setup['confirmation']
    print(f"\n✅ ENTRY CONFIRMATION:")
    print(f"  Confidence: {conf['confidence']}/100")
    print(f"  Pattern: {conf['pattern']}")
    print(f"  Signals: {', '.join(conf['signals'])}")
    
    rr = setup['risk_reward']
    print(f"\n⚖️  RISK / REWARD:")
    print(f"  Risk: {setup['risk_percent']:.2f}%")
    
    print(f"\n  📊 TARGET LEVELS:")
    for level in ['1R', '2R', '3R', '4R', '5R']:
        if level in rr['targets']:
            target = rr['targets'][level]
            print(f"    {level}: ${target['price']:.6f} (+{target['profit_percent']:.2f}%)")
    
    if rr['best_target']:
        best = rr['best_target']
        print(f"\n  🎯 Best Target: {best[0]} @ ${best[1]['price']:.6f} ({best[1]['rr_ratio']:.1f}R)")
    
    print(f"\n⭐ OVERALL QUALITY: {setup['setup_quality']} ({setup['overall_score']}/100)")
    print(f"\n{'='*70}\n")

def run_scanner():
    """Main scanner function."""
    
    print_header()
    
    symbols_to_scan = load_all_futures_symbols()
    
    if not symbols_to_scan:
        print("❌ No symbols to scan. Exiting...")
        return
    
    print(f"🔍 Scanning {len(symbols_to_scan)} pairs...\n")
    
    if SHOW_DETAILED_LOG:
        print("📋 Scanning Progress:")
    
    potential_setups = []
    processed = 0
    
    for symbol in symbols_to_scan:
        processed += 1
        
        if SHOW_DETAILED_LOG and processed % 10 == 0:
            print(f"  Progress: {processed}/{len(symbols_to_scan)} ({processed/len(symbols_to_scan)*100:.1f}%)")
        
        data = fetch_multi_timeframe_data(symbol)
        
        if data is None:
            continue
        
        setup = detect_smc_setup(data, symbol)
        
        if setup:
            potential_setups.append(setup)
            
            if SHOW_DETAILED_LOG:
                print(f"  ✅ {symbol}: Setup found (Score: {setup['overall_score']}/100)")
        
        time.sleep(SCAN_DELAY_SECONDS)
    
    print("\n" + "="*70)
    print("📋 SCAN COMPLETE - RESULTS SUMMARY".center(70))
    print("="*70)
    
    if not potential_setups:
        print("\n❌ No valid SMC setups found in current market conditions.")
        print("   Try again later or adjust filter settings in config.py\n")
        return
    
    potential_setups.sort(key=lambda x: x['overall_score'], reverse=True)
    
    print(f"\n✅ Found {len(potential_setups)} potential setups!")
    print(f"\nTop Setups (sorted by quality):\n")
    
    print(f"{'#':<4} {'Symbol':<15} {'Score':<8} {'Quality':<20} {'Risk':<8} {'Best Target':<12}")
    print("-" * 70)
    
    for idx, setup in enumerate(potential_setups[:MAX_RESULTS_DISPLAY], 1):
        best_target = setup['best_target'] if setup['best_target'] != 'N/A' else 'N/A'
        
        print(f"{idx:<4} {setup['symbol']:<15} {setup['overall_score']:<8} "
              f"{setup['setup_quality']:<20} {setup['risk_percent']:.2f}%    {best_target}")
    
    print("\n" + "="*70)
    print("📊 DETAILED SETUP REPORTS".center(70))
    print("="*70)
    
    num_details = min(5, len(potential_setups))
    
    print(f"\nShowing detailed reports for top {num_details} setups:\n")
    
    for idx, setup in enumerate(potential_setups[:num_details], 1):
        print_setup_details(setup, idx)
    
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS".center(70))
    print("="*70 + "\n")
    
    excellent = [s for s in potential_setups if s['overall_score'] >= 80]
    good = [s for s in potential_setups if 65 <= s['overall_score'] < 80]
    fair = [s for s in potential_setups if 50 <= s['overall_score'] < 65]
    
    if excellent:
        print(f"🌟 EXCELLENT SETUPS ({len(excellent)}):")
        for setup in excellent[:3]:
            print(f"  • {setup['symbol']} - Score: {setup['overall_score']} - "
                  f"Entry around ${setup['entry']:.6f}")
    
    if good:
        print(f"\n✅ GOOD SETUPS ({len(good)}):")
        for setup in good[:3]:
            print(f"  • {setup['symbol']} - Score: {setup['overall_score']} - "
                  f"Wait for confirmation")
    
    if fair:
        print(f"\n⚠️  FAIR SETUPS ({len(fair)}):")
        print(f"  Consider waiting for better confluence or confirmation")
    
    print("\n" + "="*70)
    print("\n💡 Next Steps:")
    print("1. Review detailed charts on TradingView")
    print("2. Confirm setups match your trading plan")
    print("3. Set alerts at key levels")
    print("4. Wait for final confirmation before entry")
    print("\n⚠️  Remember: This is analysis, not financial advice!")
    print("\n" + "="*70 + "\n")

def run_quick_scan(symbols=None):
    """Quick scan untuk specific symbols."""
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    print(f"\n🚀 Quick Scan: {', '.join(symbols)}\n")
    
    for symbol in symbols:
        data = fetch_multi_timeframe_data(symbol)
        if data:
            setup = detect_smc_setup(data, symbol)
            if setup:
                print(f"✅ {symbol}: Score {setup['overall_score']}/100")
                print(f"   Entry: ${setup['entry']:.6f} | SL: ${setup['stop_loss']:.6f}")
            else:
                print(f"⏭️  {symbol}: No setup found")
        else:
            print(f"❌ {symbol}: Failed to fetch data")
        
        time.sleep(0.5)

if __name__ == "__main__":
    run_scanner()