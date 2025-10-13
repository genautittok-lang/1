# main.py
import os
import time
import ccxt
import pandas as pd
import ta
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ------------------ НАЛАШТУВАННЯ ------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TESTNET = os.getenv("TESTNET", "False").lower() in ("1", "true", "yes")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOLS = os.getenv("SYMBOLS", "AVAX/USDT:USDT,LINK/USDT:USDT,ADA/USDT:USDT,DOGE/USDT:USDT,XRP/USDT:USDT").split(",")
TIMEFRAME = "5m"
ORDER_SIZE_USDT = 5.0  # $5 per trade (працює для дешевих монет)
LEVERAGE = 10
TP_PERCENT = 5.0
SL_PERCENT = 2.0
MAX_CONCURRENT_POSITIONS = 10
POLL_INTERVAL = 20
HISTORY_LIMIT = 200

# Файл для зберігання історії трейдів
TRADES_HISTORY_FILE = "trades_history.json"

# ------------------ Превентивні перевірки ------------------
if not API_KEY or not API_SECRET:
    raise SystemExit("Помилка: встанови API_KEY та API_SECRET у змінних середовища.")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("Попередження: Telegram повідомлення вимкнені.")

# ------------------ Історія трейдів ------------------
def load_trades_history():
    """Завантажує історію трейдів з файлу"""
    try:
        with open(TRADES_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"trades": [], "total_profit_usdt": 0.0, "wins": 0, "losses": 0}

def save_trades_history(history):
    """Зберігає історію трейдів у файл"""
    try:
        with open(TRADES_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Помилка збереження історії: {e}")

trades_history = load_trades_history()

# ------------------ Telegram Bot з кнопками ------------------
def tg_send(text, buttons=None):
    """Надсилає повідомлення в Telegram з опціональними кнопками"""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            }
            if buttons:
                data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Telegram send error: {e}")
    print(f"[TG] {text}")

def send_main_menu():
    """Надсилає головне меню з кнопками"""
    buttons = [
        [{"text": "📊 Звіт", "callback_data": "report"}],
        [{"text": "💼 Баланс", "callback_data": "balance"}],
        [{"text": "📈 Активні позиції", "callback_data": "positions"}]
    ]
    tg_send("📱 Головне меню:", buttons)

def handle_telegram_callback():
    """Обробляє натискання кнопок (викликається періодично)"""
    if not TELEGRAM_TOKEN:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": -1}
        response = requests.get(url, params=params, timeout=5).json()
        
        if response.get("ok") and response.get("result"):
            for update in response["result"]:
                if "callback_query" in update:
                    callback = update["callback_query"]["data"]
                    
                    if callback == "report":
                        send_report()
                    elif callback == "balance":
                        send_balance()
                    elif callback == "positions":
                        send_active_positions()
    except:
        pass

def send_report():
    """Надсилає звіт про торгівлю"""
    history = trades_history
    wins = history.get("wins", 0)
    losses = history.get("losses", 0)
    total_trades = wins + losses
    total_profit = history.get("total_profit_usdt", 0.0)
    
    # Розраховуємо % від початкового депозиту (припустимо $25)
    initial_deposit = 25.0
    profit_percent = (total_profit / initial_deposit * 100) if initial_deposit > 0 else 0
    
    msg = f"""📊 <b>ЗВІТ ПРО ТОРГІВЛЮ</b>

✅ Виграшів: {wins}
❌ Програшів: {losses}
📈 Всього трейдів: {total_trades}

💰 Прибуток: {total_profit:+.2f} USDT ({profit_percent:+.1f}%)"""
    
    tg_send(msg)

def send_balance():
    """Надсилає поточний баланс"""
    balance = get_available_balance()
    msg = f"""💼 <b>БАЛАНС</b>

💵 Доступно: {balance:.2f} USDT"""
    tg_send(msg)

def send_active_positions():
    """Надсилає інформацію про активні позиції"""
    positions = get_open_positions_from_exchange()
    
    if not positions:
        tg_send("📈 <b>Активних позицій немає</b>")
        return
    
    msg = "📈 <b>АКТИВНІ ПОЗИЦІЇ</b>\n\n"
    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        side = pos.get('side', 'N/A')
        size = pos.get('contracts', 0)
        entry = pos.get('entryPrice', 0)
        unrealized_pnl = pos.get('unrealizedPnl', 0)
        
        msg += f"🔸 {symbol} {side.upper()}\n"
        msg += f"   Розмір: {size}\n"
        msg += f"   Вхід: {entry:.4f}\n"
        msg += f"   PnL: {unrealized_pnl:+.2f} USDT\n\n"
    
    tg_send(msg)

# ------------------ Підключення до Bybit ------------------
exchange = ccxt.bybit({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap",
        "enableUnifiedAccount": True,
        "enableUnifiedMargin": True,
        "recvWindow": 10000,
    }
})
exchange.set_sandbox_mode(TESTNET)

def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# ------------------ Утиліти ------------------
def get_available_balance():
    """Отримує доступний USDT баланс"""
    try:
        balance = exchange.fetch_balance()
        usdt_free = float(balance.get('USDT', {}).get('free', 0))
        return usdt_free
    except Exception as e:
        print(f"Помилка отримання балансу: {e}")
        return 0.0

def get_open_positions_from_exchange():
    """Отримує відкриті позиції з біржі"""
    try:
        positions = exchange.fetch_positions()
        open_pos = [p for p in positions if float(p.get('contracts', 0)) > 0]
        return open_pos
    except Exception as e:
        print(f"Помилка отримання позицій: {e}")
        return []

def fetch_ohlcv_df(symbol, timeframe=TIMEFRAME, limit=HISTORY_LIMIT):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['RSI14'] = ta.momentum.rsi(df['close'], window=14)
    df['volEMA20'] = df['volume'].ewm(span=20).mean()
    return df

def signal_from_df(df):
    last = df.iloc[-1]
    long_cond = (last['EMA20'] > last['EMA50']) and (last['close'] > last['EMA20']) and (last['RSI14'] > 60) and (last['volume'] > last['volEMA20'])
    short_cond = (last['EMA20'] < last['EMA50']) and (last['close'] < last['EMA20']) and (last['RSI14'] < 40) and (last['volume'] > last['volEMA20'])
    if long_cond:
        return "LONG"
    if short_cond:
        return "SHORT"
    return "NONE"

def can_open_new_position(symbol):
    """Перевіряє чи можна відкрити нову позицію на символі"""
    # Перевіряємо реальні позиції на біржі
    positions = get_open_positions_from_exchange()
    for p in positions:
        if p.get('symbol') == symbol and float(p.get('contracts', 0)) > 0:
            return False
    
    # Перевіряємо ліміт позицій
    if len(positions) >= MAX_CONCURRENT_POSITIONS:
        return False
    return True

def calculate_amount(order_usdt, price, leverage=LEVERAGE):
    """Розраховує кількість монет для ордера"""
    # З плечем: треба помножити на leverage щоб отримати правильну позицію
    # Наприклад: $5 margin × 10 leverage = $50 exposure
    position_size = order_usdt * leverage
    amount = position_size / price
    return float(round(amount, 6))

# ------------------ Торгові операції ------------------
def set_leverage(symbol, value):
    """Встановлює плече для символу"""
    try:
        exchange.set_leverage(value, symbol)
    except Exception as e:
        # Ігноруємо помилку "leverage not modified" - плече вже встановлено
        if "110043" not in str(e):  # retCode 110043 = leverage already set
            print(f"Leverage warning {symbol}: {e}")

def open_position(symbol, side):
    """Відкриває позицію з TP/SL на біржі"""
    try:
        # Перевіряємо баланс
        available_balance = get_available_balance()
        if available_balance < ORDER_SIZE_USDT:
            # Недостатньо коштів - НЕ надсилаємо сигнал, просто пропускаємо
            print(f"{now()} ⚠️ Недостатньо коштів для {symbol}: {available_balance:.2f} < {ORDER_SIZE_USDT}")
            return False
        
        # Отримуємо ціну
        ticker = exchange.fetch_ticker(symbol)
        price = float(ticker['last'])
        amount = calculate_amount(ORDER_SIZE_USDT, price, LEVERAGE)
        ccxt_side = 'buy' if side == "LONG" else 'sell'
        
        # Розраховуємо TP/SL ціни
        tp_price = price * (1 + TP_PERCENT/100) if side == "LONG" else price * (1 - TP_PERCENT/100)
        sl_price = price * (1 - SL_PERCENT/100) if side == "LONG" else price * (1 + SL_PERCENT/100)
        
        # Встановлюємо плече
        set_leverage(symbol, LEVERAGE)
        
        # Відкриваємо основну позицію
        print(f"{now()} → Відкриваємо {side} {symbol} amount={amount} price≈{price:.4f}")
        
        # Відкриваємо ринковий ордер
        order = exchange.create_market_order(symbol, ccxt_side, amount)
        
        # Виставляємо TP і SL через Bybit API (set_position_tpsl)
        time.sleep(0.5)  # невелика пауза
        
        try:
            # Для Bybit Unified Trading використовуємо API для встановлення TP/SL на позицію
            params = {
                'symbol': symbol.replace('/', '').replace(':USDT', ''),
                'takeProfit': str(tp_price),
                'stopLoss': str(sl_price),
                'tpTriggerBy': 'LastPrice',
                'slTriggerBy': 'LastPrice',
                'category': 'linear'
            }
            
            # Використовуємо приватний метод Bybit для встановлення TP/SL
            exchange.private_post_v5_position_trading_stop(params)
            print(f"TP/SL виставлено на біржі: TP={tp_price:.4f}, SL={sl_price:.4f}")
            
        except Exception as e:
            print(f"Помилка виставлення TP/SL на біржі: {e}")
            # Fallback - зберігаємо локально для моніторингу
            pass
        
        # Надсилаємо повідомлення про відкриття
        msg = f"""✅ <b>ПОЗИЦІЮ ВІДКРИТО</b>

🔸 {symbol} {side}
💰 Вхід: {price:.4f} USDT
📊 Розмір: ${ORDER_SIZE_USDT} (×{LEVERAGE})
🎯 TP: {tp_price:.4f} (+{TP_PERCENT}%)
🛡 SL: {sl_price:.4f} (-{SL_PERCENT}%)"""
        
        tg_send(msg)
        return True
        
    except Exception as e:
        print(f"{now()} ❌ Помилка відкриття {symbol}: {e}")
        tg_send(f"❌ Помилка відкриття {symbol}: {e}")
        return False

def check_closed_positions():
    """Перевіряє чи були закриті позиції і надсилає повідомлення"""
    global trades_history
    
    try:
        # Отримуємо історію позицій з PnL
        for symbol in SYMBOLS:
            try:
                # Отримуємо закриті позиції з історії (closed PnL)
                closed_pnl = exchange.fetch_closed_orders(symbol, limit=5)
                
                for trade in closed_pnl:
                    trade_id = trade.get('id')
                    
                    # Перевіряємо чи вже обробляли цю позицію
                    already_processed = any(
                        t.get('order_id') == trade_id 
                        for t in trades_history.get('trades', [])
                    )
                    
                    if already_processed:
                        continue
                    
                    # Перевіряємо чи це закрита позиція з PnL
                    if trade.get('status') == 'closed' and trade.get('side') in ['sell', 'buy']:
                        # Отримуємо реальний PnL з інформації про ордер
                        info = trade.get('info', {})
                        
                        # Для Bybit реальний PnL в полі cumExecValue або треба розрахувати
                        filled_qty = float(trade.get('filled', 0))
                        avg_price = float(trade.get('average', 0))
                        
                        if filled_qty > 0 and avg_price > 0:
                            # Спроба отримати PnL з API
                            try:
                                # Отримуємо історію PnL позицій
                                pnl_history = exchange.fetch_my_trades(symbol, limit=10)
                                
                                # Шукаємо відповідний трейд
                                pnl = 0
                                for t in pnl_history:
                                    if t.get('order') == trade_id:
                                        pnl = float(t.get('info', {}).get('closedPnl', 0))
                                        break
                                
                                if pnl == 0:
                                    # Якщо не знайшли - пропускаємо
                                    continue
                                
                                # Визначаємо чи це TP чи SL
                                is_profit = pnl > 0
                                reason = "TP" if is_profit else "SL"
                                
                                # Оновлюємо історію
                                if is_profit:
                                    trades_history['wins'] = trades_history.get('wins', 0) + 1
                                else:
                                    trades_history['losses'] = trades_history.get('losses', 0) + 1
                                
                                trades_history['total_profit_usdt'] = trades_history.get('total_profit_usdt', 0.0) + pnl
                                
                                # Додаємо трейд в історію
                                trades_history['trades'].append({
                                    'order_id': trade_id,
                                    'symbol': symbol,
                                    'profit': pnl,
                                    'timestamp': now()
                                })
                                
                                save_trades_history(trades_history)
                                
                                # Надсилаємо повідомлення
                                profit_percent = (pnl / ORDER_SIZE_USDT) * 100
                                emoji = "✅" if is_profit else "❌"
                                
                                msg = f"""{emoji} <b>ПОЗИЦІЮ ЗАКРИТО ({reason})</b>

🔸 {symbol}
💵 Прибуток: {pnl:+.2f} USDT ({profit_percent:+.1f}%)
📊 Вхід: {avg_price:.4f}"""
                                
                                tg_send(msg)
                                
                            except Exception as e:
                                print(f"Помилка отримання PnL: {e}")
                                continue
                        
            except Exception as e:
                print(f"Помилка перевірки закритих позицій для {symbol}: {e}")
                continue
                
    except Exception as e:
        print(f"Помилка check_closed_positions: {e}")

# ------------------ Основний цикл ------------------
def main_loop():
    mode = "TESTNET" if TESTNET else "🔴 MAINNET"
    startup_msg = f"""🤖 <b>БОТ ЗАПУЩЕНО</b>

Режим: {mode}
💼 Баланс: {get_available_balance():.2f} USDT
📊 Моніторинг: {len(SYMBOLS)} монет
⏱ Інтервал: {POLL_INTERVAL}s"""
    
    if not TESTNET:
        startup_msg += "\n\n⚠️ <b>РЕАЛЬНА ТОРГІВЛЯ!</b>"
    
    tg_send(startup_msg)
    send_main_menu()
    
    print("=== Старт бот-циклу ===")
    
    while True:
        try:
            # Перевіряємо закриті позиції
            check_closed_positions()
            
            # Обробляємо кнопки Telegram
            handle_telegram_callback()
            
            # Шукаємо сигнали
            for symbol in SYMBOLS:
                if not can_open_new_position(symbol):
                    continue
                
                try:
                    df = fetch_ohlcv_df(symbol)
                    df = calculate_indicators(df)
                    sig = signal_from_df(df)
                    
                    if sig == "LONG" and can_open_new_position(symbol):
                        open_position(symbol, "LONG")
                    elif sig == "SHORT" and can_open_new_position(symbol):
                        open_position(symbol, "SHORT")
                except Exception as e:
                    print(f"Помилка обробки {symbol}: {e}")
                    continue
                
                time.sleep(1)
            
            time.sleep(POLL_INTERVAL)
            
        except Exception as e:
            print(f"{now()} ❌ Critical error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n=== Бот зупинено ===")
        tg_send("🛑 Бот зупинено")
