# -*- coding: utf-8 -*-
import asyncio
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import urllib.parse
import urllib.request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from settings import (
    TOKEN,
    CHANNELID,
    GENERATORNAME,
    GENERATORADDR,
    INTERVAL,
    REPORTH,
    REPORTM,
    TANK_CAPACITY,
    FUEL_CONSUMPTION,
    INITIAL_FUEL,
    DB_FILE,
    LOW_FUEL_HOURS,
    ADMIN_USER_ID,
    BOTURL,
    TELEGRAPH_TOKEN,
    TELEGRAPH_AUTHOR
)

import localization as localization_module
from localization import t

SETTINGS_ORDER = [
    "LANGUAGE",
    "GENERATORNAME",
    "GENERATORADDR",
    "INTERVAL",
    "REPORTH",
    "REPORTM",
    "TANK_CAPACITY",
    "FUEL_CONSUMPTION",
    "LOW_FUEL_HOURS",
]

SETTINGS_STR_KEYS = {"LANGUAGE", "GENERATORNAME", "GENERATORADDR"}
SETTINGS_INT_KEYS = {"INTERVAL", "REPORTH", "REPORTM", "TANK_CAPACITY"}
SETTINGS_FLOAT_KEYS = {"FUEL_CONSUMPTION", "LOW_FUEL_HOURS"}


def _format_env_value(key: str, value) -> str:
    if key in SETTINGS_STR_KEYS:
        value_str = str(value)
        escaped = value_str.replace("\\", "\\\\").replace('"', "\\\"")
        return f"\"{escaped}\""
    return str(value)


def _update_env_file(key: str, value_str: str) -> bool:
    env_path = ".env"
    if not os.path.exists(env_path):
        return False

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    replaced = False
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}={value_str}\n"
            replaced = True

    if not replaced:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"
        lines.append(f"{key}={value_str}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


def _mdv2_codeblock_table(rows: list[list[str]]) -> str:
    # MarkdownV2 code block; avoid backticks to keep formatting intact.
    safe_lines = [" ".join(cell.replace("`", "'") for cell in row) for row in rows]
    return "```\n" + "\n".join(safe_lines) + "\n```"


_MDV2_ESCAPE_RE = re.compile(r"([_*[\]()~`>#+\-=|{}.!])")
_telegraph_token = TELEGRAPH_TOKEN


def _mdv2_escape(text: str) -> str:
    return _MDV2_ESCAPE_RE.sub(r"\\\1", text)


def _clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[:width]


def _table_header_row(key: str, widths: list[int], defaults: list[str]) -> list[str]:
    raw = t(key)
    cols = raw.split("|")
    if len(cols) != len(widths):
        cols = defaults
    return [f"{_clip(col.strip(), width):<{width}}" for col, width in zip(cols, widths)]


def _table_text(rows: list[list[str]]) -> str:
    return "\n".join(" ".join(row) for row in rows)


def _mdv2_link(text: str, url: str) -> str:
    safe_url = url.replace("(", "%28").replace(")", "%29")
    return f"[{_mdv2_escape(text)}]({safe_url})"


def _telegraph_call(method: str, params: dict) -> dict | None:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(f"https://api.telegra.ph/{method}", data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if not payload.get("ok"):
        return None
    return payload.get("result")


def _telegraph_get_token() -> str | None:
    global _telegraph_token
    if _telegraph_token:
        return _telegraph_token
    short_name = "genbot"
    author_name = TELEGRAPH_AUTHOR or GENERATORNAME or "Generator Bot"
    result = _telegraph_call(
        "createAccount",
        {"short_name": short_name, "author_name": author_name, "author_url": BOTURL or ""},
    )
    if not result:
        return None
    _telegraph_token = result.get("access_token")
    return _telegraph_token


def _create_telegraph_page(title: str, table_text: str) -> str | None:
    token = _telegraph_get_token()
    if not token:
        return None
    content = json.dumps([{"tag": "pre", "children": [table_text]}], ensure_ascii=True)
    result = _telegraph_call(
        "createPage",
        {
            "access_token": token,
            "title": title,
            "author_name": TELEGRAPH_AUTHOR or GENERATORNAME or "Generator Bot",
            "author_url": BOTURL or "",
            "content": content,
            "return_content": "false",
        },
    )
    if not result:
        return None
    return result.get("url")


def _get_setting_value(key: str):
    if key == "LANGUAGE":
        return localization_module.DEFAULT_LANGUAGE
    if key == "GENERATORNAME":
        return GENERATORNAME
    if key == "GENERATORADDR":
        return GENERATORADDR
    if key == "INTERVAL":
        return INTERVAL
    if key == "REPORTH":
        return REPORTH
    if key == "REPORTM":
        return REPORTM
    if key == "TANK_CAPACITY":
        return TANK_CAPACITY
    if key == "FUEL_CONSUMPTION":
        return FUEL_CONSUMPTION
    if key == "LOW_FUEL_HOURS":
        return LOW_FUEL_HOURS
    return None


def _parse_setting_value(key: str, raw_value: str):
    value = raw_value.strip()
    if key == "LANGUAGE":
        lang = value.lower()
        if lang not in {"en", "ru"}:
            return None
        return lang
    if key in SETTINGS_STR_KEYS:
        return value
    if key in SETTINGS_INT_KEYS:
        try:
            val = int(value)
        except ValueError:
            return None
        if key == "INTERVAL" and val <= 0:
            return None
        if key == "TANK_CAPACITY" and val <= 0:
            return None
        if key == "REPORTH" and not (0 <= val <= 23):
            return None
        if key == "REPORTM" and not (0 <= val <= 59):
            return None
        return val
    if key in SETTINGS_FLOAT_KEYS:
        try:
            val = float(value)
        except ValueError:
            return None
        if key == "FUEL_CONSUMPTION" and val <= 0:
            return None
        if key == "LOW_FUEL_HOURS" and val < 0:
            return None
        return val
    return None


def _apply_setting_value(key: str, value, context: ContextTypes.DEFAULT_TYPE):
    global GENERATORNAME, GENERATORADDR, INTERVAL, REPORTH, REPORTM
    global TANK_CAPACITY, FUEL_CONSUMPTION, LOW_FUEL_HOURS
    global HELP_TEXT

    if key == "LANGUAGE":
        localization_module.DEFAULT_LANGUAGE = str(value).lower()
        HELP_TEXT = t("help")
    elif key == "GENERATORNAME":
        GENERATORNAME = str(value)
    elif key == "GENERATORADDR":
        GENERATORADDR = str(value)
    elif key == "INTERVAL":
        INTERVAL = int(value)
    elif key == "REPORTH":
        REPORTH = int(value)
    elif key == "REPORTM":
        REPORTM = int(value)
    elif key == "TANK_CAPACITY":
        TANK_CAPACITY = int(value)
    elif key == "FUEL_CONSUMPTION":
        FUEL_CONSUMPTION = float(value)
    elif key == "LOW_FUEL_HOURS":
        LOW_FUEL_HOURS = float(value)

    os.environ[key] = str(value)

    if key == "INTERVAL":
        job_queue = context.application.job_queue
        for job in job_queue.get_jobs_by_name("monitor"):
            job.schedule_removal()
        job_queue.run_repeating(
            monitor_job,
            interval=INTERVAL,
            first=0,
            name="monitor"
        )

    if key in {"REPORTH", "REPORTM"}:
        job_queue = context.application.job_queue
        for job in job_queue.get_jobs_by_name("daily_report"):
            job.schedule_removal()
        job_queue.run_daily(
            daily_report,
            time=dt.time(hour=REPORTH, minute=REPORTM),
            name="daily_report"
        )
        for job in job_queue.get_jobs_by_name("monthly_report"):
            job.schedule_removal()
        job_queue.run_daily(
            monthly_report,
            time=dt.time(hour=REPORTH, minute=REPORTM),
            name="monthly_report"
        )

# ================= DATABASE =================

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS generator_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            stop_time TEXT,
            runtime_seconds INTEGER,
            fuel_used REAL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS refuel_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            amount REAL,
            fuel_before REAL,
            fuel_after REAL,
            user_id INTEGER,
            username TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            added_at TEXT
        )
        """)

def is_user_allowed(user_id: int) -> bool:
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (user_id,)
        )
        return cur.fetchone() is not None


def add_user_to_whitelist(user_id: int, username: str | None):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (user_id, username, added_at)
            VALUES (?, ?, ?)
        """, (
            user_id,
            username,
            dt.datetime.now().isoformat()
        ))


def remove_user_from_whitelist(user_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "DELETE FROM users WHERE user_id = ?",
            (user_id,)
        )

def whitelist_required(handler):
    async def wrapper(update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if not user:
            return

        if not is_user_allowed(user.id):
            await update.message.reply_text(t("access_denied"))
            return

        return await handler(update, context)

    return wrapper

def get_whitelist_users():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("""
            SELECT user_id, username, added_at
            FROM users
            ORDER BY added_at ASC
        """)
        return cur.fetchall()


#===allow id ====
async def allow_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    if not context.args:
        await update.message.reply_text(t("usage_allow"))
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t("invalid_user_id"))
        return

    add_user_to_whitelist(uid, None)
    await update.message.reply_text(t("allow_added", user_id=uid))

#===deny id ====
async def deny_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    if not context.args:
        await update.message.reply_text(t("usage_deny"))
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text(t("invalid_user_id"))
        return

    remove_user_from_whitelist(uid)
    await update.message.reply_text(t("deny_removed", user_id=uid))

#===my id ====

async def whoami_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username_line = (
        t("username_line", username=user.username) if user.username else ""
    )
    await update.message.reply_text(
        t("whoami", user_id=user.id, username_line=username_line)
    )


def get_state(key, default=None):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "SELECT value FROM state WHERE key = ?",
            (key,)
        )
        row = cur.fetchone()
        return row[0] if row else default

def set_state(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (key, str(value))
        )

# ================= ICMP =================

def ping(host: str) -> bool:
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0

# ================= FUEL =================

def fuel_used(seconds: int) -> float:
    return (seconds / 3600.0) * FUEL_CONSUMPTION


# ================= Runtime remaining =================

def format_remaining_time(fuel_left: float) -> str:
    if FUEL_CONSUMPTION <= 0:
        return "N/A"

    total_minutes = int((fuel_left / FUEL_CONSUMPTION) * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    return f"{hours}h {minutes}m"

def remaining_hours_from_fuel(fuel_left: float) -> float:
    if FUEL_CONSUMPTION <= 0:
        return 1e9
    return max(0.0, fuel_left / FUEL_CONSUMPTION)

def _hours_minutes_from_seconds(seconds: int) -> tuple[int, int]:
    total_minutes = max(0, seconds) // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return hours, minutes

def get_total_runtime_seconds(now: dt.datetime | None = None) -> int:
    if now is None:
        now = dt.datetime.now()
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT SUM(runtime_seconds) FROM generator_log")
        row = cur.fetchone()
        total = int(row[0] or 0)
    if get_state("running", "0") == "1":
        total += get_used_since_start_seconds(now)
    return total

def get_service_due_seconds() -> float | None:
    raw = get_state("service_due_seconds")
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        return None

def _parse_iso(dt_str: str | None) -> dt.datetime | None:
    if not dt_str:
        return None
    try:
        return dt.datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def get_used_since_start_seconds(now: dt.datetime) -> int:
    start_dt = _parse_iso(get_state("start_time"))
    if not start_dt:
        return 0
    seconds = int((now - start_dt).total_seconds())
    if seconds < 0:
        seconds = 0
    return seconds


def get_fuel_start() -> float | None:
    val = get_state("fuel_start")
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def set_fuel_start(value: float) -> None:
    set_state("fuel_start", float(value))


def get_effective_fuel_left_now(now: dt.datetime | None = None) -> float:
    """
    Returns current fuel estimate.
    - If STOPPED: returns state.fuel_left
    - If RUNNING: returns max(0, fuel_start - used_since_start)
    """
    if now is None:
        now = dt.datetime.now()

    running = get_state("running", "0") == "1"
    fuel_left_db = float(get_state("fuel_left", INITIAL_FUEL))

    if not running:
        return fuel_left_db

    fuel_start = get_fuel_start()
    if fuel_start is None:
        # Migration/repair: if bot restarted while running and fuel_start missing
        fuel_start = fuel_left_db
        set_fuel_start(fuel_start)

    used = fuel_used(get_used_since_start_seconds(now))
    return max(0.0, fuel_start - used)


def apply_fuel_setpoint_while_running(new_effective_fuel: float, now: dt.datetime | None = None) -> None:
    """
    When RUNNING, we want the effective fuel (right now) to become new_effective_fuel.
    We keep start_time unchanged and adjust fuel_start so that:
      new_effective = fuel_start_new - used_since_start
      => fuel_start_new = new_effective + used_since_start
    """
    if now is None:
        now = dt.datetime.now()

    used = fuel_used(get_used_since_start_seconds(now))
    fuel_start_new = new_effective_fuel + used
    set_fuel_start(fuel_start_new)


# ================ Ref history ============
async def refuel_history_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(t("refuel_history_usage"))
        return

    try:
        days = int(context.args[0])
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("refuel_history_invalid_days"))
        return

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("""
            SELECT
                timestamp,
                amount,
                fuel_before,
                fuel_after,
                username
            FROM refuel_log
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp DESC
            LIMIT 10
        """, (f"-{days} days",))

        rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            t("refuel_history_empty", days=days)
        )
        return

    header_raw = t("refuel_history_header", days=days)
    header = _mdv2_escape(header_raw)
    widths = [16, 12, 7, 7, 12]
    table_rows = [
        _table_header_row(
            "refuel_table_cols",
            widths,
            ["TIME", "ACTION", "BEFORE", "AFTER", "USER"],
        )
    ]

    for ts, amount, before, after, user in rows:
        time_str = _clip(ts.replace("T", " ")[5:16], widths[0])
        action = (
            t("refuel_history_action_add", amount=amount)
            if amount > 0
            else t("refuel_history_action_reset")
        )
        action_s = _clip(action, widths[1])
        before_s = f"{before:>{widths[2]}.1f}"
        after_s = f"{after:>{widths[3]}.1f}"
        user_s = _clip(user or t("unknown_user"), widths[4])

        table_rows.append(
            [
                f"{time_str:<{widths[0]}}",
                f"{action_s:<{widths[1]}}",
                f"{before_s:>{widths[2]}}",
                f"{after_s:>{widths[3]}}",
                f"{user_s:<{widths[4]}}",
            ]
        )

    table_text = _table_text(table_rows)
    table = _mdv2_codeblock_table(table_rows)
    report_url = await asyncio.to_thread(_create_telegraph_page, header_raw, table_text)
    report_line = (
        f"\n{t('report_link', link=_mdv2_link('Telegraph', report_url))}"
        if report_url
        else ""
    )
    await update.message.reply_text(
        f"{header}\n{table}{report_line}",
        parse_mode="MarkdownV2",
    )

# ================= History =====================

async def history_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    # default: 1 day
    if not context.args:
        days = 1
    else:
        try:
            days = int(context.args[0])
            if days <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(t("history_usage"))
            return

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("""
            SELECT
                start_time,
                stop_time,
                runtime_seconds,
                fuel_used
            FROM generator_log
            WHERE start_time >= datetime('now', ?)
            ORDER BY start_time DESC
            LIMIT 10
        """, (f"-{days} days",))

        rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            t("history_empty", days=days)
        )
        return
    header_raw = t("history_header", days=days)
    header = _mdv2_escape(header_raw)
    widths = [16, 16, 9, 7]
    table_rows = [
        _table_header_row(
            "history_table_cols",
            widths,
            ["START", "STOP", "RUN", "FUEL(L)"],
        )
    ]

    for start, stop, runtime, fuel in rows:
        start_s = _clip(start.replace("T", " ")[:16], widths[0])
        stop_s = _clip(stop.replace("T", " ")[:16], widths[1]) if stop else _clip(
            t("not_available"), widths[1]
        )

        hours = runtime // 3600
        minutes = (runtime % 3600) // 60
        run_s = _clip(
            t("history_table_run_format", hours=hours, minutes=minutes),
            widths[2],
        )
        fuel_s = f"{fuel:>{widths[3]}.1f}"

        table_rows.append(
            [
                f"{start_s:<{widths[0]}}",
                f"{stop_s:<{widths[1]}}",
                f"{run_s:<{widths[2]}}",
                f"{fuel_s:>{widths[3]}}",
            ]
        )

    table_text = _table_text(table_rows)
    table = _mdv2_codeblock_table(table_rows)
    report_url = await asyncio.to_thread(_create_telegraph_page, header_raw, table_text)
    report_line = (
        f"\n{t('report_link', link=_mdv2_link('Telegraph', report_url))}"
        if report_url
        else ""
    )
    await update.message.reply_text(
        f"{header}\n{table}{report_line}",
        parse_mode="MarkdownV2",
    )


# ================= TELEGRAM =================

async def send(app: Application, text: str):
    await app.bot.send_message(
        chat_id=CHANNELID,
        text=text,
        reply_markup=bot_link_keyboard()
    )

def bot_link_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("open_bot_button"), url=BOTURL)]
    ])

async def users_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    rows = get_whitelist_users()

    if not rows:
        await update.message.reply_text(t("whitelist_empty"))
        return

    lines = [t("whitelist_header")]

    for uid, username, added_at in rows:
        date = added_at.replace("T", " ")[:16] if added_at else t("not_available")
        name = f"@{username}" if username else t("unknown_user")
        lines.append(t("whitelist_line", user_id=uid, username=name, added_at=date))

    await update.message.reply_text("\n".join(lines))


async def settings_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    lines = [t("settings_header")]

    for key in SETTINGS_ORDER:
        value = _get_setting_value(key)
        lines.append(t("settings_line", setting_key=key, value=value))

    await update.message.reply_text("\n".join(lines))


async def set_setting_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            t("settings_usage", keys=", ".join(SETTINGS_ORDER))
        )
        return

    key = context.args[0].upper()
    if key not in SETTINGS_ORDER:
        await update.message.reply_text(
            t("settings_invalid_key", keys=", ".join(SETTINGS_ORDER))
        )
        return

    raw_value = " ".join(context.args[1:]).strip()
    parsed = _parse_setting_value(key, raw_value)
    if parsed is None:
        await update.message.reply_text(
            t("settings_invalid_value", setting_key=key)
        )
        return

    _apply_setting_value(key, parsed, context)

    try:
        env_value = _format_env_value(key, parsed)
        updated = _update_env_file(key, env_value)
    except Exception:
        updated = False

    message = t("settings_updated", setting_key=key, value=parsed)
    if not updated:
        message = f"{message}\n{t('settings_env_missing')}"
    await update.message.reply_text(message)


# ================= STATS =================

def get_stats(hours: int):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("""
            SELECT
                SUM(runtime_seconds),
                SUM(fuel_used)
            FROM generator_log
            WHERE start_time >= datetime('now', ?)
        """, (f"-{hours} hours",))
        row = cur.fetchone()
        return row[0] or 0, row[1] or 0


def get_month_range(now: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    if now.month == 1:
        start = dt.datetime(now.year - 1, 12, 1)
    else:
        start = dt.datetime(now.year, now.month - 1, 1)
    end = dt.datetime(now.year, now.month, 1)
    return start, end


def get_monthly_stats(start: dt.datetime, end: dt.datetime) -> tuple[int, float, float]:
    start_iso = start.isoformat()
    end_iso = end.isoformat()

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("""
            SELECT
                SUM(runtime_seconds),
                SUM(fuel_used)
            FROM generator_log
            WHERE start_time >= ? AND start_time < ?
        """, (start_iso, end_iso))
        row = cur.fetchone()
        runtime = row[0] or 0
        fuel_used = row[1] or 0.0

        cur = conn.execute("""
            SELECT
                SUM(amount)
            FROM refuel_log
            WHERE timestamp >= ? AND timestamp < ? AND amount > 0
        """, (start_iso, end_iso))
        row = cur.fetchone()
        refuel_added = row[0] or 0.0

    return runtime, fuel_used, refuel_added

# ================= restart msg =================
async def startup_message(app: Application):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await app.bot.send_message(
        chat_id=CHANNELID,
        text=t("bot_restarted", time=now)
    )


# ================= COMMANDS =================

async def status_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    now = dt.datetime.now()
    fuel_left = get_effective_fuel_left_now(now)
    remaining_time = format_remaining_time(fuel_left)
    running = get_state("running", "0") == "1"

    day_runtime, day_fuel = get_stats(24)
    week_runtime, week_fuel = get_stats(24 * 7)
    total_runtime = get_total_runtime_seconds(now)
    total_h, total_m = _hours_minutes_from_seconds(total_runtime)

    due_seconds = get_service_due_seconds()
    if due_seconds is None:
        service_line = t("service_not_set_line")
    else:
        remaining = int(due_seconds - total_runtime)
        if remaining > 0:
            rem_h, rem_m = _hours_minutes_from_seconds(remaining)
            service_line = t("service_remaining_line", hours=rem_h, minutes=rem_m)
        else:
            overdue_h, overdue_m = _hours_minutes_from_seconds(-remaining)
            service_line = t("service_overdue_line", hours=overdue_h, minutes=overdue_m)

    state_label = t("state_running") if running else t("state_stopped")

    msg = t(
        "status",
        generator=GENERATORNAME,
        state=state_label,
        fuel_left=fuel_left,
        remaining_time=remaining_time,
        day_hours=day_runtime // 3600,
        day_minutes=(day_runtime % 3600) // 60,
        day_fuel=day_fuel,
        week_hours=week_runtime // 3600,
        week_minutes=(week_runtime % 3600) // 60,
        week_fuel=week_fuel,
    )

    msg = (
        f"{msg}\n\n"
        f"{t('motohours_line', total_hours=total_h, total_minutes=total_m)}\n"
        f"{service_line}"
    )

    await update.message.reply_text(msg)

@whitelist_required
async def refuel_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(t("refuel_usage"))
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("refuel_invalid_amount"))
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    now = dt.datetime.now()
    running = get_state("running", "0") == "1"

    fuel_before = get_effective_fuel_left_now(now)
    fuel_after = min(TANK_CAPACITY, fuel_before + amount)

    if running:
       # Adjust fuel_start so that effective fuel NOW becomes fuel_after
        apply_fuel_setpoint_while_running(fuel_after, now)
    else:
        set_state("fuel_left", fuel_after)

    # allow alert to trigger again after refuel
    set_state("low_fuel_alerted", 0)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO refuel_log (
              timestamp,
              amount,
              fuel_before,
              fuel_after,
              user_id,
              username
           ) VALUES (?, ?, ?, ?, ?, ?)
      """, (
        now.isoformat(),
        amount,
        fuel_before,
        fuel_after,
        user_id,
        username
    ))

    # allow alert to trigger again after refuel
    set_state("low_fuel_alerted", 0)


    await update.message.reply_text(
        t(
            "refuel_saved",
            amount=amount,
            fuel_after=fuel_after,
            capacity=TANK_CAPACITY,
            user=username,
        )
    )

@whitelist_required
async def reset_fuel_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(t("reset_usage"))
        return

    try:
        value = float(context.args[0])
        if value < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(t("reset_invalid"))
        return

    if value > TANK_CAPACITY:
        await update.message.reply_text(
            t("reset_overflow", capacity=TANK_CAPACITY)
        )
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    now = dt.datetime.now()
    running = get_state("running", "0") == "1"

    fuel_before = get_effective_fuel_left_now(now)
    fuel_after = value  # already validated <= TANK_CAPACITY

    if running:
       apply_fuel_setpoint_while_running(fuel_after, now)
    else:
        set_state("fuel_left", fuel_after)

    set_state("low_fuel_alerted", 0)

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO refuel_log (
                timestamp,
                amount,
                fuel_before,
                fuel_after,
                user_id,
                username
            ) VALUES (?, ?, ?, ?, ?, ?)
         """, (
            now.isoformat(),
            0.0,  # reset marker
            fuel_before,
            fuel_after,
            user_id,
            f"{username} (reset)"
    ))


    await update.message.reply_text(
        t(
            "reset_done",
            fuel_after=fuel_after,
            capacity=TANK_CAPACITY,
            user=username,
        )
    )


# ================= MONITOR =================
async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    running = get_state("running", "0") == "1"
    alive = ping(GENERATORADDR)
    now = dt.datetime.now()

    # Low-fuel alert (while running)
    if running:
        fuel_now = get_effective_fuel_left_now(now)
        rem_h = remaining_hours_from_fuel(fuel_now)

        alerted = get_state("low_fuel_alerted", "0") == "1"

        if (rem_h < LOW_FUEL_HOURS) and (not alerted):
            remaining_time = format_remaining_time(fuel_now)
            await send(
                context.application,
                t(
                    "low_fuel_alert",
                    generator=GENERATORNAME,
                    fuel_left=fuel_now,
                    remaining_time=remaining_time,
                    threshold=LOW_FUEL_HOURS,
                )
            )
            set_state("low_fuel_alerted", 1)

        if rem_h >= LOW_FUEL_HOURS:
            set_state("low_fuel_alerted", 0)

    # Service reminder
    due_seconds = get_service_due_seconds()
    if due_seconds is not None:
        total_runtime = get_total_runtime_seconds(now)
        alerted = get_state("service_alerted", "0") == "1"
        if (total_runtime >= due_seconds) and (not alerted):
            total_h, total_m = _hours_minutes_from_seconds(total_runtime)
            await send(
                context.application,
                t(
                    "service_due_alert",
                    generator=GENERATORNAME,
                    total_hours=total_h,
                    total_minutes=total_m,
                )
            )
            set_state("service_alerted", 1)

    # START
    if alive and not running:
        running = True
        start_time = now.isoformat()

        set_state("running", 1)
        set_state("start_time", start_time)

        fuel_left_db = float(get_state("fuel_left", INITIAL_FUEL))
        set_fuel_start(fuel_left_db)

        fuel_now = get_effective_fuel_left_now(now)
        remaining_time = format_remaining_time(fuel_now)

        await send(
            context.application,
            t(
                "generator_started",
                generator=GENERATORNAME,
                fuel_left=fuel_now,
                remaining_time=remaining_time,
            )
        )

    # STOP
    if (not alive) and running:
        stop_time = now

        seconds = get_used_since_start_seconds(now)
        used = fuel_used(seconds)

        fuel_start = get_fuel_start()
        if fuel_start is None:
            fuel_start = float(get_state("fuel_left", INITIAL_FUEL))

        fuel_left = max(0.0, fuel_start - used)
        remaining_time = format_remaining_time(fuel_left)

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                INSERT INTO generator_log
                (start_time, stop_time, runtime_seconds, fuel_used)
                VALUES (?, ?, ?, ?)
            """, (
                get_state("start_time"),
                stop_time.isoformat(),
                seconds,
                used
            ))

        set_state("running", 0)
        set_state("fuel_left", fuel_left)
        set_state("fuel_start", None)

        await send(
            context.application,
            t(
                "generator_stopped",
                generator=GENERATORNAME,
                runtime_minutes=seconds // 60,
                fuel_used=used,
                fuel_left=fuel_left,
                remaining_time=remaining_time,
            )
        )


# ================== HELP =================


HELP_TEXT = t("help")


async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


   
async def help_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def setservice_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text(t("admin_only"))
        return

    if not context.args:
        await update.message.reply_text(t("setservice_usage"))
        return

    raw_value = context.args[0]
    try:
        hours = float(raw_value)
    except ValueError:
        await update.message.reply_text(t("setservice_invalid_value"))
        return

    if hours < 0:
        await update.message.reply_text(t("setservice_invalid_value"))
        return

    if hours == 0:
        set_state("service_due_seconds", "")
        set_state("service_alerted", 0)
        await update.message.reply_text(t("setservice_cleared"))
        return

    total_runtime = get_total_runtime_seconds()
    due_seconds = total_runtime + int(hours * 3600)
    set_state("service_due_seconds", due_seconds)
    set_state("service_alerted", 0)

    await update.message.reply_text(
        t("setservice_done", hours=hours)
    )

async def month_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    now = dt.datetime.now()
    start, end = get_month_range(now)
    runtime, fuel_used, refuel_added = get_monthly_stats(start, end)

    month_label = start.strftime("%Y-%m")
    msg = t(
        "monthly_report",
        generator=GENERATORNAME,
        month=month_label,
        runtime_hours=runtime // 3600,
        runtime_minutes=(runtime % 3600) // 60,
        fuel_used=fuel_used,
        refuel_added=refuel_added,
    )

    await update.message.reply_text(msg)

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    app = context.application
    now = dt.datetime.now()

    runtime, fuel_used_24h = get_stats(24)

    fuel_left = get_effective_fuel_left_now(now)
    remaining_time = format_remaining_time(fuel_left)

    if runtime > 0:
        msg = t(
            "daily_report_running",
            generator=GENERATORNAME,
            date=now.strftime("%Y-%m-%d"),
            runtime_hours=runtime // 3600,
            runtime_minutes=(runtime % 3600) // 60,
            fuel_used=fuel_used_24h,
            fuel_left=fuel_left,
            remaining_time=remaining_time,
        )
    else:
        msg = t(
            "daily_report_idle",
            generator=GENERATORNAME,
            date=now.strftime("%Y-%m-%d"),
            fuel_left=fuel_left,
            remaining_time=remaining_time,
        )

    await send(app, msg)


async def monthly_report(context: ContextTypes.DEFAULT_TYPE):
    now = dt.datetime.now()
    if now.day != 1:
        return

    start, end = get_month_range(now)
    runtime, fuel_used, refuel_added = get_monthly_stats(start, end)

    month_label = start.strftime("%Y-%m")
    msg = t(
        "monthly_report",
        generator=GENERATORNAME,
        month=month_label,
        runtime_hours=runtime // 3600,
        runtime_minutes=(runtime % 3600) // 60,
        fuel_used=fuel_used,
        refuel_added=refuel_added,
    )

    await send(context.application, msg)



# ================= MAIN ==================
async def post_init(app: Application):
    await startup_message(app)
    # monitor loop
    app.job_queue.run_repeating(
        monitor_job,
        interval=INTERVAL,
        first=0,
        name="monitor"
    )

    # daily report
    app.job_queue.run_daily(
        daily_report,
        time=dt.time(hour=REPORTH, minute=REPORTM),
        name="daily_report"
    )
    # monthly report
    app.job_queue.run_daily(
        monthly_report,
        time=dt.time(hour=REPORTH, minute=REPORTM),
        name="monthly_report"
    )


def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("refuel", refuel_cmd))
    app.add_handler(CommandHandler("rhistory", refuel_history_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("reset_fuel", reset_fuel_cmd))
    app.add_handler(CommandHandler("allow", allow_cmd))
    app.add_handler(CommandHandler("deny", deny_cmd))
    app.add_handler(CommandHandler("whoami", whoami_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("set", set_setting_cmd))
    app.add_handler(CommandHandler("setservice", setservice_cmd))
    app.add_handler(CommandHandler("month", month_cmd))


    app.post_init = post_init
    app.run_polling()




if __name__ == "__main__":
    main()
