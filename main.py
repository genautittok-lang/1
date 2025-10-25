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

# Завантажити .env тільки якщо файл існує (для локальної розробки)
# В Replit secrets автоматично доступні через os.getenv()
if os.path.exists('.env'):
    load_dotenv()

# ------------------ НАЛАШТУВАННЯ ------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TESTNET = os.getenv("TESTNET", "False").lower() in ("1", "true", "yes")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ТОП-200 НАЙЛІКВІДНІШИХ ТОКЕНІВ НА BYBIT USDT PERPETUAL (оновлено 2025-10-20)
# Мемкоїни з малою ціною використовують формат 1000X (1000SHIB, 1000PEPE, тощо)
DEFAULT_SYMBOLS = """BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT,BNB/USDT:USDT,XRP/USDT:USDT,ADA/USDT:USDT,AVAX/USDT:USDT,DOT/USDT:USDT,LINK/USDT:USDT,DOGE/USDT:USDT,TON/USDT:USDT,TRX/USDT:USDT,MATIC/USDT:USDT,SUI/USDT:USDT,UNI/USDT:USDT,1000PEPE/USDT:USDT,LTC/USDT:USDT,NEAR/USDT:USDT,APT/USDT:USDT,HBAR/USDT:USDT,BCH/USDT:USDT,ICP/USDT:USDT,ARB/USDT:USDT,SHIB/USDT:USDT,OP/USDT:USDT,STX/USDT:USDT,TAO/USDT:USDT,WIF/USDT:USDT,TWT/USDT:USDT,FIL/USDT:USDT,AAVE/USDT:USDT,INJ/USDT:USDT,SEI/USDT:USDT,ATOM/USDT:USDT,MKR/USDT:USDT,IMX/USDT:USDT,VET/USDT:USDT,1000BONK/USDT:USDT,GRT/USDT:USDT,ALGO/USDT:USDT,1000FLOKI/USDT:USDT,TIA/USDT:USDT,ETC/USDT:USDT,RUNE/USDT:USDT,FTM/USDT:USDT,THETA/USDT:USDT,JUP/USDT:USDT,SAND/USDT:USDT,AXS/USDT:USDT,MANA/USDT:USDT,HYPE/USDT:USDT,VIRTUAL/USDT:USDT,MOVE/USDT:USDT,USUAL/USDT:USDT,POPCAT/USDT:USDT,RENDER/USDT:USDT,POL/USDT:USDT,GRASS/USDT:USDT,ME/USDT:USDT,TRUMP/USDT:USDT,XLM/USDT:USDT,GALA/USDT:USDT,PENDLE/USDT:USDT,PYTH/USDT:USDT,ORDI/USDT:USDT,WLD/USDT:USDT,JASMY/USDT:USDT,BLUR/USDT:USDT,CRV/USDT:USDT,LDO/USDT:USDT,BRETT/USDT:USDT,APE/USDT:USDT,AR/USDT:USDT,ONDO/USDT:USDT,SNX/USDT:USDT,EGLD/USDT:USDT,BEAM/USDT:USDT,STRK/USDT:USDT,AIOZ/USDT:USDT,FLOW/USDT:USDT,ROSE/USDT:USDT,MINA/USDT:USDT,DYM/USDT:USDT,GMT/USDT:USDT,CHZ/USDT:USDT,XTZ/USDT:USDT,SUSHI/USDT:USDT,1INCH/USDT:USDT,COMP/USDT:USDT,ENJ/USDT:USDT,CELO/USDT:USDT,KAVA/USDT:USDT,ZIL/USDT:USDT,BAT/USDT:USDT,LRC/USDT:USDT,ANKR/USDT:USDT,SKL/USDT:USDT,AUDIO/USDT:USDT,STORJ/USDT:USDT,NKN/USDT:USDT,ACH/USDT:USDT,YFI/USDT:USDT,ZEC/USDT:USDT,DASH/USDT:USDT,WAVES/USDT:USDT,MASK/USDT:USDT,LPT/USDT:USDT,MAGIC/USDT:USDT,CFX/USDT:USDT,AXL/USDT:USDT,ONE/USDT:USDT,ALT/USDT:USDT,MEME/USDT:USDT,BOME/USDT:USDT,PEOPLE/USDT:USDT,IO/USDT:USDT,ZK/USDT:USDT,NOT/USDT:USDT,LISTA/USDT:USDT,ZRO/USDT:USDT,OMNI/USDT:USDT,REZ/USDT:USDT,SAGA/USDT:USDT,W/USDT:USDT,ENA/USDT:USDT,AEVO/USDT:USDT,METIS/USDT:USDT,DGB/USDT:USDT,FXS/USDT:USDT,CELR/USDT:USDT,GMX/USDT:USDT,RDNT/USDT:USDT,WOO/USDT:USDT,SFP/USDT:USDT,HOOK/USDT:USDT,ID/USDT:USDT,HIGH/USDT:USDT,GAS/USDT:USDT,DYDX/USDT:USDT,SSV/USDT:USDT,MAV/USDT:USDT,EDU/USDT:USDT,CYBER/USDT:USDT,ARK/USDT:USDT,QNT/USDT:USDT,VANRY/USDT:USDT,PIXEL/USDT:USDT,PORTAL/USDT:USDT,ACE/USDT:USDT,NFP/USDT:USDT,AI/USDT:USDT,XAI/USDT:USDT,MANTA/USDT:USDT,JTO/USDT:USDT,AUCTION/USDT:USDT,PEPE/USDT:USDT,FLOKI/USDT:USDT,TRB/USDT:USDT,CORE/USDT:USDT,BONK/USDT:USDT,GOAT/USDT:USDT,PNUT/USDT:USDT,ACT/USDT:USDT,NEIRO/USDT:USDT,TURBO/USDT:USDT,DOGS/USDT:USDT,HMSTR/USDT:USDT,CATI/USDT:USDT,EIGEN/USDT:USDT,SCR/USDT:USDT,CETUS/USDT:USDT,ETHFI/USDT:USDT,BIGTIME/USDT:USDT"""

SYMBOLS = os.getenv("SYMBOLS", DEFAULT_SYMBOLS).split(",")
TIMEFRAME = "5m"
ORDER_SIZE_USDT = 8.0  # $8 per trade
LEVERAGE = 15
TP_PERCENT = 5.0  # Повернуто на 5%
SL_PERCENT = 2.0
MAX_CONCURRENT_POSITIONS = 10  # 18 позицій (баланс $90 / $5 = 18)
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

last_update_id = 0

def handle_telegram_callback():
    """Обробляє натискання кнопок (викликається періодично)"""
    global last_update_id
    if not TELEGRAM_TOKEN:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": last_update_id + 1}
        response = requests.get(url, params=params, timeout=5).json()
        
        if response.get("ok") and response.get("result"):
            for update in response["result"]:
                update_id = update.get("update_id", 0)
                last_update_id = max(last_update_id, update_id)
                
                if "callback_query" in update:
                    callback_query = update["callback_query"]
                    callback = callback_query["data"]
                    callback_id = callback_query["id"]
                    
                    # Підтверджуємо callback
                    answer_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
                    requests.post(answer_url, json={"callback_query_id": callback_id}, timeout=5)
                    
                    # Обробляємо команду
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
    df['EMA5'] = ta.trend.ema_indicator(df['close'], window=5)    # НОВИЙ: Короткий імпульс
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

def signal_from_df(df, symbol="", btc_rsi=None, btc_adx=None, ema20_15m=None, ema50_15m=None):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    rsi_4bars_ago = df.iloc[-4] if len(df) >= 4 else df.iloc[0]
    atr_3bars_ago = df.iloc[-3] if len(df) >= 3 else df.iloc[0]
    
    # Адаптивний ATR: великі монети (>$10) легше, малі - жорсткіше
    if last['close'] > 10:
        min_atr_percent = 0.002  # BTC, ETH, SOL - м'якше!
    elif last['close'] > 0.1:
        min_atr_percent = 0.003  # Звичайні монети
    else:
        min_atr_percent = 0.01   # Мемкоїни
    atr_pct = last['ATR'] / last['close'] if last['close'] > 0 else 0
    
    # EMA200 тренд
    ema200_long_allowed = last['close'] > last['EMA200']
    ema200_short_allowed = last['close'] < last['EMA200']
    
    # ⚡ ПОКРАЩЕННЯ 2: BTC фільтр волатильності (skip BTC/ETH)
    btc_allows_long = True
    btc_allows_short = True
    if btc_rsi is not None and btc_adx is not None and symbol not in ["BTC/USDT:USDT", "ETH/USDT:USDT"]:
        # Якщо BTC у флеті (ADX < 20) або боковику (RSI 45-55) - не торгуємо!
        if btc_adx < 20 or (45 < btc_rsi < 55):
            btc_allows_long = False
            btc_allows_short = False
        # Старі умови
        elif btc_rsi < 50:
            btc_allows_long = False
        elif btc_rsi > 60:
            btc_allows_short = False
    
    # ⚡ ПОКРАЩЕННЯ 3: Перевірка 15m таймфрейму
    tf15m_allows_long = True
    tf15m_allows_short = True
    if ema20_15m is not None and ema50_15m is not None:
        # LONG тільки якщо на 15m також uptrend
        if ema20_15m < ema50_15m:
            tf15m_allows_long = False
        # SHORT тільки якщо на 15m також downtrend
        if ema20_15m > ema50_15m:
            tf15m_allows_short = False
    
    # Сила тренду EMA
    ema_distance = abs(last['EMA20'] - last['EMA50']) / last['close']
    strong_trend = ema_distance > 0.003
    
    # СТРАТЕГІЯ: 12 БАЗОВИХ + 3 ІМПУЛЬС + 2 КРИТИЧНІ + 2 ПОКРАЩЕННЯ = 19 ФІЛЬТРІВ!
    
    # LONG умови (20 фільтрів):
    long_cond = (
        # === 12 СТАРИХ ФІЛЬТРІВ ===
        (last['EMA20'] > last['EMA50']) and          # 1. Uptrend
        (last['close'] > last['EMA20']) and          # 2. Ціна вище EMA20
        (last['RSI14'] > 55) and                     # 3. RSI сильний
        (last['RSI14'] < 70) and                     # 4. RSI не перегрів
        (last['volume'] > last['volEMA20'] * 1.25) and # 5. Обсяг ×1.25 (М'ЯКШЕ!)
        (last['ADX'] > 25) and                       # 6. СИЛЬНИЙ тренд (ВАРІАНТ A)
        (last['MACD'] > last['MACD_signal']) and     # 7. MACD кросовер
        (last['MACD'] > 0) and                       # 8. MACD позитивний (ПОВЕРНУТО!)
        (last['close'] < last['BB_upper'] * 1.005) and # 9. ЕТАП 1: Breakout дозволено!
        ema200_long_allowed and                      # 10. EMA200 (ПОВЕРНУТО!)
        btc_allows_long and                          # 11. BTC фільтр (ПОКРАЩЕНО!)
        (prev['close'] < last['close']) and          # 12. Candle confirmation
        # === 3 НОВИХ ФІЛЬТРИ ===
        (last['EMA5'] > last['EMA20']) and           # 13. НОВИЙ: Короткий імпульс!
        (last['RSI14'] > rsi_4bars_ago['RSI14'] + 2.5) and  # 14. RSI росте +2.5 (ВАРІАНТ A)
        (last['ATR'] > atr_3bars_ago['ATR']) and     # 15. Волатильність зростає!
        # === ЕТАП 2 ===
        (last['high'] > df['high'].iloc[-6:-1].max() if len(df) >= 6 else True) and  # 16. Новий HIGH!
        # === КРИТИЧНІ ФІЛЬТРИ (BUG FIX!) ===
        (atr_pct >= min_atr_percent) and             # 17. ATR адаптивний!
        strong_trend and                             # 18. Сильний тренд EMA!
        # === ПОКРАЩЕННЯ 3: 15m таймфрейм ===
        tf15m_allows_long                            # 19. 15m uptrend!
    )
    
    # SHORT умови (20 фільтрів):
    short_cond = (
        # === 12 СТАРИХ ФІЛЬТРІВ ===
        (last['EMA20'] < last['EMA50']) and          # 1. Downtrend
        (last['close'] < last['EMA20']) and          # 2. Ціна нижче EMA20
        (last['RSI14'] < 45) and                     # 3. RSI слабкий
        (last['RSI14'] > 30) and                     # 4. RSI не перепродано
        (last['volume'] > last['volEMA20'] * 1.25) and # 5. Обсяг ×1.25 (М'ЯКШЕ!)
        (last['ADX'] > 25) and                       # 6. СИЛЬНИЙ тренд (ВАРІАНТ A)
        (last['MACD'] < last['MACD_signal']) and     # 7. MACD кросовер
        (last['MACD'] < 0) and                       # 8. MACD негативний (ПОВЕРНУТО!)
        (last['close'] > last['BB_lower'] * 0.995) and # 9. ЕТАП 1: Breakout дозволено!
        ema200_short_allowed and                     # 10. EMA200 (ПОВЕРНУТО!)
        btc_allows_short and                         # 11. BTC фільтр (ПОКРАЩЕНО!)
        (prev['close'] > last['close']) and          # 12. Candle confirmation
        # === 3 НОВИХ ФІЛЬТРИ ===
        (last['EMA5'] < last['EMA20']) and           # 13. Короткий імпульс вниз!
        (last['RSI14'] < rsi_4bars_ago['RSI14'] - 2.5) and  # 14. RSI падає -2.5 (ВАРІАНТ A)
        (last['ATR'] > atr_3bars_ago['ATR']) and     # 15. Волатільність зростає!
        # === ЕТАП 2 ===
        (last['low'] < df['low'].iloc[-6:-1].min() if len(df) >= 6 else True) and  # 16. Новий LOW!
        # === КРИТИЧНІ ФІЛЬТРИ (BUG FIX!) ===
        (atr_pct >= min_atr_percent) and             # 17. ATR адаптивний!
        strong_trend and                             # 18. Сильний тренд EMA!
        # === ПОКРАЩЕННЯ 3: 15m таймфрейм ===
        tf15m_allows_short                           # 19. 15m downtrend!
    )
    
    # 🔍 DEBUG: Детальний розклад ВСІХ фільтрів (завжди показуємо!)
    long_conditions = {
            "1.EMA20>EMA50": last['EMA20'] > last['EMA50'],
            "2.close>EMA20": last['close'] > last['EMA20'],
            "3.RSI>55": last['RSI14'] > 55,
            "4.RSI<70": last['RSI14'] < 70,
            "5.Vol×1.25": last['volume'] > last['volEMA20'] * 1.25,
            "6.ADX>25": last['ADX'] > 25,
            "7.MACD_cross": last['MACD'] > last['MACD_signal'],
            "8.MACD>0": last['MACD'] > 0,
            "9.BB_breakout": last['close'] < last['BB_upper'] * 1.005,
            "10.EMA200": ema200_long_allowed,
            "11.BTC_filter": btc_allows_long,
            "12.Candle": prev['close'] < last['close'],
            "13.EMA5>EMA20": last['EMA5'] > last['EMA20'],
            "14.RSI_impulse": last['RSI14'] > rsi_4bars_ago['RSI14'] + 2.5,
            "15.ATR_growth": last['ATR'] > atr_3bars_ago['ATR'],
            "16.New_HIGH": last['high'] > df['high'].iloc[-6:-1].max() if len(df) >= 6 else True,
            "17.ATR_min": atr_pct >= min_atr_percent,
            "18.Strong_trend": strong_trend,
            "19.15m_uptrend": tf15m_allows_long
        }
    short_conditions = {
            "1.EMA20<EMA50": last['EMA20'] < last['EMA50'],
            "2.close<EMA20": last['close'] < last['EMA20'],
            "3.RSI<45": last['RSI14'] < 45,
            "4.RSI>30": last['RSI14'] > 30,
            "5.Vol×1.25": last['volume'] > last['volEMA20'] * 1.25,
            "6.ADX>25": last['ADX'] > 25,
            "7.MACD_cross": last['MACD'] < last['MACD_signal'],
            "8.MACD<0": last['MACD'] < 0,
            "9.BB_breakout": last['close'] > last['BB_lower'] * 0.995,
            "10.EMA200": ema200_short_allowed,
            "11.BTC_filter": btc_allows_short,
            "12.Candle": prev['close'] > last['close'],
            "13.EMA5<EMA20": last['EMA5'] < last['EMA20'],
            "14.RSI_impulse": last['RSI14'] < rsi_4bars_ago['RSI14'] - 2.5,
            "15.ATR_growth": last['ATR'] > atr_3bars_ago['ATR'],
            "16.New_LOW": last['low'] < df['low'].iloc[-6:-1].min() if len(df) >= 6 else True,
            "17.ATR_min": atr_pct >= min_atr_percent,
            "18.Strong_trend": strong_trend,
            "19.15m_downtrend": tf15m_allows_short
        }
    
    # Показуємо які фільтри заблокували (завжди!)
    failed_long = [k for k, v in long_conditions.items() if not v]
    failed_short = [k for k, v in short_conditions.items() if not v]
    
    if last['EMA20'] > last['EMA50'] and failed_long:
        print(f"   ❌ LONG blocked by: {', '.join(failed_long)}")
    if last['EMA20'] < last['EMA50'] and failed_short:
        print(f"   ❌ SHORT blocked by: {', '.join(failed_short)}")
    if last['EMA20'] == last['EMA50']:
        print(f"   ⚠️ SIDEWAYS: EMA20 == EMA50 (немає тренду)")
    
    if long_cond:
        print(f"   🚀 LONG SIGNAL! All 19 filters passed!")
        return "LONG"
    if short_cond:
        print(f"   📉 SHORT SIGNAL! All 19 filters passed!")
        return "SHORT"
    return "NONE"

def can_open_new_position(symbol, cached_positions=None):
    """Перевіряє чи можна відкрити нову позицію на символі
    
    Args:
        symbol: Символ токена
        cached_positions: Кешовані позиції (щоб не робити 151 запит до API!)
    """
    # Використовуємо кешовані позиції або завантажуємо (якщо не передано)
    positions = cached_positions if cached_positions is not None else get_open_positions_from_exchange()
    
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

def open_position(symbol, side, atr=None):
    """Відкриває позицію з TP/SL на біржі
    
    Args:
        symbol: Символ токена
        side: LONG або SHORT
        atr: ATR значення для адаптивного TP/SL (якщо None - використовує фіксовані %)
    """
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
        
        # ⚡ ПОКРАЩЕННЯ 1: Адаптивний TP/SL на базі ATR з мінімумами
        # Мінімуми: TP >= 1.5%, SL >= 0.5%, TP завжди >= SL × 2
        MIN_TP_PERCENT = 1.5
        MIN_SL_PERCENT = 0.5
        
        if atr is not None and atr > 0:
            # Динамічний TP/SL: TP = entry ± ATR×3, SL = entry ± ATR×1.5
            atr_tp_distance = atr * 3.0
            atr_sl_distance = atr * 1.5
            
            # Мінімальні відстані в абсолютних значеннях
            min_sl_distance = price * (MIN_SL_PERCENT / 100)
            
            # SL = максимум з ATR×1.5 або мінімуму 0.5%
            sl_distance = max(atr_sl_distance, min_sl_distance)
            
            # TP = максимум з (ATR×3, SL×2, мінімум 1.5%)
            min_tp_by_ratio = sl_distance * 2  # TP завжди >= SL × 2
            min_tp_distance = price * (MIN_TP_PERCENT / 100)
            tp_distance = max(atr_tp_distance, min_tp_by_ratio, min_tp_distance)
            
            if side == "LONG":
                tp_price = price + tp_distance
                sl_price = price - sl_distance
            else:  # SHORT
                tp_price = price - tp_distance
                sl_price = price + sl_distance
            
            # Розраховуємо % для логування
            tp_percent = abs((tp_price - price) / price * 100)
            sl_percent = abs((sl_price - price) / price * 100)
        else:
            # Фіксовані % (fallback)
            tp_price = price * (1 + TP_PERCENT/100) if side == "LONG" else price * (1 - TP_PERCENT/100)
            sl_price = price * (1 - SL_PERCENT/100) if side == "LONG" else price * (1 + SL_PERCENT/100)
            tp_percent = TP_PERCENT
            sl_percent = SL_PERCENT
        
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
        atr_mode = "ATR×3/1.5" if atr is not None else "Fixed"
        msg = f"""✅ <b>ПОЗИЦІЮ ВІДКРИТО</b>

🔸 {symbol} {side}
💰 Вхід: {price:.4f} USDT
📊 Розмір: ${ORDER_SIZE_USDT} (×{LEVERAGE})
🎯 TP: {tp_price:.4f} (+{tp_percent:.1f}%)
🛡 SL: {sl_price:.4f} (-{sl_percent:.1f}%)
⚡ Mode: {atr_mode}"""
        
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
            
            # ⚡ ПОКРАЩЕННЯ 2+3: Отримуємо BTC RSI + ADX для фільтра волатильності
            btc_rsi = None
            btc_adx = None
            try:
                btc_df = fetch_ohlcv_df("BTC/USDT:USDT")
                btc_df = calculate_indicators(btc_df)
                btc_rsi = btc_df.iloc[-1]['RSI14']
                btc_adx = btc_df.iloc[-1]['ADX']
                print(f"📊 BTC RSI: {btc_rsi:.1f} | ADX: {btc_adx:.1f}")
            except Exception as e:
                print(f"⚠️ Не вдалось отримати BTC дані: {e}")
            
            # ВИПРАВЛЕНО: Кешуємо позиції 1 раз на цикл (було 151 запит!)
            cached_positions = get_open_positions_from_exchange()
            print(f"📊 Відкритих позицій: {len(cached_positions)}/{MAX_CONCURRENT_POSITIONS}")
            
            # Шукаємо сигнали
            for symbol in SYMBOLS:
                if not can_open_new_position(symbol, cached_positions):
                    print(f"⏭ Пропускаю {symbol} (вже є позиція або ліміт)")
                    continue
                
                try:
                    print(f"📊 Аналіз {symbol}...")
                    df = fetch_ohlcv_df(symbol, timeframe=TIMEFRAME)
                    df = calculate_indicators(df)
                    
                    # ⚡ ПОКРАЩЕННЯ 3: Отримуємо 15m таймфрейм для підтвердження
                    ema20_15m = None
                    ema50_15m = None
                    try:
                        df_15m = fetch_ohlcv_df(symbol, timeframe="15m", limit=100)
                        df_15m = calculate_indicators(df_15m)
                        ema20_15m = df_15m.iloc[-1]['EMA20']
                        ema50_15m = df_15m.iloc[-1]['EMA50']
                    except:
                        pass  # Якщо не вдалось - пропускаємо (фільтр буде True)
                    
                    # Детальні логи з DEBUG (19 фільтрів)
                    last = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    # Адаптивний ATR: великі монети (>$10) легше
                    if last['close'] > 10:
                        min_atr_percent = 0.002  # BTC, ETH, SOL - м'якше!
                    elif last['close'] > 0.1:
                        min_atr_percent = 0.003  # Звичайні монети
                    else:
                        min_atr_percent = 0.01   # Мемкоїни
                    atr_pct = (last['ATR'] / last['close'] * 100) if last['close'] > 0 else 0
                    
                    # Перевірка volume
                    vol_status = "⚠️ ZERO!" if last['volume'] == 0 else f"{last['volume']:.0f}"
                    
                    print(f"   💰 Ціна: {last['close']:.4f}")
                    print(f"   📊 EMA: 5={last['EMA5']:.4f} | 20={last['EMA20']:.4f} | 50={last['EMA50']:.4f} | 200={last['EMA200']:.4f}")
                    if ema20_15m and ema50_15m:
                        print(f"   📊 15m EMA: 20={ema20_15m:.4f} | 50={ema50_15m:.4f} {'📈' if ema20_15m > ema50_15m else '📉'}")
                    print(f"   📉 RSI: {last['RSI14']:.1f} (need: 55-70 LONG, 30-45 SHORT)")
                    print(f"   💪 ADX: {last['ADX']:.1f} (need >25) {'✅' if last['ADX'] > 25 else '❌'}")
                    print(f"   🔥 ATR: {last['ATR']:.6f} = {atr_pct:.3f}% (need {min_atr_percent*100:.1f}%) {'✅' if atr_pct/100 >= min_atr_percent else '❌'}")
                    print(f"   📈 MACD: {last['MACD']:.6f} | Signal: {last['MACD_signal']:.6f} {'✅' if last['MACD'] > last['MACD_signal'] else '❌'}")
                    print(f"   💹 Volume: {vol_status} | volEMA20: {last['volEMA20']:.0f} (×1.25 = {last['volEMA20']*1.25:.0f}) {'✅' if last['volume'] > last['volEMA20']*1.25 else '❌'}")
                    
                    sig = signal_from_df(df, symbol=symbol, btc_rsi=btc_rsi, btc_adx=btc_adx, ema20_15m=ema20_15m, ema50_15m=ema50_15m)
                    print(f"   ⚡ Сигнал: {sig}")
                    
                    if sig == "LONG" and can_open_new_position(symbol, cached_positions):
                        print(f"🚀 Відкриваю LONG {symbol}")
                        open_position(symbol, "LONG", atr=last['ATR'])
                        # Оновлюємо кеш після відкриття
                        cached_positions = get_open_positions_from_exchange()
                    elif sig == "SHORT" and can_open_new_position(symbol, cached_positions):
                        print(f"📉 Відкриваю SHORT {symbol}")
                        open_position(symbol, "SHORT", atr=last['ATR'])
                        # Оновлюємо кеш після відкриття
                        cached_positions = get_open_positions_from_exchange()
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
