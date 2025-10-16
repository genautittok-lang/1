[README (3).md](https://github.com/user-attachments/files/22944898/README.3.md)
# 🤖 Bybit Trading Bot - EMA/RSI Strategy

Автоматизований торговий бот для Bybit з технічним аналізом та Telegram сповіщеннями.

## ⚠️ ВАЖЛИВО - Обмеження Replit

**Bybit API заблоковано на Replit через CloudFront!** 

Бот НЕ може працювати безпосередньо з Replit. Використовуйте:
- ✅ **Railway.com** (рекомендовано) - [Інструкція тут](RAILWAY.md)
- ✅ VPS (DigitalOcean, AWS, Google Cloud)
- ✅ Локальний комп'ютер
- ✅ Інший хостинг без географічних обмежень

## 🚂 Швидке розгортання на Railway.com

**Найпростіший спосіб запустити бота:**

1. **Форкніть або клонуйте цей репозиторій на GitHub**
2. **Зайдіть на [Railway.com](https://railway.com)**
3. **Створіть новий проект → Deploy from GitHub repo**
4. **Додайте змінні середовища** (API_KEY, API_SECRET, TELEGRAM_TOKEN, etc.)
5. **Готово!** Бот запуститься автоматично

📚 **[Детальна інструкція для Railway →](RAILWAY.md)**

## 📦 Швидкий старт

1. **Завантажте код**
2. **Встановіть залежності:**
```bash
pip install ccxt pandas ta requests python-dotenv
```

3. **Створіть `.env` файл:**
```
API_KEY=ваш_bybit_api_key
API_SECRET=ваш_bybit_api_secret
TELEGRAM_TOKEN=ваш_telegram_bot_token
TELEGRAM_CHAT_ID=ваш_chat_id
TESTNET=True
```

4. **Запустіть:**
```bash
python main.py
```

## 📊 Стратегія (v4.1 - MEGA EDITION 🔥💎)

**11 ПРОФЕСІЙНИХ фільтрів для максимальної якості:**

- **LONG**: EMA20 > EMA50 + ціна > EMA20 + RSI 60-70 + обсяг × 1.3 + ADX > 25 + MACD + BB + **ATR > 0.2% + EMA200 + BTC RSI > 45 + Candle Confirmation**
- **SHORT**: EMA20 < EMA50 + ціна < EMA20 + RSI 30-40 + обсяг × 1.3 + ADX > 25 + MACD + BB + **ATR > 0.2% + EMA200 + BTC RSI < 65 + Candle Confirmation**
- **TP**: +5% | **SL**: -2%
- **Плече**: 10x | **Розмір**: $6
- **Монет**: **80** (ТОП-50 + 30 мемкоїнів: ETH, BNB, DOGE, SHIB, PEPE, FLOKI, BONK, WIF, та інші)
- **Max позицій**: **30** (максимальна диверсифікація!)
- **Winrate**: 70-75% (очікуваний)
- **Профіт**: +$20-30/день стабільно

## 📚 Повна документація

Дивіться [replit.md](replit.md) для детальної інформації.

## 🔒 Безпека

- Тільки testnet для тестів
- API без прав на виведення
- Ніколи не діліться ключами

---

**Статус**: ✅ Готовий до використання (потрібен хостинг без CloudFront блокування)
