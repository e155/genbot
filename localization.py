import os

DEFAULT_LANGUAGE = os.getenv("LANGUAGE", "en").lower()

MESSAGES = {
    "en": {
        "access_denied": "Access denied.\nYou are not authorized to use this bot.",
        "admin_only": "Admin only.",
        "usage_allow": "Usage: /allow <user_id>",
        "usage_deny": "Usage: /deny <user_id>",
        "invalid_user_id": "Invalid user_id.",
        "allow_added": "User {user_id} added to whitelist.",
        "deny_removed": "User {user_id} removed from whitelist.",
        "whoami": "Your ID: {user_id}{username_line}",
        "username_line": "\nUsername: @{username}",
        "refuel_history_usage": "Usage: /rhistory <days>",
        "refuel_history_invalid_days": "Invalid number of days.",
        "refuel_history_empty": "No refuel records for last {days} days.",
        "refuel_history_header": "Refuel history (last {days} days):",
        "refuel_history_line": "{time} | {action} | {before:.1f} -> {after:.1f} | {user}",
        "refuel_history_action_add": "+{amount:.1f} L",
        "refuel_history_action_reset": "RESET",
        "history_usage": "Usage: /history [days]\nExample: /history 7",
        "history_empty": "No generator activity for last {days} day(s).",
        "history_header": "Generator history (last {days} day(s)):",
        "history_line": "{start} -> {stop}\n  Runtime: {hours}h {minutes}m\n  Fuel used: {fuel:.1f} L",
        "open_bot_button": "Open bot",
        "whitelist_empty": "Whitelist is empty.",
        "whitelist_header": "Allowed users:",
        "whitelist_line": "{user_id} | {username} | added: {added_at}",
        "unknown_user": "N/A",
        "not_available": "N/A",
        "bot_restarted": "Generator bot restarted\nTime: {time}",
        "state_running": "RUNNING",
        "state_stopped": "STOPPED",
        "status": (
            "STATUS: {generator}\n\n"
            "State: {state}\n"
            "Fuel left: {fuel_left:.1f} L\n\n"
            "Estimated runtime: {remaining_time}\n\n"
            "Last 24h:\n"
            "  Runtime: {day_hours}h {day_minutes}m\n"
            "  Fuel used: {day_fuel:.1f} L\n\n"
            "Last 7 days:\n"
            "  Runtime: {week_hours}h {week_minutes}m\n"
            "  Fuel used: {week_fuel:.1f} L"
        ),
        "refuel_usage": "Usage: /refuel <liters>",
        "refuel_invalid_amount": "Invalid fuel amount.",
        "refuel_saved": (
            "Refuel recorded\n"
            "Added: {amount:.1f} L\n"
            "Fuel level: {fuel_after:.1f} / {capacity:.1f} L\n"
            "By: {user}"
        ),
        "reset_usage": "Usage: /reset_fuel <liters>",
        "reset_invalid": "Invalid fuel value.",
        "reset_overflow": "Fuel value exceeds tank capacity ({capacity:.1f} L).",
        "reset_done": (
            "Fuel level RESET\n"
            "New level: {fuel_after:.1f} / {capacity:.1f} L\n"
            "By: {user}"
        ),
        "low_fuel_alert": (
            "[ALERT] Low fuel for {generator}\n"
            "Fuel left (est.): {fuel_left:.1f} L\n"
            "Estimated runtime: {remaining_time}\n"
            "Threshold: < {threshold:.2f} h"
        ),
        "generator_started": (
            "{generator} STARTED\n"
            "Fuel left: {fuel_left:.1f} L\n"
            "Estimated runtime: {remaining_time}"
        ),
        "generator_stopped": (
            "{generator} STOPPED\n"
            "Runtime: {runtime_minutes} min\n"
            "Fuel used: {fuel_used:.1f} L\n"
            "Fuel left: {fuel_left:.1f} L\n"
            "Estimated runtime: {remaining_time}"
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
            "  Show this help message"
        ),
        "daily_report_running": (
            "DAILY REPORT: {generator}\n\n"
            "Date: {date}\n\n"
            "Generator was RUNNING\n\n"
            "Runtime: {runtime_hours}h {runtime_minutes}m\n"
            "Fuel used: {fuel_used:.1f} L\n\n"
            "Fuel left: {fuel_left:.1f} L\n"
            "Estimated runtime: {remaining_time}"
        ),
        "daily_report_idle": (
            "DAILY REPORT: {generator}\n\n"
            "Date: {date}\n\n"
            "Generator was NOT running in last 24h\n\n"
            "Fuel left: {fuel_left:.1f} L\n"
            "Estimated runtime: {remaining_time}"
        ),
    },
    "ru": {
        "access_denied": "Доступ запрещен.\nУ вас нет прав для использования этого бота.",
        "admin_only": "Только администратор.",
        "usage_allow": "Использование: /allow <user_id>",
        "usage_deny": "Использование: /deny <user_id>",
        "invalid_user_id": "Некорректный user_id.",
        "allow_added": "Пользователь {user_id} добавлен в белый список.",
        "deny_removed": "Пользователь {user_id} удален из белого списка.",
        "whoami": "Ваш ID: {user_id}{username_line}",
        "username_line": "\nИмя пользователя: @{username}",
        "refuel_history_usage": "Использование: /rhistory <days>",
        "refuel_history_invalid_days": "Некорректное число дней.",
        "refuel_history_empty": "Заправок за последние {days} дн. нет.",
        "refuel_history_header": "История заправок (последние {days} дн.):",
        "refuel_history_line": "{time} | {action} | {before:.1f} -> {after:.1f} | {user}",
        "refuel_history_action_add": "+{amount:.1f} л",
        "refuel_history_action_reset": "СБРОС",
        "history_usage": "Использование: /history [days]\nПример: /history 7",
        "history_empty": "Генератор не работал последние {days} дн.",
        "history_header": "История генератора (последние {days} дн.):",
        "history_line": "{start} -> {stop}\n  Время работы: {hours}ч {minutes}м\n  Топлива израсходовано: {fuel:.1f} л",
        "open_bot_button": "Открыть бота",
        "whitelist_empty": "Белый список пуст.",
        "whitelist_header": "Разрешенные пользователи:",
        "whitelist_line": "{user_id} | {username} | добавлен: {added_at}",
        "unknown_user": "не задан",
        "not_available": "н/д",
        "bot_restarted": "Бот генератора перезапущен\nВремя: {time}",
        "state_running": "РАБОТАЕТ",
        "state_stopped": "ОСТАНОВЛЕН",
        "status": (
            "СТАТУС: {generator}\n\n"
            "Состояние: {state}\n"
            "Топлива осталось: {fuel_left:.1f} л\n\n"
            "Оценка работы: {remaining_time}\n\n"
            "Последние 24 часа:\n"
            "  Время работы: {day_hours}ч {day_minutes}м\n"
            "  Расход: {day_fuel:.1f} л\n\n"
            "Последние 7 дней:\n"
            "  Время работы: {week_hours}ч {week_minutes}м\n"
            "  Расход: {week_fuel:.1f} л"
        ),
        "refuel_usage": "Использование: /refuel <liters>",
        "refuel_invalid_amount": "Некорректное количество топлива.",
        "refuel_saved": (
            "Заправка сохранена\n"
            "Добавлено: {amount:.1f} л\n"
            "Уровень: {fuel_after:.1f} / {capacity:.1f} л\n"
            "Пользователь: {user}"
        ),
        "reset_usage": "Использование: /reset_fuel <liters>",
        "reset_invalid": "Некорректное значение топлива.",
        "reset_overflow": "Значение топлива превышает объем бака ({capacity:.1f} л).",
        "reset_done": (
            "Уровень топлива сброшен\n"
            "Новый уровень: {fuel_after:.1f} / {capacity:.1f} л\n"
            "Пользователь: {user}"
        ),
        "low_fuel_alert": (
            "[ALERT] Низкий уровень топлива для {generator}\n"
            "Остаток (оценка): {fuel_left:.1f} л\n"
            "Оставшееся время: {remaining_time}\n"
            "Порог: < {threshold:.2f} ч"
        ),
        "generator_started": (
            "{generator} ЗАПУЩЕН\n"
            "Топлива: {fuel_left:.1f} л\n"
            "Оставшееся время: {remaining_time}"
        ),
        "generator_stopped": (
            "{generator} ОСТАНОВЛЕН\n"
            "Время работы: {runtime_minutes} мин\n"
            "Расход: {fuel_used:.1f} л\n"
            "Остаток: {fuel_left:.1f} л\n"
            "Оставшееся время: {remaining_time}"
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
            "  Показать это сообщение"
        ),
        "daily_report_running": (
            "ЕЖЕДНЕВНЫЙ ОТЧЕТ: {generator}\n\n"
            "Дата: {date}\n\n"
            "Генератор работал\n\n"
            "Время работы: {runtime_hours}ч {runtime_minutes}м\n"
            "Расход: {fuel_used:.1f} л\n\n"
            "Остаток: {fuel_left:.1f} л\n"
            "Оставшееся время: {remaining_time}"
        ),
        "daily_report_idle": (
            "ЕЖЕДНЕВНЫЙ ОТЧЕТ: {generator}\n\n"
            "Дата: {date}\n\n"
            "Генератор не работал за последние 24ч\n\n"
            "Остаток: {fuel_left:.1f} л\n"
            "Оставшееся время: {remaining_time}"
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
