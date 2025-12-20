# Generator Monitoring Telegram Bot

Telegram-based monitoring bot for a generator. It uses ICMP ping to detect
RUNNING/STOPPED state, tracks runtime and fuel usage, and provides reports.

---

## Key features

- Generator state monitoring via ICMP ping (RUNNING / STOPPED).
- Runtime and fuel usage stats for 24 hours and 7 days.
- Refuel and fuel reset tracking.
- Whitelist access control.
- Daily reports at a scheduled time.
- Monthly report for the previous month.
- Admin-only settings view and edit via bot commands.

---

## Settings and behavior

- The bot uses `.env` for configuration and reads values at startup.
- `INTERVAL` controls ping check frequency.
- Daily reports use `REPORTH` and `REPORTM`.
- Monthly report is sent on day 1 at `REPORTH`/`REPORTM`.

### Environment variables

- `TOKEN` Telegram bot token
- `CHANNELID` target channel ID
- `ADMIN_USER_ID` admin user ID
- `BOTURL` bot URL for inline button
- `LANGUAGE` bot language (`en` or `ru`)
- `GENERATORNAME` generator display name
- `GENERATORADDR` generator IP/host for ICMP ping
- `INTERVAL` ping interval (seconds)
- `REPORTH` daily report hour (0-23)
- `REPORTM` daily report minute (0-59)
- `TANK_CAPACITY` tank capacity (liters)
- `FUEL_CONSUMPTION` liters per hour
- `INITIAL_FUEL` initial fuel in tank (liters)
- `LOW_FUEL_HOURS` low-fuel alert threshold (hours)

---

## Database

SQLite database `generator.db`:

- `generator_log` start/stop history and fuel usage
- `refuel_log` refuel/reset history
- `state` current state values
- `users` whitelist

---

## Bot commands

- `status` current generator status
- `history` generator activity history
- `rhistory` refuel/reset history
- `refuel` add fuel
- `reset_fuel` set fuel value
- `month` monthly report for previous month (public)
- `help` show help
- `allow` add user (admin)
- `deny` remove user (admin)
- `users` list whitelist (admin)
- `settings` show current settings (admin)
- `set` update a setting (admin)

---

## Deploy script (from GitHub)

```bash
curl -fsSL -L https://raw.githubusercontent.com/e155/genbot/refs/heads/master/deploy_lxc.sh | bash

./deploy_lxc.sh
```

---

# ⚡ Generator Monitoring Telegram Bot

Telegram-бот для мониторинга времени работы дизельного/бензинового генератора по сети (ICMP ping),
учёта времени работы, рассчетного расхода топлива и ведения истории заправок.

---

## 📌 Основные возможности

- 📡 Определение состояния генератора (RUNNING / STOPPED) по ping
- ⛽ Учёт топлива и расчёт оставшегося времени работы
- 🚨 Уведомление о низком уровне топлива
- 📊 Статистика работы за 24 часа и 7 дней
- 🕓 История запусков и остановок генератора
- 🛢️ История заправок и ручных корректировок топлива
- 🔐 Система whitelist-доступа пользователей для регистрации заправок
---

## 🚀 Скрипт развертывания (из GitHub)

```bash
curl -fsSL -L https://raw.githubusercontent.com/e155/genbot/refs/heads/master/deploy_lxc.sh | bash
```

---

## 🧠 Логика работы

### Определение состояния генератора
- Генератор считается **запущенным**, если хост (`GENERATORADDR`) отвечает на ICMP ping
- Генератор считается **остановленным**, если ping недоступен

Проверка выполняется каждые `INTERVAL` секунд.

---

### Учёт топлива

Бот использует **расчётную модель топлива**, а не реальные датчики, подстройка усредненного значения расхода указывается в **.env**.

#### Основные параметры:
- `TANK_CAPACITY` — ёмкость бака (литры)
- `FUEL_CONSUMPTION` — расход топлива (л/час)
- `INITIAL_FUEL` — начальный уровень топлива (считывается из .env впервые, потом из БД)
- `LOW_FUEL_HOURS` — порог предупреждения (в часах работы)

#### Как считается топливо:
- При запуске генератора фиксируется:
  - `start_time`
  - `fuel_start`
- Во время работы:

  - `fuel_used = runtime_seconds / 3600 * FUEL_CONSUMPTION`
  - fuel_left = fuel_start - fuel_used

#### При остановке:
- данные сохраняются в историю
- уровень топлива фиксируется в БД

⚠️ Бот корректно восстанавливает состояние после перезапуска.

---

### Уведомление о низком топливе

- Если оставшееся время работы `< LOW_FUEL_HOURS`
- И предупреждение ещё не отправлялось
→ бот отправляет **однократное** предупреждение в канал

После заправки или выхода за порог уведомление может сработать снова.

---

## 🗄️ Хранение данных

Используется SQLite (`generator.db`):

### Таблицы:
- `generator_log` — история запусков/остановок
- `refuel_log` — история заправок и reset
- `state` — текущее состояние генератора
- `users` — whitelist пользователей

---

## 🔐 Система доступа

- Все команды, влияющие на состояние заправки, доступны **только пользователям из whitelist**
- Управление whitelist — только для администратора (`ADMIN_USER_ID`)
- Администратор задаётся через `.env`

---

## ⚙️ Установка и запуск

### 1️⃣ Установка зависимостей
```bash
 git clone https://github.com/e155/genbot
 cd genbot/
 nano .env #Configure variables
 apt install python3.13-venv
 python3 -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 timedatectl set-timezone Europe/Kyiv #yourTZ
 ln -sf /usr/share/zoneinfo/Europe/Kyiv /etc/localtime #yourTZ
 echo "Europe/Kyiv" |  tee /etc/timezone #YourTZ
 python3 bot.py
```
### 2️⃣ Настройка .env
```bash
TOKEN=YOUR_TELEGRAM_BOT_TOKEN
CHANNELID=-1001234567890
ADMIN_USER_ID=123456789

GENERATORNAME=Main Generator
GENERATORADDR=192.168.1.50

#Recomended interval >=30
INTERVAL=60
#Daily report time (UTC time)
REPORTH=7
REPORTM=0

TANK_CAPACITY=240
FUEL_CONSUMPTION=16
INITIAL_FUEL=190
LOW_FUEL_HOURS=4
```
### 3️⃣ Запуск
```bash
python3 bot.py
```

### 4️⃣ Использование в качестве сервиса 
#### Установка как сервис
```
chmod +x installservice.sh
installservice.sh
```
Edit **SERVICE_NAME** variable<BR> 
Default ="Genbot"

#### Remove  service
```
chmod +x removeservice.sh
removeservice.sh
```

### 5️⃣ Комманды бота

- status -  Текущий статус
- history  -  История циклов работы
- rhistory - Исторя заправко/корректировок: /rhistory 2 - за 2 дня
- refuel -  Внести заправку: /refuel 50 - 50 литров
- reset_fuel - Указать новое значение заправки
- month - Отчет за прошлый месяц (доступно всем)
- allow id- добавить оператора
- deny id- убрать оператора
- users - показать id операторов
- settings - показать текущие настройки (админ)
- set - изменить настройку (админ)
- help - Показать справку

---

## Обновления

- Команды администратора: `/settings` показывает текущие значения, `/set <KEY> <VALUE>` обновляет значения в памяти и `.env`.
- Месячный отчет: `/month` показывает отчет за прошлый месяц.
- Авто-отчет за месяц: выполняется 1-го числа в время `REPORTH`/`REPORTM`.
