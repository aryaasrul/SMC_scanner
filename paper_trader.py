# paper_trader.py
import json
import os
from datetime import datetime
import pandas as pd
from data_loader import fetch_ohlcv
from config import PRIMARY_TIMEFRAME, LEVERAGE, INITIAL_CAPITAL, RISK_PER_TRADE

DB_FILE = 'paper_trades.json'

def load_db():
    if not os.path.exists(DB_FILE):
        # Inisialisasi DB baru dengan balance awal
        return {'balance': INITIAL_CAPITAL, 'trades': [], 'history': []}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'balance': INITIAL_CAPITAL, 'trades': [], 'history': []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4, default=str)

def open_position(setup):
    db = load_db()
    
    # Filter hanya trade yang masih OPEN
    active_trades = [t for t in db['trades'] if t.get('status') == 'OPEN']
    
    # 1. Cek Slot Posisi
    if len(active_trades) >= 3: # Max 3 posisi
        return False, "Max slot posisi tercapai"

    # 2. Cek apakah koin ini sudah ada posisi aktif
    for trade in active_trades:
        if trade['symbol'] == setup['symbol']:
            return False, "Posisi sudah ada untuk koin ini"

    # --- PERHITUNGAN POSISI SIZE & MARGIN ---
    entry_price = setup['entry']
    stop_loss = setup['stop_loss']
    
    # Hitung Jarak SL dalam Persen (Absolute)
    sl_percent = abs(entry_price - stop_loss) / entry_price
    
    if sl_percent == 0: return False, "Error: SL Price sama dengan Entry"

    # Hitung Risiko per Trade dalam Dolar ($) berdasarkan Balance saat ini
    current_balance = db['balance']
    risk_amount_usd = current_balance * (RISK_PER_TRADE / 100)
    
    # Hitung Size Posisi (Total Value Coin)
    # Rumus: Risk $ / SL %
    position_size_usd = risk_amount_usd / sl_percent
    
    # Hitung Jumlah Koin
    quantity = position_size_usd / entry_price
    
    # Hitung Margin yang Dibutuhkan
    required_margin = position_size_usd / LEVERAGE
    
    # Cek Free Margin
    used_margin = sum(t.get('margin_used', 0) for t in active_trades)
    free_margin = current_balance - used_margin
    
    if required_margin > free_margin:
        return False, f"Margin kurang! Butuh ${required_margin:.2f}, Sisa ${free_margin:.2f}"

    # --- EKSEKUSI (SIMULASI) ---
    trade = {
        'id': int(datetime.now().timestamp()),
        'symbol': setup['symbol'],
        'entry_time': str(datetime.now()),
        'side': 'LONG',
        'leverage': LEVERAGE,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'tp1': setup['risk_reward']['targets']['2R']['price'],
        'tp2': setup['risk_reward']['targets']['3R']['price'],
        'quantity': quantity,
        'position_size_usd': position_size_usd,
        'margin_used': required_margin,
        'risk_usd': risk_amount_usd,
        'status': 'OPEN',
        'pnl': 0
    }
    
    db['trades'].append(trade)
    save_db(db)
    
    log_msg = (
        f"OPEN LONG {setup['symbol']} | Lev: {LEVERAGE}x | "
        f"Size: ${position_size_usd:.2f} | Margin: ${required_margin:.2f}"
    )
    return True, log_msg

def update_positions():
    """Cek posisi, update status, dan update BALANCE."""
    db = load_db()
    
    # Pastikan kita hanya memproses yang OPEN
    # (Menggunakan list comprehension baru agar aman saat remove item)
    active_trades = [t for t in db['trades'] if t['status'] == 'OPEN']
    
    if not active_trades:
        return []

    logs = []
    updated_trades_list = [] # List untuk menyimpan trade yang masih OPEN
    
    print("\n🔄 Memeriksa Posisi Paper Trading...")
    
    balance_changed = False
    
    for trade in active_trades:
        # Ambil harga terbaru
        df = fetch_ohlcv(trade['symbol'], PRIMARY_TIMEFRAME, 5)
        
        # Jika gagal fetch data, biarkan trade tetap OPEN tanpa perubahan
        if df is None:
            updated_trades_list.append(trade)
            continue
            
        # Data candle terakhir
        current_price = df['close'].iloc[-1]
        low_price = df['low'].iloc[-1]
        high_price = df['high'].iloc[-1]
        
        status = 'OPEN'
        pnl_R = 0
        close_reason = ''
        
        # --- CEK SL & TP ---
        # 1. Cek Stop Loss (Hit Low)
        if low_price <= trade['stop_loss']:
            status = 'CLOSED'
            close_reason = 'STOP LOSS 🔴'
            pnl_R = -1 # Loss 1R
            close_price = trade['stop_loss']
            
        # 2. Cek TP (Hit High)
        elif high_price >= trade['tp2']:
            status = 'CLOSED'
            close_reason = 'TAKE PROFIT (3R) 🟢'
            pnl_R = 3 # Profit 3R
            close_price = trade['tp2']
            
        # Jika status CLOSED, proses pemindahan ke history & update balance
        if status == 'CLOSED':
            trade['status'] = 'CLOSED'
            trade['close_time'] = str(datetime.now())
            trade['close_price'] = close_price
            trade['final_pnl_R'] = pnl_R
            
            # --- UPDATE BALANCE (PENTING!) ---
            # PnL dalam Dolar = PnL(R) * Risiko($)
            pnl_amount = pnl_R * trade['risk_usd']
            trade['pnl_amount'] = pnl_amount
            
            db['balance'] += pnl_amount  # Update saldo dompet
            balance_changed = True
            
            db['history'].append(trade) # Pindah ke history
            logs.append(f"{trade['symbol']}: {close_reason} | PnL: ${pnl_amount:.2f}")
            
        else:
            # Jika masih OPEN, update harga saat ini saja
            trade['current_price'] = current_price
            updated_trades_list.append(trade) # Masukkan kembali ke list OPEN
            
    # Simpan perubahan
    db['trades'] = updated_trades_list # Overwrite list trades dengan yang masih open
    save_db(db)
    
    if balance_changed:
        logs.append(f"💰 New Balance: ${db['balance']:.2f}")
        
    return logs

def get_portfolio_summary():
    db = load_db()
    # Hitung total profit dari history
    total_profit_usd = sum(t.get('pnl_amount', 0) for t in db['history'])
    
    return {
        'balance': db['balance'],
        'active_trades': len(db['trades']),
        'history_count': len(db['history']),
        'total_profit_usd': total_profit_usd
    }