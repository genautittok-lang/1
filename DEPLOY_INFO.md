[DEPLOY_INFO.md](https://github.com/user-attachments/files/22891815/DEPLOY_INFO.md)
# 📦 DEPLOY ІНСТРУКЦІЯ + ЯК ПРАЦЮЄ БОТ

## 1️⃣ ФАЙЛИ ДЛЯ GITHUB (усі обов'язкові!)

### ✅ Основні файли для деплою:
```
├── main.py              # ← ГОЛОВНИЙ КОД БОТА
├── requirements.txt     # ← Залежності Python (ccxt, pandas, ta, requests)
├── Procfile            # ← Команда запуску для Railway (worker: python main.py)
├── runtime.txt         # ← Версія Python (python-3.11.0)
├── .gitignore          # ← Виключення файлів (trades_history.json, .env, __pycache__)
└── README.md           # ← Опис проекту
```

### 📋 ТОЧНИЙ СПИСОК для `git add`:
```bash
git add main.py
git add requirements.txt
git add Procfile
git add runtime.txt
git add .gitignore
git add README.md
git add RAILWAY.md        # (опціонально - інструкції для Railway)
git commit -m "Trading bot ready for deployment"
git push origin main
```

### ⚠️ НЕ додавати на GitHub:
- ❌ `.env` файл (секрети!)
- ❌ `trades_history.json` (локальна історія)
- ❌ `__pycache__/` (кеш Python)
- ❌ `replit.md` (специфічно для Replit)

---

## 2️⃣ ЯК ПРАЦЮЄ БОТ: ДЕТАЛЬНИЙ РОЗБІР

### 🔄 Цикл роботи бота (кожні 20 секунд):

```
1. Перевіряє закриті позиції → якщо є, надсилає статистику
2. Обробляє Telegram кнопки → Звіт / Баланс / Позиції
3. Для кожної монети (BTC, ETH, SOL, LINK, ADA):
   ├── Завантажує історичні дані (200 свічок по 5 хвилин)
   ├── Розраховує індикатори (EMA20, EMA50, RSI14, volEMA20)
   ├── Перевіряє умови LONG/SHORT
   ├── Якщо сигнал є → перевіряє чи можна відкрити позицію
   └── Відкриває позицію з TP/SL на біржі
4. Чекає 20 секунд → повторює цикл
```

---

## 3️⃣ ІНДИКАТОРИ: ЯК ПРАЦЮЮТЬ

### 📊 Розрахунок індикаторів (код в `calculate_indicators(df)`):

```python
# 1. EMA20 (Exponential Moving Average 20) - швидка ковзна середня
df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)

# 2. EMA50 (Exponential Moving Average 50) - повільна ковзна середня  
df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)

# 3. RSI14 (Relative Strength Index 14) - індекс відносної сили
df['RSI14'] = ta.momentum.rsi(df['close'], window=14)

# 4. volEMA20 - середній обсяг за 20 періодів
df['volEMA20'] = df['volume'].ewm(span=20).mean()
```

### 📈 Що означають індикатори:

| Індикатор | Пояснення |
|-----------|-----------|
| **EMA20** | Середня ціна за останні 20 свічок (5-хвилинних). Реагує швидко на зміни. |
| **EMA50** | Середня ціна за останні 50 свічок. Реагує повільніше, показує тренд. |
| **RSI14** | Від 0 до 100. > 60 = сила покупців, < 40 = сила продавців. |
| **volEMA20** | Середній обсяг торгів. Використовується для фільтра слабких сигналів. |

---

## 4️⃣ УМОВИ ВІДКРИТТЯ ПОЗИЦІЙ

### ✅ LONG (купівля) - код в `signal_from_df(df)`:

```python
long_cond = (
    last['EMA20'] > last['EMA50']        # ← Швидка EMA вище повільної (висхідний тренд)
    AND last['close'] > last['EMA20']    # ← Ціна вище швидкої EMA (імпульс вгору)
    AND last['RSI14'] > 60               # ← RSI > 60 (сила покупців)
    AND last['volume'] > last['volEMA20'] # ← Обсяг вищий за середній (підтвердження)
)
```

**Простими словами LONG:**
1. ✅ Тренд висхідний (EMA20 > EMA50)
2. ✅ Ціна зростає вище EMA20 (імпульс)
3. ✅ Покупці сильні (RSI > 60)
4. ✅ Великий обсяг торгів (підтвердження руху)

### 📉 SHORT (продаж):

```python
short_cond = (
    last['EMA20'] < last['EMA50']        # ← Швидка EMA нижче повільної (спадний тренд)
    AND last['close'] < last['EMA20']    # ← Ціна нижче швидкої EMA (імпульс вниз)
    AND last['RSI14'] < 40               # ← RSI < 40 (сила продавців)
    AND last['volume'] > last['volEMA20'] # ← Обсяг вищий за середній (підтвердження)
)
```

**Простими словами SHORT:**
1. ✅ Тренд спадний (EMA20 < EMA50)
2. ✅ Ціна падає нижче EMA20 (імпульс)
3. ✅ Продавці сильні (RSI < 40)
4. ✅ Великий обсяг торгів (підтвердження руху)

---

## 5️⃣ ПРОЦЕС ПЕРЕВІРКИ МОНЕТ

### 🔍 Покроковий алгоритм (для кожної монети):

```python
# КРОК 1: Отримує історичні дані
bars = exchange.fetch_ohlcv("BTC/USDT:USDT", timeframe="5m", limit=200)
# ↓ Завантажує 200 останніх 5-хвилинних свічок

# КРОК 2: Створює DataFrame з даними
df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
# ↓ Таблиця з цінами та обсягом

# КРОК 3: Розраховує індикатори
df = calculate_indicators(df)
# ↓ Додає EMA20, EMA50, RSI14, volEMA20

# КРОК 4: Перевіряє умови на ОСТАННІЙ свічці
last_row = df.iloc[-1]  # ← Беремо останній рядок (найсвіжіші дані)
signal = signal_from_df(df)  # ← "LONG" / "SHORT" / "NONE"

# КРОК 5: Якщо сигнал є → перевіряє чи можна відкрити
if signal in ["LONG", "SHORT"]:
    if can_open_new_position("BTC/USDT:USDT"):  # ← Чи немає позиції, чи є баланс
        open_position("BTC/USDT:USDT", signal)  # ← ВІДКРИВАЄ ПОЗИЦІЮ!
```

### 🛡️ Захисні перевірки ПЕРЕД відкриттям:

```python
def can_open_new_position(symbol):
    # 1. Перевіряє чи НЕ відкрита вже позиція на цій монеті
    positions = get_open_positions_from_exchange()
    for p in positions:
        if p['symbol'] == symbol:
            return False  # ← Позиція вже є - НЕ відкриваємо нову!
    
    # 2. Перевіряє ліміт позицій (максимум 10)
    if len(positions) >= MAX_CONCURRENT_POSITIONS:
        return False  # ← Вже 10 позицій - НЕ відкриваємо нову!
    
    # 3. Перевіряє баланс
    balance = get_available_balance()
    if balance < ORDER_SIZE_USDT:  # < $5
        return False  # ← Недостатньо грошей - НЕ відкриваємо!
    
    return True  # ← Все ОК, можна відкривати!
```

---

## 6️⃣ ВІДКРИТТЯ ПОЗИЦІЇ: ЩО ВІДБУВАЄТЬСЯ

### 🚀 Процес відкриття (код в `open_position()`):

```python
# 1. Отримує поточну ціну
ticker = exchange.fetch_ticker("BTC/USDT:USDT")
price = 95000.0  # Приклад

# 2. Розраховує кількість BTC для $5
amount = ORDER_SIZE_USDT / price  # = 5 / 95000 = 0.0000526 BTC

# 3. Розраховує TP/SL ціни
if side == "LONG":
    tp_price = price * 1.05  # +5% = 99750
    sl_price = price * 0.98  # -2% = 93100
else:  # SHORT
    tp_price = price * 0.95  # -5% = 90250
    sl_price = price * 1.02  # +2% = 96900

# 4. Встановлює плече ×10
exchange.set_leverage(10, "BTC/USDT:USDT")

# 5. ВІДКРИВАЄ РИНКОВИЙ ОРДЕР
order = exchange.create_market_order("BTC/USDT:USDT", "buy", 0.0000526)
# ↓ Позиція відкрита!

# 6. ВИСТАВЛЯЄ TP/SL НА БІРЖІ через Bybit API
params = {
    'symbol': 'BTCUSDT',
    'takeProfit': '99750',
    'stopLoss': '93100',
    'tpTriggerBy': 'LastPrice',
    'slTriggerBy': 'LastPrice',
    'category': 'linear'
}
exchange.private_post_v5_position_trading_stop(params)
# ↓ TP/SL виставлено на Bybit - працює навіть якщо бот впаде!

# 7. Надсилає Telegram повідомлення
msg = "✅ ПОЗИЦІЮ ВІДКРИТО
🔸 BTC/USDT:USDT LONG
💵 Розмір: $5.00
📊 Вхід: 95000.0000
🎯 TP: 99750.0000 (+5.0%)
🛑 SL: 93100.0000 (-2.0%)"
```

### 🔥 Чому TP/SL на біржі - це ВАЖЛИВО:

```
ЯКЩО БОТ ВПАДЕ / ВІДКЛЮЧИТЬСЯ:
❌ Локальний моніторинг → позиція БЕЗ ЗАХИСТУ (можуть бути втрати!)
✅ TP/SL на біржі → Bybit АВТОМАТИЧНО закриє по TP або SL
```

---

## 7️⃣ ЗАКРИТТЯ ПОЗИЦІЙ І СТАТИСТИКА

### 💸 Як визначається прибуток:

```python
# Бот періодично перевіряє закриті ордери
closed_orders = exchange.fetch_closed_orders("BTC/USDT:USDT", limit=5)

for order in closed_orders:
    # Отримує РЕАЛЬНИЙ PnL з Bybit API
    pnl_history = exchange.fetch_my_trades("BTC/USDT:USDT", limit=10)
    for trade in pnl_history:
        if trade['order'] == order['id']:
            pnl = trade['info']['closedPnl']  # ← РЕАЛЬНИЙ прибуток/збиток
            
            # Додає в статистику
            if pnl > 0:
                trades_history['wins'] += 1
            else:
                trades_history['losses'] += 1
            
            trades_history['total_profit_usdt'] += pnl
            
            # Зберігає в JSON
            save_trades_history(trades_history)
```

### 📊 Повідомлення про закриття:

```
✅ ПОЗИЦІЮ ЗАКРИТО (TP)
🔸 BTC/USDT:USDT
💵 Прибуток: +0.25 USDT (+5.0%)
📊 Вхід: 95000.0000

АБО

❌ ПОЗИЦІЮ ЗАКРИТО (SL)
🔸 ETH/USDT:USDT
💵 Прибуток: -0.10 USDT (-2.0%)
📊 Вхід: 3500.0000
```

---

## 8️⃣ ЧИ ВСЕ ПРАВИЛЬНО В КОДІ?

### ✅ ПЕРЕВІРЕНО:

| Що | Статус | Пояснення |
|----|--------|-----------|
| **TP/SL на біржі** | ✅ ОК | Використовує `private_post_v5_position_trading_stop` |
| **Формат символів** | ✅ ОК | `BTC/USDT:USDT` правильний для Bybit futures |
| **Розрахунок PnL** | ✅ ОК | Береться з `closedPnl` API (не з комісій) |
| **Розрахунок суми** | ✅ ОК | `amount = 5 / price` (без множення на leverage) |
| **Індикатори** | ✅ ОК | EMA20/50, RSI14, volEMA20 розраховуються правильно |
| **Умови LONG** | ✅ ОК | 4 умови: EMA20>EMA50, ціна>EMA20, RSI>60, обсяг>volEMA20 |
| **Умови SHORT** | ✅ ОК | 4 умови: EMA20<EMA50, ціна<EMA20, RSI<40, обсяг>volEMA20 |
| **Захист від дублів** | ✅ ОК | Перевіряє чи немає позиції перед відкриттям |
| **Ліміт позицій** | ✅ ОК | Максимум 10 позицій одночасно |
| **Telegram кнопки** | ✅ ОК | Звіт, Баланс, Активні позиції |

### 🔍 КОД ІНДИКАТОРІВ (рядки 208-223 в main.py):

```python
def calculate_indicators(df):
    df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['RSI14'] = ta.momentum.rsi(df['close'], window=14)
    df['volEMA20'] = df['volume'].ewm(span=20).mean()
    return df

def signal_from_df(df):
    last = df.iloc[-1]  # ← Остання свічка
    
    # LONG: всі 4 умови одночасно
    long_cond = (
        last['EMA20'] > last['EMA50'] and      # тренд вгору
        last['close'] > last['EMA20'] and      # імпульс вгору
        last['RSI14'] > 60 and                 # покупці сильні
        last['volume'] > last['volEMA20']      # великий обсяг
    )
    
    # SHORT: всі 4 умови одночасно
    short_cond = (
        last['EMA20'] < last['EMA50'] and      # тренд вниз
        last['close'] < last['EMA20'] and      # імпульс вниз
        last['RSI14'] < 40 and                 # продавці сильні
        last['volume'] > last['volEMA20']      # великий обсяг
    )
    
    if long_cond:
        return "LONG"
    if short_cond:
        return "SHORT"
    return "NONE"
```

---

## 9️⃣ ШВИДКИЙ СТАРТ НА RAILWAY

### 1. Завантаж на GitHub:
```bash
git add main.py requirements.txt Procfile runtime.txt .gitignore README.md
git commit -m "Bot ready"
git push origin main
```

### 2. На Railway.com:
- New Project → Deploy from GitHub
- Вибери репозиторій
- Variables → додай секрети:
  ```
  API_KEY=твій_bybit_api_key
  API_SECRET=твій_bybit_secret
  TELEGRAM_TOKEN=твій_telegram_token
  TELEGRAM_CHAT_ID=твій_chat_id
  TESTNET=True  (для тестів) або False (для реальної торгівлі)
  ```
- Deploy автоматично запуститься!

### 3. Перевір логи:
- Deployments → View Logs
- Маєш побачити: "🤖 БОТ ЗАПУЩЕНО"

---

## 🎯 ВИСНОВОК

✅ Всі файли готові для деплою  
✅ Індикатори працюють правильно  
✅ Умови відкриття чіткі та перевірені  
✅ TP/SL виставляються на біржі (безпечно)  
✅ PnL розраховується з реальних даних Bybit  
✅ Захист від дублювання позицій працює  
✅ Telegram бот з кнопками готовий  

**Бот готовий до реальної торгівлі!** 🚀  
(але спочатку протестуй на `TESTNET=True`)
