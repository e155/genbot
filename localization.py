import os

DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en").lower()

MESSAGES = {
    "en": {
        "access_denied": "❗️Access denied.\nYou are not authorized to use this bot.",
        "admin_only": "❗️Admin only.",
        "settings_header": "Settings:",
        "settings_line": "{setting_key}={value}",
        "settings_usage": "Usage: /set <KEY> <VALUE>\nKeys: {keys}",
        "settings_invalid_key": "Invalid key. Keys: {keys}",
        "settings_invalid_value": "Invalid value for {setting_key}.",
        "settings_updated": "{setting_key} updated to {value}.",
        "settings_env_missing": "Warning: .env not updated; change applies only to this run.",
        "usage_allow": "❕Usage: /allow <user_id>",
        "usage_deny": "❕Usage: /deny <user_id>",
        "invalid_user_id": "❕Invalid user_id.",
        "allow_added": "❕User {user_id} added to whitelist.",
        "deny_removed": "❕User {user_id} removed from whitelist.",
        "whoami": "❕Your ID: {user_id}{username_line}",
        "username_line": "\n❕Username: @{username}",
        "refuel_history_usage": "❕Usage: /rhistory <days>",
        "refuel_history_invalid_days": "❕Invalid number of days.",
        "refuel_history_empty": "❕No refuel records for last {days} days.",
        "refuel_history_header": "❕Refuel history (last {days} days):",
        "refuel_history_line": "{time} | {action} | {before:.1f} -> {after:.1f} | {user}",
        "refuel_history_action_add": "+{amount:.1f} L",
        "refuel_history_action_reset": "❕RESET",
        "history_usage": "❕Usage: /history [days]\nExample: /history 7",
        "history_empty": "❕No generator activity for last {days} day(s).",
        "history_header": "❕Generator history (last {days} day(s)):",
        "history_line": "{start} -> {stop}\n  ⏱️Runtime: {hours}h {minutes}m\n  ⛽️🔽 Fuel used: {fuel:.1f} L",
        "refuel_table_cols": "TIME|ACTION|BEFORE|AFTER|USER",
        "history_table_cols": "START|STOP|RUN|FUEL(L)",
        "history_table_run_format": "{hours}h {minutes:02d}m",
        "report_link": "Report: {link}",
        "open_bot_button": "Open bot",
        "whitelist_empty": "❕Whitelist is empty.",
        "whitelist_header": "❕Allowed users:",
        "whitelist_line": "❕{user_id} | {username} | added: {added_at}",
        "unknown_user": "N/A",
        "not_available": "N/A",
        "bot_restarted": "❕Generator bot restarted\nTime: {time}",
        "state_running": "🌀RUNNING",
        "state_stopped": "❌STOPPED",
        "status": (
            "❕STATUS: {generator}\n\n"
            "State: {state}\n"
            "⛽️Fuel left: {fuel_left:.1f} L\n\n"
            "⏳Estimated runtime: {remaining_time}\n\n"
            "Last 24h:\n"
            "  ⏱️Runtime: {day_hours}h {day_minutes}m\n"
            "  ⛽️🔽 Fuel used: {day_fuel:.1f} L\n\n"
            "Last 7 days:\n"
            "  ⏱️Runtime: {week_hours}h {week_minutes}m\n"
            "  ⛽️🔽 Fuel used: {week_fuel:.1f} L"
        ),
        "motohours_line": "Total runtime: {total_hours}h {total_minutes}m",
        "service_not_set_line": "Service: not set (use /setservice X)",
        "service_remaining_line": "Service in: {hours}h {minutes}m",
        "service_overdue_line": "Service overdue by: {hours}h {minutes}m",
        "service_due_alert": (
            "??????SERVICE DUE: {generator}\n"
            "Total runtime: {total_hours}h {total_minutes}m\n"
            "Please schedule maintenance and set next service via /setservice X"
        ),
        "setservice_usage": "Usage: /setservice <hours>\nExample: /setservice 100",
        "setservice_invalid_value": "Invalid hours value.",
        "setservice_done": "Next service set in {hours} h.",
        "setservice_cleared": "Service reminder cleared.",
        "setmhours_usage": "Usage: /setmhours <hours>\nExample: /setmhours 123.5",
        "setmhours_invalid_value": "Invalid hours value.",
        "setmhours_done": "Motohours set to {hours} h.",
        "refuel_usage": "❕Usage: /refuel <liters>",
        "refuel_invalid_amount": "❕Invalid fuel amount.",
        "refuel_saved": (
            "❕Refuel recorded\n"
            "🔄Added: {amount:.1f} L\n"
            "⛽️Fuel level: {fuel_after:.1f} / {capacity:.1f} L\n"
            "👨🏻‍🦱By: {user}"
        ),
        "reset_usage": "❕Usage: /reset_fuel <liters>",
        "reset_invalid": "❕Invalid fuel value.",
        "reset_overflow": "❕Fuel value exceeds tank capacity ({capacity:.1f} L).",
        "reset_done": (
            "❕Fuel level RESET\n"
            "🔄New level: {fuel_after:.1f} / {capacity:.1f} L\n"
            "👨🏻‍🦱By: {user}"
        ),
        "low_fuel_alert": (
            "❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️\n"
            "❗️Low fuel for {generator}\n"
            "⛽️Fuel left (est.): {fuel_left:.1f} L\n"
            "⏳Estimated runtime: {remaining_time}\n"
            "⚠️Threshold: < {threshold:.2f} h"
        ),
        "generator_started": (
            "{generator} STARTED\n"
            "⛽️Fuel left: {fuel_left:.1f} L\n"
            "⏳Estimated runtime: {remaining_time}"
        ),
        "generator_stopped": (
            "{generator} STOPPED\n"
            "⏱️Runtime: {runtime_minutes} min\n"
            "⛽️🔽 Fuel used: {fuel_used:.1f} L\n"
            "⛽️Fuel left: {fuel_left:.1f} L\n"
            "⏳Estimated runtime: {remaining_time}"
        ),
        "help": (
            "Generator monitoring bot\n\n"
            "Available commands:\n\n"
            "/status\n"
            "  Show current generator status\n"
            "  Fuel level and estimated remaining runtime\n"
            "  Statistics for last 24 hours and last 7 days\n\n"
            "/history [days]\n"
            "  Generator start/stop history and fuel usage\n"
            "  Default: 1 day\n"
            "  Example: /history 7\n\n"
            "/refuel <liters>\n"
            "  Add fuel to the tank\n"
            "  Example: /refuel 50\n\n"
            "/rhistory <days>\n"
            "  Refuel/reset history\n"
            "  Example: /rhistory 7\n\n"
            "/reset_fuel <liters>\n"
            "  Force set current fuel level\n"
            "  Example: /reset_fuel 190\n\n"
            "/help\n"
            "  Show this help message\n\n"
            "/month\n"
            "  Show monthly report for last month\n\n"
            "/setservice <hours>\n"
            "  Set next service after X hours of runtime\n"
            "  Use /setservice 0 to clear the reminder\n\n"
            "Admin only:\n"
            "/allow <user_id>\n"
            "  Add user to whitelist\n"
            "/deny <user_id>\n"
            "  Remove user from whitelist\n"
            "/users\n"
            "  List whitelist users\n"
            "/whoami\n"
            "  Show your user id\n\n"
            "/settings\n"
            "  Show current settings\n"
            "/set <KEY> <VALUE>\n"
            "  Update setting in .env and runtime\n\n"
            "/setmhours <hours>\n"
            "  Adjust total motohours\n"
        ),
        "daily_report_running": (
            "📊DAILY REPORT: {generator}\n\n"
            "🗓Date: {date}\n\n"
            "⚡️Generator was RUNNING\n\n"
            "⏱️Runtime: {runtime_hours}h {runtime_minutes}m\n"
            "⛽️🔽 Fuel used: {fuel_used:.1f} L\n\n"
            "⛽️Fuel left: {fuel_left:.1f} L\n"
            "⏳Estimated runtime: {remaining_time}"
        ),
        "daily_report_idle": (
            "📊 DAILY REPORT: {generator}\n\n"
            "🗓Date: {date}\n\n"
            "💤Generator was NOT running in last 24h\n\n"
            "⛽️Fuel left: {fuel_left:.1f} L\n"
            "⏳Estimated runtime: {remaining_time}"
        ),
        "monthly_report": (
            "📅MONTHLY REPORT: {generator}\n\n"
            "Month: {month}\n\n"
            "⏱️Runtime: {runtime_hours}h {runtime_minutes}m\n"
            "⛽️🔽 Fuel used: {fuel_used:.1f} L\n"
            "⛽️➕ Refueled: {refuel_added:.1f} L"
        ),
    },
    "ru": {
        "access_denied": "❗️Доступ запрещен.\nУ вас нет прав для использования этого бота.",
        "admin_only": "❗️Только администратор.",
        "settings_header": "Настройки:",
        "settings_line": "{setting_key}={value}",
        "settings_usage": "Использование: /set <KEY> <VALUE>\nКлючи: {keys}",
        "settings_invalid_key": "Неверный ключ. Ключи: {keys}",
        "settings_invalid_value": "Неверное значение для {setting_key}.",
        "settings_updated": "{setting_key} обновлен на {value}.",
        "settings_env_missing": "Предупреждение: .env не обновлен; изменение действует только до перезапуска.",
        "usage_allow": "❕Использование: /allow <user_id>",
        "usage_deny": "❕Использование: /deny <user_id>",
        "invalid_user_id": "❕Некорректный user_id.",
        "allow_added": "❕Пользователь {user_id} добавлен в белый список.",
        "deny_removed": "❕Пользователь {user_id} удален из белого списка.",
        "whoami": "❕Ваш ID: {user_id}{username_line}",
        "username_line": "\nИмя пользователя: @{username}",
        "refuel_history_usage": "❕Использование: /rhistory <days>",
        "refuel_history_invalid_days": "❕Некорректное число дней.",
        "refuel_history_empty": "❕Заправок за последние {days} дн. нет.",
        "refuel_history_header": "❕История заправок (последние {days} дн.):",
        "refuel_history_line": "{time} | {action} | {before:.1f} -> {after:.1f} | {user}",
        "refuel_history_action_add": "+{amount:.1f} л",
        "refuel_history_action_reset": "❕СБРОС",
        "history_usage": "❕Использование: /history [days]\nПример: /history 7",
        "history_empty": "❕Генератор не работал последние {days} дн.",
        "history_header": "❕История генератора (последние {days} дн.):",
        "history_line": "{start} -> {stop}\n  ⏱️Время работы: {hours}ч {minutes}м\n  ⛽️🔽 Топлива израсходовано: {fuel:.1f} л",
        "refuel_table_cols": "ВРЕМЯ|ДЕЙСТВИЕ|БЫЛО|СТАЛО|ПОЛЬЗ.",
        "history_table_cols": "СТАРТ|СТОП|ВРЕМЯ|ТОПЛ(Л)",
        "history_table_run_format": "{hours}ч {minutes:02d}м",
        "report_link": "Отчет: {link}",
        "open_bot_button": "Открыть бота",
        "whitelist_empty": "❕Белый список пуст.",
        "whitelist_header": "❕Разрешенные пользователи:",
        "whitelist_line": "{user_id} | {username} | добавлен: {added_at}",
        "unknown_user": "не задан",
        "not_available": "н/д",
        "bot_restarted": "Бот генератора перезапущен\nВремя: {time}",
        "state_running": "🌀РАБОТАЕТ",
        "state_stopped": "❌ОСТАНОВЛЕН",
        "status": (
            "❕СТАТУС: {generator}\n\n"
            "Состояние: {state}\n"
            "⛽️Топлива осталось: {fuel_left:.1f} л\n\n"
            "⏳Оценка работы: {remaining_time}\n\n"
            "Последние 24 часа:\n"
            "  ⏱️Время работы: {day_hours}ч {day_minutes}м\n"
            "  ⛽️🔽 Расход: {day_fuel:.1f} л\n\n"
            "Последние 7 дней:\n"
            "  ⏱️Время работы: {week_hours}ч {week_minutes}м\n"
            "  ⛽️🔽 Расход: {week_fuel:.1f} л"
        ),
        "motohours_line": "Моточасы: {total_hours}ч {total_minutes}м",
        "service_not_set_line": "Сервис не задан (используйте /setservice X)",
        "service_remaining_line": "Сервис через: {hours}ч {minutes}м",
        "service_overdue_line": "Просрочка сервиса: {hours}ч {minutes}м",
        "service_due_alert": (
            "❗️СЕРВИС: {generator}\n"
            "Моточасы: {total_hours}ч {total_minutes}м\n"
            "Запланируйте обслуживание и задайте следующее через /setservice X"
        ),
        "setservice_usage": "Использование: /setservice <часы>\nПример: /setservice 100",
        "setmhours_usage": "Использование: /setmhours <часы>\nПример: /setmhours 123.5",
        "setmhours_invalid_value": "Некорректное значение часов.",
        "setmhours_done": "Моточасы установлены на {hours} ч.",
        "setservice_invalid_value": "Некорректное значение часов.",
        "setservice_done": "Следующее обслуживание через {hours} ч.",
        "setservice_cleared": "Напоминание о сервисе сброшено.",
        "refuel_usage": "❕Использование: /refuel <liters>",
        "refuel_invalid_amount": "❕Некорректное количество топлива.",
        "refuel_saved": (
            "❕Заправка сохранена\n"
            "🔄Добавлено: {amount:.1f} л\n"
            "⛽️Топлива в баке: {fuel_after:.1f} / {capacity:.1f} л\n"
            "👨🏻‍🦱Внесено: {user}"
        ),
        "reset_usage": "❕Использование: /reset_fuel <liters>",
        "reset_invalid": "❕Некорректное значение топлива.",
        "reset_overflow": "❕Значение топлива превышает объем бака ({capacity:.1f} л).",
        "reset_done": (
            "❕Уровень топлива сброшен\n"
            "🔄Новый уровень: {fuel_after:.1f} / {capacity:.1f} л\n"
            "👨🏻‍🦱Внесено: {user}"
        ),
        "low_fuel_alert": (
            "❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️\n"
            "❗️ Низкий уровень топлива для {generator}\n"
            "⛽️Остаток (оценка): {fuel_left:.1f} л\n"
            "⏳Оставшееся время: {remaining_time}\n"
            "⚠️Порог: < {threshold:.2f} ч"
        ),
        "generator_started": (
            "{generator} ЗАПУЩЕН\n"
            "⛽️Топлива: {fuel_left:.1f} л\n"
            "⏳Оставшееся время: {remaining_time}"
        ),
        "generator_stopped": (
            "{generator} ОСТАНОВЛЕН\n"
            "⏱️Время работы: {runtime_minutes} мин\n"
            "⛽️🔽 Расход: {fuel_used:.1f} л\n"
            "⛽️Остаток: {fuel_left:.1f} л\n"
            "⏳Оставшееся время: {remaining_time}"
        ),
        "help": (
            "Бот мониторинга генератора\n\n"
            "Доступные команды:\n\n"
            "/status\n"
            "  Текущий статус генератора\n"
            "  Уровень топлива и оставшееся время работы\n"
            "  Статистика за 24 часа и 7 дней\n\n"
            "/history [days]\n"
            "  История запусков/остановок и расхода топлива\n"
            "  По умолчанию: 1 день\n"
            "  Пример: /history 7\n\n"
            "/refuel <liters>\n"
            "  Добавить топливо\n"
            "  Пример: /refuel 50\n\n"
            "/rhistory <days>\n"
            "  История заправок/сбросов\n"
            "  Пример: /rhistory 7\n\n"
            "/reset_fuel <liters>\n"
            "  Принудительно установить уровень топлива\n"
            "  Пример: /reset_fuel 190\n\n"
            "/help\n"
            "  Показать это сообщение\n\n"
            "/month\n"
            "  Показать отчет за прошлый месяц\n\n"
            "/setservice <часы>\n"
            "  Задать следующее обслуживание через X часов работы\n"
            "  /setservice 0 для сброса напоминания\n\n"
            "Только для админа:\n"
            "/allow <user_id>\n"
            "  Добавить в белый список\n"
            "/deny <user_id>\n"
            "  Убрать из белого списка\n"
            "/users\n"
            "  Список белого списка\n"
            "/whoami\n"
            "  Показать свой ID\n\n"
            "/settings\n"
            "  Просмотр текущих настроек\n"
            "/set <KEY> <VALUE>\n"
            "  Изменить настройку в .env и в памяти\n"
            "/setmhours <часы>\n"
            "  Корректировка общих моточасов\n"
        ),
        "daily_report_running": (
            "📊ЕЖЕДНЕВНЫЙ ОТЧЕТ: {generator}\n\n"
            "🗓Дата: {date}\n\n"
            "⚡️Генератор работал\n\n"
            "⏱️Время работы: {runtime_hours}ч {runtime_minutes}м\n"
            "⛽️🔽 Расход: {fuel_used:.1f} л\n\n"
            "⛽️Остаток: {fuel_left:.1f} л\n"
            "⏳Оставшееся время: {remaining_time}"
        ),
        "daily_report_idle": (
            "📊ЕЖЕДНЕВНЫЙ ОТЧЕТ: {generator}\n\n"
            "🗓Дата: {date}\n\n"
            "💤Генератор не работал за последние 24ч\n\n"
            "⛽️Остаток: {fuel_left:.1f} л\n"
            "⏳Оставшееся время: {remaining_time}"
        ),
        "monthly_report": (
            "📅ЕЖЕМЕСЯЧНЫЙ ОТЧЕТ: {generator}\n\n"
            "Месяц: {month}\n\n"
            "⏱️Время работы: {runtime_hours}ч {runtime_minutes}м\n"
            "⛽️🔽 Расход: {fuel_used:.1f} л\n"
            "⛽️➕ Заправлено: {refuel_added:.1f} л"
        ),
    },
}


def _normalize_lang(lang: str | None) -> str:
    lang_code = (lang or DEFAULT_LANGUAGE or "en").lower()
    return lang_code if lang_code in MESSAGES else "en"


def t(key: str, *, lang: str | None = None, **kwargs) -> str:
    lang_code = _normalize_lang(lang)
    template = MESSAGES.get(lang_code, {}).get(key) or MESSAGES["en"].get(key, key)
    try:
        return template.format(**kwargs)
    except Exception:
        return template
