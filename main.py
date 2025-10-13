# main.py
import os
import time
import ccxt
import pandas as pd
import ta
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ------------------ НАЛАШТУВАННЯ (міняй у env або тут) ------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TESTNET = os.getenv("TESTNET", "False").lower() in ("1", "true", "yes")  # За замовчуванням MAINNET!
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SYMBOLS = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT,LINK/USDT,ADA/USDT").split(",")
TIMEFRAME = "5m"
ORDER_SIZE_USDT = 5.0
LEVERAGE = 10
TP_PERCENT = 5.0
SL_PERCENT = 2.0
MAX_CONCURRENT_POSITIONS = 10
POLL_INTERVAL = 20         # основний цикл пауза в секундах
HISTORY_LIMIT = 200        # скільки барів тягнути
MIN_BALANCE_USDT = 10.0    # мінімальний баланс для торгівлі

# ------------------ Превентивні перевірки ------------------
if not API_KEY or not API_SECRET:
    raise SystemExit("Помилка: встанови API_KEY та API_SECRET у змінних середовища.")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("Попередження: Telegram повідомлення вимкнені (TELEGRAM_TOKEN або TELEGRAM_CHAT_ID не встановлені).")

# ------------------ Підключення до Telegram через HTTP API ------------------
def tg_send(text):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text
            }
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Telegram send error: {e}")
    # також друкуємо локально
    print(f"[TG] {text}")

# ------------------ Підключення до Bybit через ccxt ------------------
exchange = ccxt.bybit({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap",           # Для Unified Trading Account
        "enableUnifiedAccount": True,    # Вмикаємо Unified Account mode
        "enableUnifiedMargin": True,     # Unified margin
        "recvWindow": 10000,             # Збільшуємо час для запитів
    }
})
exchange.set_sandbox_mode(TESTNET)

def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# ------------------ Локальний облік позицій ------------------
# Кожен елемент: {symbol, side('buy'/'sell'), entry_price, amount, tp, sl, opened_at}
open_positions = []

# ------------------ Утиліти для роботи з біржею ------------------
def get_available_balance():
    """Отримує доступний USDT баланс для торгівлі"""
    try:
        balance = exchange.fetch_balance()
        usdt_free = float(balance.get('USDT', {}).get('free', 0))
        return usdt_free
    except Exception as e:
        print(f"Помилка отримання балансу: {e}")
        return 0.0


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
    # не відкривати позицію на тій же монеті одночасно
    for p in open_positions:
        if p['symbol'] == symbol:
            return False
    if len(open_positions) >= MAX_CONCURRENT_POSITIONS:
        return False
    return True

def calculate_amount(order_usdt, price, leverage=LEVERAGE):
    # позиція в USDT
    pos_usdt = order_usdt * leverage
    amount = pos_usdt / price
    # округлення — для BTC 6 знаків, можна підлаштувати під монету при необхідності
    return float(round(amount, 6))

# ------------------ Торгові операції ------------------
def set_leverage(symbol, value):
    try:
        # Для Unified Trading Account використовуємо set_leverage
        exchange.set_leverage(value, symbol)
    except Exception as e:
        # Якщо не вдалось встановити, продовжуємо без плеча (буде default)
        print(f"Не вдалось встановити leverage для {symbol}: {e}")
        pass

def open_position(symbol, side):
    try:
        # Отримуємо поточну ціну та розраховуємо параметри
        ticker = exchange.fetch_ticker(symbol)
        price = float(ticker['last'])
        amount = calculate_amount(ORDER_SIZE_USDT, price, LEVERAGE)
        ccxt_side = 'buy' if side == "LONG" else 'sell'
        
        # Розраховуємо TP/SL
        tp = price * (1 + TP_PERCENT/100) if side == "LONG" else price * (1 - TP_PERCENT/100)
        sl = price * (1 - SL_PERCENT/100) if side == "LONG" else price * (1 + SL_PERCENT/100)
        
        # Перевіряємо баланс
        available_balance = get_available_balance()
        required_balance = ORDER_SIZE_USDT
        
        # Формуємо повідомлення про сигнал
        signal_msg = (
            f"🔔 СИГНАЛ {side} на {symbol}\n"
            f"💰 Ціна входу: {price:.4f} USDT\n"
            f"📊 Розмір: {amount:.6f} {symbol.split('/')[0]} (${ORDER_SIZE_USDT} × {LEVERAGE}x)\n"
            f"🎯 Take Profit: {tp:.4f} USDT (+{TP_PERCENT}%)\n"
            f"🛡 Stop Loss: {sl:.4f} USDT (-{SL_PERCENT}%)\n"
            f"💼 Баланс: {available_balance:.2f} USDT"
        )
        
        # Якщо балансу недостатньо - тільки надсилаємо сигнал
        if available_balance < required_balance:
            signal_msg += f"\n\n⚠️ НЕДОСТАТНЬО КОШТІВ! Потрібно: ${required_balance} USDT"
            print(f"{now()} ⚠️ Недостатньо коштів для {symbol}: {available_balance:.2f} < {required_balance}")
            tg_send(signal_msg)
            return False
        
        # Баланс є - відкриваємо позицію
        print(f"{now()} → Відкриваємо {side} {symbol} amount={amount} price≈{price:.2f}")
        tg_send(signal_msg + "\n\n✅ Відкриваємо позицію...")

        # Встановлюємо плече
        try:
            set_leverage(symbol, LEVERAGE)
        except Exception:
            pass

        # Відкриваємо ринкову позицію
        order = exchange.create_market_order(symbol, ccxt_side, amount)
        
        # Зберігаємо локально
        pos = {
            "symbol": symbol,
            "side": 'buy' if side == "LONG" else 'sell',
            "entry_price": price,
            "amount": amount,
            "tp": tp,
            "sl": sl,
            "opened_at": time.time()
        }
        open_positions.append(pos)
        tg_send(f"✅ Позицію {side} {symbol} ВІДКРИТО!\nEntry: {price:.4f} | TP: {tp:.4f} | SL: {sl:.4f}")
        return True
        
    except Exception as e:
        print(f"{now()} ❌ Помилка відкриття {symbol}: {e}")
        tg_send(f"❌ Помилка відкриття {symbol}: {e}")
        return False

def close_position(pos, reason="manual"):
    try:
        symbol = pos['symbol']
        side = 'sell' if pos['side'] == 'buy' else 'buy'  # закриваємо протилежною стороною
        amount = pos['amount']
        print(f"{now()} → Закриваємо {symbol} | by {side} | amount={amount}")
        exchange.create_market_order(symbol, side, amount)
        open_positions.remove(pos)
        tg_send(f"Закрито {symbol} ({reason}). Entry={pos['entry_price']:.2f}")
        return True
    except Exception as e:
        print(f"{now()} ❌ Помилка при закритті позиції: {e}")
        tg_send(f"Помилка при закритті {pos['symbol']}: {e}")
        return False

def monitor_positions():
    # Перевіряємо кожну локальну позицію — якщо TP/SL досягнуто, закриваємо ринковим ордером
    for pos in open_positions.copy():
        try:
            ticker = exchange.fetch_ticker(pos['symbol'])
            last = float(ticker['last'])
            if pos['side'] == 'buy':
                if last >= pos['tp']:
                    print(f"{now()} → TP досягнуто {pos['symbol']} | last={last} >= tp={pos['tp']}")
                    close_position(pos, reason="TP")
                elif last <= pos['sl']:
                    print(f"{now()} → SL досягнуто {pos['symbol']} | last={last} <= sl={pos['sl']}")
                    close_position(pos, reason="SL")
            else:  # short
                if last <= pos['tp']:
                    print(f"{now()} → TP (short) досягнуто {pos['symbol']} | last={last} <= tp={pos['tp']}")
                    close_position(pos, reason="TP")
                elif last >= pos['sl']:
                    print(f"{now()} → SL (short) досягнуто {pos['symbol']} | last={last} >= sl={pos['sl']}")
                    close_position(pos, reason="SL")
        except Exception as e:
            print(f"{now()} ❌ Помилка моніторингу позиції {pos['symbol']}: {e}")
            tg_send(f"Помилка моніторингу {pos['symbol']}: {e}")

# ------------------ Основний цикл ------------------
def main_loop():
    mode = "TESTNET" if TESTNET else "🔴 РЕАЛЬНА БІРЖА 🔴"
    startup_msg = f"🤖 БОТ ЗАПУЩЕНО\n\nРежим: {mode}\n\n"
    
    if not TESTNET:
        startup_msg += "⚠️ УВАГА! Це РЕАЛЬНА торгівля з реальними грошима!\n"
        startup_msg += "🛡 Переконайтесь що ваш API ключ БЕЗ прав на виведення коштів!\n\n"
    
    startup_msg += f"💼 Активних позицій: {len(open_positions)}\n"
    startup_msg += f"📊 Моніторинг: {', '.join(SYMBOLS)}\n"
    startup_msg += f"⏱ Інтервал: {POLL_INTERVAL}s"
    
    tg_send(startup_msg)
    print("=== Старт бот-циклу ===")
    while True:
        try:
            # 1) моніторинг відкритих позицій
            monitor_positions()

            # 2) проходимо по символах, шукаємо сигнали
            for symbol in SYMBOLS:
                # якщо вже є позиція на цій монеті — пропускаємо
                if not can_open_new_position(symbol):
                    continue

                df = fetch_ohlcv_df(symbol)
                df = calculate_indicators(df)
                sig = signal_from_df(df)

                if sig == "LONG" and can_open_new_position(symbol):
                    tg_send(f"Побачено LONG на {symbol}. Перевіряємо можливість відкриття...")
                    open_position(symbol, "LONG")
                elif sig == "SHORT" and can_open_new_position(symbol):
                    tg_send(f"Побачено SHORT на {symbol}. Перевіряємо можливість відкриття...")
                    open_position(symbol, "SHORT")

                time.sleep(1)  # невеличка пауза між символами

            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"{now()} ❌ Critical error main loop: {e}")
            tg_send(f"Critical error main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Зупинка по Ctrl+C")
