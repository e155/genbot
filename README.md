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
- Telegraph report links for `/history` and `/rhistory`.

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
- `TELEGRAPH_TOKEN` Telegraph access token for report pages (optional)
- `TELEGRAPH_AUTHOR` Telegraph author name (optional)

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

## Telegraph reports

`/history` and `/rhistory` append a Telegraph report link. If `TELEGRAPH_TOKEN` is
not set, the bot attempts to create a temporary Telegraph account at runtime.

### Create token script

`create_telegraph_token.sh` creates a telegra.ph account and stores
`TELEGRAPH_TOKEN` in `.env`.

```bash
chmod +x create_telegraph_token.sh
./create_telegraph_token.sh
```

---

## Deploy script (from GitHub)

```bash
curl -fsSL -L https://raw.githubusercontent.com/e155/genbot/refs/heads/master/deploy_lxc.sh | bash

./deploy_lxc.sh
```

---

# ⚡ Generator Monitoring Telegram Bot (RU)

Телеграм-бот для мониторинга работы генератора. Определяет состояние
RUNNING/STOPPED по ICMP ping, считает время работы и расход топлива,
ведет историю и формирует отчеты.

---

## Возможности

- Мониторинг состояния генератора (RUNNING / STOPPED).
- Статистика за 24 часа и 7 дней.
- История запусков/остановок и расхода топлива.
- История заправок/сбросов топлива.
- Белый список пользователей.
- Ежедневный и ежемесячный отчеты.
- Ссылки на отчеты в telegra.ph для `/history` и `/rhistory`.

---

## Переменные окружения

- `TOKEN` токен Telegram-бота
- `CHANNELID` ID канала
- `ADMIN_USER_ID` ID администратора
- `BOTURL` ссылка на бота для inline-кнопки
- `LANGUAGE` язык (`en` или `ru`)
- `GENERATORNAME` имя генератора
- `GENERATORADDR` IP/хост генератора
- `INTERVAL` интервал пинга (сек)
- `REPORTH` час ежедневного отчета (0-23)
- `REPORTM` минута ежедневного отчета (0-59)
- `TANK_CAPACITY` объем бака (л)
- `FUEL_CONSUMPTION` расход (л/ч)
- `INITIAL_FUEL` начальный объем топлива (л)
- `LOW_FUEL_HOURS` порог низкого топлива (ч)
- `TELEGRAPH_TOKEN` токен telegra.ph (опционально)
- `TELEGRAPH_AUTHOR` автор на telegra.ph (опционально)

---

## Команды

- `status` статус генератора
- `history [days]` история работы
- `rhistory <days>` история заправок/сбросов
- `refuel <liters>` заправить
- `reset_fuel <liters>` установить уровень топлива
- `month` ежемесячный отчет
- `help` справка
- `allow <user_id>` добавить в whitelist (admin)
- `deny <user_id>` удалить из whitelist (admin)
- `users` список whitelist (admin)
- `settings` текущие настройки (admin)
- `set <KEY> <VALUE>` обновить настройку (admin)

---

## Telegraph отчеты

К командам `/history` и `/rhistory` добавляется ссылка на страницу
telegra.ph с тем же отчетом. Если `TELEGRAPH_TOKEN` не задан, бот
попытается создать временный аккаунт при запуске.

### Скрипт для токена

`create_telegraph_token.sh` создает аккаунт telegra.ph и записывает
`TELEGRAPH_TOKEN` в `.env`.

```bash
chmod +x create_telegraph_token.sh
./create_telegraph_token.sh
```

---

## Быстрый старт

```bash
git clone https://github.com/e155/genbot
cd genbot
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python bot.py
```

Пример `.env`:

```bash
TOKEN=YOUR_TELEGRAM_BOT_TOKEN
CHANNELID=-1001234567890
ADMIN_USER_ID=123456789
BOTURL=https://t.me/yourbot

GENERATORNAME=Main Generator
GENERATORADDR=192.168.1.50

INTERVAL=60
REPORTH=7
REPORTM=0

TANK_CAPACITY=240
FUEL_CONSUMPTION=16
INITIAL_FUEL=190
LOW_FUEL_HOURS=4

TELEGRAPH_TOKEN=YOUR_TELEGRAPH_TOKEN
TELEGRAPH_AUTHOR=Generator Bot
```
