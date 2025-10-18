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

# ТОП-150 НАЙЛІКВІДНІШИХ ТОКЕНІВ НА BYBIT USDT PERPETUAL (перевірено 2025-10-18)
# Мемкоїни з малою ціною використовують формат 1000X (1000SHIB, 1000PEPE, тощо)
DEFAULT_SYMBOLS = """BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT,BNB/USDT:USDT,XRP/USDT:USDT,ADA/USDT:USDT,AVAX/USDT:USDT,DOT/USDT:USDT,LINK/USDT:USDT,DOGE/USDT:USDT,TON/USDT:USDT,TRX/USDT:USDT,MATIC/USDT:USDT,SUI/USDT:USDT,UNI/USDT:USDT,1000PEPE/USDT:USDT,LTC/USDT:USDT,NEAR/USDT:USDT,APT/USDT:USDT,HBAR/USDT:USDT,BCH/USDT:USDT,ICP/USDT:USDT,ARB/USDT:USDT,FET/USDT:USDT,OP/USDT:USDT,STX/USDT:USDT,TAO/USDT:USDT,WIF/USDT:USDT,RNDR/USDT:USDT,FIL/USDT:USDT,AAVE/USDT:USDT,INJ/USDT:USDT,SEI/USDT:USDT,ATOM/USDT:USDT,MKR/USDT:USDT,IMX/USDT:USDT,VET/USDT:USDT,1000BONK/USDT:USDT,GRT/USDT:USDT,ALGO/USDT:USDT,1000FLOKI/USDT:USDT,TIA/USDT:USDT,ETC/USDT:USDT,RUNE/USDT:USDT,FTM/USDT:USDT,THETA/USDT:USDT,JUP/USDT:USDT,SAND/USDT:USDT,AXS/USDT:USDT,MANA/USDT:USDT,XLM/USDT:USDT,EOS/USDT:USDT,GALA/USDT:USDT,PENDLE/USDT:USDT,PYTH/USDT:USDT,ORDI/USDT:USDT,WLD/USDT:USDT,JASMY/USDT:USDT,BLUR/USDT:USDT,CRV/USDT:USDT,LDO/USDT:USDT,BRETT/USDT:USDT,APE/USDT:USDT,AR/USDT:USDT,ONDO/USDT:USDT,SNX/USDT:USDT,EGLD/USDT:USDT,BEAM/USDT:USDT,STRK/USDT:USDT,AIOZ/USDT:USDT,FLOW/USDT:USDT,ROSE/USDT:USDT,MINA/USDT:USDT,DYM/USDT:USDT,GMT/USDT:USDT,CHZ/USDT:USDT,XTZ/USDT:USDT,SUSHI/USDT:USDT,1INCH/USDT:USDT,COMP/USDT:USDT,ENJ/USDT:USDT,CELO/USDT:USDT,KAVA/USDT:USDT,ZIL/USDT:USDT,BAT/USDT:USDT,LRC/USDT:USDT,ANKR/USDT:USDT,SKL/USDT:USDT,AUDIO/USDT:USDT,STORJ/USDT:USDT,NKN/USDT:USDT,ACH/USDT:USDT,YFI/USDT:USDT,ZEC/USDT:USDT,DASH/USDT:USDT,WAVES/USDT:USDT,MASK/USDT:USDT,LPT/USDT:USDT,MAGIC/USDT:USDT,CFX/USDT:USDT,AXL/USDT:USDT,ONE/USDT:USDT,ALT/USDT:USDT,MEME/USDT:USDT,BOME/USDT:USDT,PEOPLE/USDT:USDT,IO/USDT:USDT,ZK/USDT:USDT,NOT/USDT:USDT,LISTA/USDT:USDT,ZRO/USDT:USDT,OMNI/USDT:USDT,REZ/USDT:USDT,SAGA/USDT:USDT,W/USDT:USDT,ENA/USDT:USDT,AEVO/USDT:USDT,METIS/USDT:USDT,DGB/USDT:USDT,FXS/USDT:USDT,CELR/USDT:USDT,GMX/USDT:USDT,RDNT/USDT:USDT,WOO/USDT:USDT,SFP/USDT:USDT,HOOK/USDT:USDT,ID/USDT:USDT,HIGH/USDT:USDT,GAS/USDT:USDT,LEVER/USDT:USDT,DYDX/USDT:USDT,SSV/USDT:USDT,MAV/USDT:USDT,EDU/USDT:USDT,CYBER/USDT:USDT,ARK/USDT:USDT,COMBO/USDT:USDT,VANRY/USDT:USDT,PIXEL/USDT:USDT,PORTAL/USDT:USDT,ACE/USDT:USDT,NFP/USDT:USDT,AI/USDT:USDT,XAI/USDT:USDT,MANTA/USDT:USDT,JTO/USDT:USDT,AUCTION/USDT:USDT,1000SHIB/USDT:USDT,1000SATS/USDT:USDT,TRB/USDT:USDT,CORE/USDT:USDT,AGIX/USDT:USDT"""

SYMBOLS = os.getenv("SYMBOLS", DEFAULT_SYMBOLS).split(",")
TIMEFRAME = "5m"
ORDER_SIZE_USDT = 6.0  # $6 per trade
LEVERAGE = 10
TP_PERCENT = 5.0  # Повернуто на 5%
SL_PERCENT = 2.0
MAX_CONCURRENT_POSITIONS = 15  # 15 позицій (баланс $90 / $6 = 15)
POLL_INTERVAL = 20
HISTORY_LIMIT = 200

# Захист від спаму помилок
last_balance_warning = 0  # Час останнього попередження про недостатній баланс

# Файли для зберігання даних
TRADES_HISTORY_FILE = "trades_history.json"
POSITIONS_FILE = "active_positions.json"

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

# ------------------ Локальні позиції (резервний механізм) ------------------
def load_positions():
    """Завантажує активні позиції з файлу"""
    try:
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_positions(positions):
    """Зберігає активні позиції у файл"""
    try:
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
    except Exception as e:
        print(f"Помилка збереження позицій: {e}")

local_positions = load_positions()

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
    # Базові індикатори
    df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['EMA200'] = ta.trend.ema_indicator(df['close'], window=200)  # ПРО: Глобальний тренд
    df['RSI14'] = ta.momentum.rsi(df['close'], window=14)
    df['volEMA20'] = df['volume'].ewm(span=20).mean()
    
    # ПРОФЕСІЙНІ ІНДИКАТОРИ
    # ADX - вимірює СИЛУ тренду (ключовий фільтр!)
    adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['ADX'] = adx_indicator.adx()
    
    # ATR - фільтр волатильності (уникати флету!)
    atr_indicator = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14)
    df['ATR'] = atr_indicator.average_true_range()
    
    # MACD - підтверджує тренд
    macd_indicator = ta.trend.MACD(df['close'])
    df['MACD'] = macd_indicator.macd()
    df['MACD_signal'] = macd_indicator.macd_signal()
    
    # Bollinger Bands - визначає перекупленість
    bb_indicator = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['BB_upper'] = bb_indicator.bollinger_hband()
    df['BB_lower'] = bb_indicator.bollinger_lband()
    df['BB_middle'] = bb_indicator.bollinger_mavg()
    
    return df

def signal_from_df(df, symbol="", btc_rsi=None):
    last = df.iloc[-1]
    prev = df.iloc[-2]  # ПРО: Попередня свічка для підтвердження
    
    # ПРО ФІЛЬТР 1: ATR - уникати флету (волатільність має бути достатня)
    atr_min = last['close'] * 0.003  # ATR має бути >0.3% від ціни (ПОСИЛЕНО!)
    if last['ATR'] < atr_min:
        return "NONE"  # Флет, пропускаємо
    
    # ПРО ФІЛЬТР 2: EMA200 - глобальний тренд
    ema200_long_allowed = last['close'] > last['EMA200']  # Дозволено LONG тільки вище EMA200
    ema200_short_allowed = last['close'] < last['EMA200']  # Дозволено SHORT тільки нижче EMA200
    
    # ПРО ФІЛЬТР 3: BTC фільтр для альткоїнів (80% альтів ідуть за BTC)
    btc_allows_long = True
    btc_allows_short = True
    if btc_rsi is not None and symbol != "BTC/USDT:USDT":
        if btc_rsi < 50:  # BTC слабкий - не відкривати LONG по альтах (ПОСИЛЕНО!)
            btc_allows_long = False
        if btc_rsi > 60:  # BTC сильний - не відкривати SHORT по альтах (ПОСИЛЕНО!)
            btc_allows_short = False
    
    # ПРО ФІЛЬТР 4: Сила тренду EMA (відстань між EMA20 і EMA50)
    ema_distance = abs(last['EMA20'] - last['EMA50']) / last['close']
    strong_trend = ema_distance > 0.003  # EMA20 і EMA50 мають бути розділені >0.3%
    
    if not strong_trend:
        return "NONE"  # Слабкий тренд
    
    # ПОСИЛЕНА СТРАТЕГІЯ - 12 умов з СИЛЬНИМИ параметрами!
    
    # LONG умови (12 фільтрів - ПОСИЛЕНО):
    long_cond = (
        (last['EMA20'] > last['EMA50']) and          # 1. Uptrend
        (last['close'] > last['EMA20']) and          # 2. Ціна вище EMA20
        (last['RSI14'] > 55) and                     # 3. RSI сильний
        (last['RSI14'] < 70) and                     # 4. RSI не перегрів (ПОСИЛЕНО!)
        (last['volume'] > last['volEMA20'] * 1.5) and # 5. Обсяг вище на 50% (ПОСИЛЕНО!)
        (last['ADX'] > 30) and                       # 6. СИЛЬНИЙ ТРЕНД (ПОСИЛЕНО з 20 до 30!)
        (last['MACD'] > last['MACD_signal']) and     # 7. MACD підтверджує
        (last['MACD'] > 0) and                       # 8. MACD позитивний (новий фільтр!)
        (last['close'] < last['BB_upper']) and       # 9. НЕ перекуплено
        ema200_long_allowed and                      # 10. ПРО: EMA200 дозволяє LONG
        btc_allows_long and                          # 11. ПРО: BTC не блокує LONG
        (prev['close'] < last['close'])              # 12. ПРО: Candle confirmation (зростання)
    )
    
    # SHORT умови (12 фільтрів - ПОСИЛЕНО):
    short_cond = (
        (last['EMA20'] < last['EMA50']) and          # 1. Downtrend
        (last['close'] < last['EMA20']) and          # 2. Ціна нижче EMA20
        (last['RSI14'] < 45) and                     # 3. RSI слабкий
        (last['RSI14'] > 30) and                     # 4. RSI не перепродано (ПОСИЛЕНО!)
        (last['volume'] > last['volEMA20'] * 1.5) and # 5. Обсяг вище на 50% (ПОСИЛЕНО!)
        (last['ADX'] > 30) and                       # 6. СИЛЬНИЙ ТРЕНД (ПОСИЛЕНО з 20 до 30!)
        (last['MACD'] < last['MACD_signal']) and     # 7. MACD підтверджує
        (last['MACD'] < 0) and                       # 8. MACD негативний (новий фільтр!)
        (last['close'] > last['BB_lower']) and       # 9. НЕ перепродано
        ema200_short_allowed and                     # 10. ПРО: EMA200 дозволяє SHORT
        btc_allows_short and                         # 11. ПРО: BTC не блокує SHORT
        (prev['close'] > last['close'])              # 12. ПРО: Candle confirmation (падіння)
    )
    
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
    global last_balance_warning
    
    try:
        # Перевіряємо баланс
        available_balance = get_available_balance()
        if available_balance < ORDER_SIZE_USDT:
            # Недостатньо коштів - повідомляємо раз на 5 хвилин
            current_time = time.time()
            if current_time - last_balance_warning > 300:  # 5 хвилин
                print(f"{now()} ⚠️ Недостатньо коштів: {available_balance:.2f} USDT < {ORDER_SIZE_USDT}")
                tg_send(f"⚠️ <b>НЕДОСТАТНЬО КОШТІВ</b>\n\n💰 Баланс: {available_balance:.2f} USDT\n📊 Потрібно: {ORDER_SIZE_USDT} USDT")
                last_balance_warning = current_time
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
        
        # Виставляємо TP і SL через Bybit API
        time.sleep(1.0)  # пауза для обробки ордера
        
        try:
            # Правильний формат symbol для Bybit V5 API
            # BTC/USDT:USDT -> BTCUSDT
            bybit_symbol = symbol.replace('/', '').replace(':USDT', '')
            
            # Для Bybit Unified Trading використовуємо правильні параметри
            params = {
                'category': 'linear',
                'symbol': bybit_symbol,
                'takeProfit': str(round(tp_price, 4)),
                'stopLoss': str(round(sl_price, 4)),
                'tpTriggerBy': 'LastPrice',
                'slTriggerBy': 'LastPrice',
                'positionIdx': 0  # 0 = One-Way Mode (обов'язково!)
            }
            
            print(f"Встановлюю TP/SL для {bybit_symbol}: TP={tp_price:.4f}, SL={sl_price:.4f}")
            
            # Використовуємо приватний метод Bybit для встановлення TP/SL
            response = exchange.private_post_v5_position_trading_stop(params)
            print(f"✅ TP/SL виставлено на біржі: TP={tp_price:.4f}, SL={sl_price:.4f}")
            print(f"   Відповідь біржі: {response}")
            
        except Exception as e:
            print(f"🚨 КРИТИЧНА ПОМИЛКА: TP/SL НЕ ВИСТАВЛЕНО на біржі: {e}")
            tg_send(f"🚨 <b>КРИТИЧНА ПОМИЛКА!</b>\n\nTP/SL НЕ виставлено для {symbol}!\nПомилка: {str(e)}\n\n⚠️ ЗАКРИЙТЕ ПОЗИЦІЮ ВРУЧНУ!")
        
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

# БОТ НЕ ЗАКРИВАЄ ПОЗИЦІЇ - тільки відкриває і встановлює TP/SL на біржі
# Позиції автоматично закриваються біржею по TP/SL

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
            # Обробляємо кнопки Telegram
            handle_telegram_callback()
            
            # ПРО ФІЛЬТР: Отримуємо BTC RSI для альткоїнів
            btc_rsi = None
            try:
                btc_df = fetch_ohlcv_df("BTC/USDT:USDT")
                btc_df = calculate_indicators(btc_df)
                btc_rsi = btc_df.iloc[-1]['RSI14']
                print(f"📊 BTC RSI: {btc_rsi:.1f}")
            except Exception as e:
                print(f"⚠️ Не вдалось отримати BTC RSI: {e}")
            
            # Шукаємо сигнали
            for symbol in SYMBOLS:
                if not can_open_new_position(symbol):
                    print(f"⏭ Пропускаю {symbol} (вже є позиція або ліміт)")
                    continue
                
                try:
                    print(f"📊 Аналіз {symbol}...")
                    df = fetch_ohlcv_df(symbol)
                    df = calculate_indicators(df)
                    
                    # Детальні логи ВСІХ індикаторів (ПРО версія)
                    last = df.iloc[-1]
                    print(f"   📈 Ціна: {last['close']:.4f}")
                    print(f"   📊 EMA20: {last['EMA20']:.4f} | EMA50: {last['EMA50']:.4f} | EMA200: {last['EMA200']:.4f}")
                    print(f"   📉 RSI14: {last['RSI14']:.1f}")
                    print(f"   💪 ADX: {last['ADX']:.1f} (сильний тренд {'✅' if last['ADX'] > 25 else '❌'})")
                    print(f"   🔥 ATR: {last['ATR']:.4f} (волатильність {'✅' if last['ATR'] > last['close']*0.002 else '❌'})")
                    print(f"   📈 MACD: {last['MACD']:.4f} | Signal: {last['MACD_signal']:.4f}")
                    print(f"   💹 Обсяг: {last['volume']:.0f} | volEMA20: {last['volEMA20']:.0f}")
                    
                    sig = signal_from_df(df, symbol=symbol, btc_rsi=btc_rsi)
                    print(f"   ⚡ Сигнал: {sig}")
                    
                    if sig == "LONG" and can_open_new_position(symbol):
                        print(f"🚀 Відкриваю LONG {symbol}")
                        open_position(symbol, "LONG")
                    elif sig == "SHORT" and can_open_new_position(symbol):
                        print(f"📉 Відкриваю SHORT {symbol}")
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
