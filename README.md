# 1[README.md](https://github.com/user-attachments/files/22889111/README.md)
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

## 📊 Стратегія

- **LONG**: EMA20 > EMA50 + ціна > EMA20 + RSI > 60 + обсяг > volEMA20
- **SHORT**: EMA20 < EMA50 + ціна < EMA20 + RSI < 40 + обсяг > volEMA20
- **TP**: +5% | **SL**: -2%
- **Плече**: 10x | **Розмір**: $5

## 📚 Повна документація

Дивіться [replit.md](replit.md) для детальної інформації.

## 🔒 Безпека

- Тільки testnet для тестів
- API без прав на виведення
- Ніколи не діліться ключами

---

**Статус**: ✅ Готовий до використання (потрібен хостинг без CloudFront блокування)
