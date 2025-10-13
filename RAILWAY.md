[RAILWAY (1).md](https://github.com/user-attachments/files/22891825/RAILWAY.1.md)
# 🚂 Розгортання на Railway.com

Детальна інструкція як розгорнути торговий бот на Railway.com

## 📋 Що потрібно підготувати

1. **Акаунт на Railway.com** - зареєструйтесь на https://railway.com
2. **Акаунт на GitHub** - для зберігання коду
3. **Bybit API ключі** - з https://testnet.bybit.com (для тестів)
4. **Telegram Bot** - токен від @BotFather
5. **Telegram Chat ID** - від @userinfobot

---

## 🔧 Крок 1: Підготовка Git репозиторію

### 1.1 Створіть новий репозиторій на GitHub

1. Відкрийте https://github.com/new
2. Назвіть репозиторій, наприклад: `bybit-trading-bot`
3. Виберіть **Private** (для безпеки)
4. **НЕ додавайте** README, .gitignore чи license (вони вже є у проекті)
5. Натисніть **Create repository**

### 1.2 Завантажте код на GitHub

Виконайте в терміналіReplit (Shell):

```bash
# Ініціалізуйте git (якщо ще не зроблено)
git init

# Додайте всі файли
git add .

# Зробіть коміт
git commit -m "Initial commit - Bybit trading bot"

# Підключіть GitHub репозиторій (замініть YOUR_USERNAME та REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Завантажте код
git branch -M main
git push -u origin main
```

**Важливо:** Замініть `YOUR_USERNAME` на ваш GitHub username та `REPO_NAME` на назву репозиторію.

---

## 🚀 Крок 2: Розгортання на Railway

### 2.1 Створіть новий проект

1. Увійдіть на https://railway.com
2. Натисніть **"New Project"**
3. Виберіть **"Deploy from GitHub repo"**
4. Авторизуйте Railway для доступу до GitHub (якщо потрібно)
5. Виберіть репозиторій `bybit-trading-bot`
6. Railway автоматично знайде `Procfile` та почне деплой

### 2.2 Додайте змінні середовища (Environment Variables)

1. В проекті на Railway натисніть на **Variables** (ліва панель)
2. Додайте наступні змінні:

```
API_KEY = ваш_bybit_api_key
API_SECRET = ваш_bybit_api_secret
TELEGRAM_TOKEN = ваш_telegram_bot_token
TELEGRAM_CHAT_ID = ваш_chat_id
TESTNET = True
```

**Опціонально:**
```
SYMBOLS = BTC/USDT,ETH/USDT,SOL/USDT,LINK/USDT,ADA/USDT
```

3. Натисніть **"Deploy"** або Railway автоматично передеплоїть

### 2.3 Перевірте логи

1. Перейдіть на вкладку **Deployments**
2. Натисніть на останній деплой
3. Відкрийте **View Logs**
4. Повинні побачити:
```
[TG] Бот запущено (Testnet=True)
=== Старт бот-циклу ===
```

5. Перевірте Telegram - повинно прийти повідомлення від бота

---

## ✅ Крок 3: Перевірка роботи

### Що перевірити:

1. **Логи Railway** - немає помилок 403 (CloudFront блокування)
2. **Telegram** - отримали стартове повідомлення
3. **Чекаємо сигналів** - бот моніторить ринок та надішле повідомлення при виявленні сигналу

### Якщо бачите помилки:

**403 Forbidden:**
- Railway може мати ті ж обмеження що й Replit
- Спробуйте інший хостинг (DigitalOcean, AWS, Heroku)

**API помилки:**
- Перевірте правильність API ключів
- Переконайтесь що TESTNET=True для testnet ключів

**Telegram не працює:**
- Перевірте TELEGRAM_TOKEN та TELEGRAM_CHAT_ID
- Переконайтесь що бот не заблокований

---

## 🔄 Оновлення коду

Після змін у коді:

```bash
# Додайте зміни
git add .

# Зробіть коміт
git commit -m "Опис змін"

# Завантажте на GitHub
git push

# Railway автоматично задеплоїть нову версію
```

---

## ⚙️ Налаштування параметрів торгівлі

Параметри можна змінити у файлі `main.py`:

```python
ORDER_SIZE_USDT = 5.0          # Розмір позиції в USDT
LEVERAGE = 10                   # Плече
TP_PERCENT = 5.0               # Take Profit %
SL_PERCENT = 2.0               # Stop Loss %
MAX_CONCURRENT_POSITIONS = 10  # Максимум позицій
POLL_INTERVAL = 20             # Інтервал перевірки (секунди)
```

Після зміни - зробіть коміт та push.

---

## 🛑 Зупинка бота

### На Railway:
1. Відкрийте проект
2. Settings → Service → **Delete Service**

### Або тимчасово:
1. Variables → Видаліть API_KEY
2. Бот зупиниться з помилкою

---

## 💰 Вартість

**Railway.com:**
- $5 кредиту безкоштовно щомісяця
- Цей бот споживає мінімум ресурсів
- Повинно вистачити безкоштовного плану

**Альтернативи:**
- **Heroku** (був безкоштовний, тепер платний)
- **Render.com** (безкоштовний план)
- **Fly.io** (безкоштовний план)
- **DigitalOcean** ($4-6/місяць)
- **AWS/GCP** (free tier для малих навантажень)

---

## 🔒 Безпека

✅ **Перед запуском:**
- Використовуйте **Private** GitHub репозиторій
- Обов'язково тестуйте на **Bybit Testnet**
- API ключ **БЕЗ прав на виведення**
- Ніколи не комітьте `.env` файл (він в `.gitignore`)

⚠️ **Пам'ятайте:**
- Це високоризикова торгівля
- Можливі збитки навіть з TP/SL
- Почніть з малих сум

---

## 🆘 Підтримка та помилки

**Якщо щось не працює:**

1. Перевірте логи на Railway
2. Перевірте змінні середовища
3. Переконайтесь що API ключі правильні
4. Перевірте баланс на Bybit testnet

**Поширені проблеми:**

- **403 Forbidden** → Спробуйте інший хостинг
- **Invalid API key** → Перевірте ключі та секрет
- **Insufficient balance** → Поповніть testnet акаунт
- **No signals** → Нормально, чекайте умов стратегії

---

Готово! Бот повинен працювати 24/7 на Railway та надсилати вам Telegram повідомлення про всі торгові події. 🎉
