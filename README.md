# Telegram-бот для заявок с сайта-портфолио

Заявка с сайта → сохраняется в Supabase (таблица `leads`) + приходит уведомлением в Telegram.

## 1. Создать бота

1. В Telegram откройте **@BotFather**, отправьте `/newbot`
2. Укажите имя и username бота (заканчивается на `bot`)
3. Скопируйте **токен** (вида `123456789:AA...`)

## 2. Развернуть на PythonAnywhere (бесплатно)

1. Зарегистрируйтесь на https://www.pythonanywhere.com (бесплатный тариф)
2. Вкладка **Web** → **Add a new web app** → **Manual configuration** → **Python 3.10+** → Next
3. Вкладка **Files** → загрузите файлы этого проекта в `/home/<ваш-юзер>/tg-zayavki/`
   (`app.py`, `requirements.txt`)
4. Вкладка **Consoles** → **Bash console**, выполните:
   ```
   pip install --user flask flask-cors requests gunicorn
   ```
5. Вкладка **Web** → найдите раздел **Virtualenv** → **Enter a virtualenv path** → оставьте пустым (глобальный)
6. В разделе **Code** → **WSGI configuration file** — откройте и замените содержимое на:
   ```python
   import sys
   sys.path.insert(0, '/home/<ваш-юзер>/tg-zayavki')
   from app import app as application
   ```
7. В разделе **Environment variables** добавьте:
   - `BOT_TOKEN` — токен от BotFather
   - `LEAD_SECRET` — любая секретная строка (та же, что в `js/config.js` сайта в `leadSecret`)
   - `SUPABASE_URL` — `https://udozteluyreuhfdgjiqq.supabase.co`
   - `SUPABASE_ANON_KEY` — anon-ключ из `js/config.js` сайта
   - `OWNER_IDS` — ваш Telegram chat_id (узнайте: напишите боту `/start`, потом откройте `https://api.telegram.org/bot<ТОКЕН>/getUpdates` и посмотрите `chat.id`)
8. Нажмите **Reload** (кнопка сверху)
9. Откройте в браузере: `https://<ваш-юзер>.pythonanywhere.com/tg/set-webhook`
   — должно вернуть `{"ok": true, "result": {"ok": true, ...}}`

## 3. Подключить сайт

В `C:\Users\Danis\Desktop\deep-seek-test\js\config.js`:
```
leadUrl: "https://<ваш-юзер>.pythonanywhere.com/api/lead",
leadSecret: "та же строка, что LEAD_SECRET"
```
Задеплойте сайт на Vercel.

## 4. Проверка

1. Напишите боту `/start` (ваш chat_id автоматически добавится в получатели)
2. На сайте заполните форму «Отправить заявку»
3. Заявка придёт вам в Telegram, а также появится в таблице `leads` в Supabase

## Локальный запуск (для теста)

```
set BOT_TOKEN=...
set LEAD_SECRET=...
set SUPABASE_URL=...
set SUPABASE_ANON_KEY=...
python app.py
```
И webhook будет недоступен локально — используйте `ngrok http 5000` и откройте `http://localhost:5000/tg/set-webhook` после настройки ngrok URL, либо вместо этого просто проверьте `/api/lead` через `curl`.
