# -*- coding: utf-8 -*-
import asyncio
import datetime as dt
import sqlite3
import subprocess
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
    BOTURL
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
            await update.message.reply_text(
                "⛔ Access denied.\n"
                "You are not authorized to use this bot."
            )
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
        await update.message.reply_text("⛔ Admin only")
        return

    if not context.args:
        await update.message.reply_text("Usage: /allow <user_id>")
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user_id")
        return

    add_user_to_whitelist(uid, None)
    await update.message.reply_text(f"✅ User {uid} added to whitelist")

#===deny id ====
async def deny_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only")
        return

    if not context.args:
        await update.message.reply_text("Usage: /deny <user_id>")
        return

    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid user_id")
        return

    remove_user_from_whitelist(uid)
    await update.message.reply_text(f"❌ User {uid} removed from whitelist")

#===my id ====

async def whoami_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username_line = f"\nUsername: @{user.username}" if user.username else ""
    await update.message.reply_text(
        f"👤 Your ID: {user.id}{username_line}"
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
        await update.message.reply_text("Usage: /rhistory <days>")
        return

    try:
        days = int(context.args[0])
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid number of days")
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
            f"No refuel records for last {days} days"
        )
        return

    lines = [f"Refuel history (last {days} days):\n"]

    for ts, amount, before, after, user in rows:
        time_str = ts.replace("T", " ")[:16]
        if amount > 0:
            action = f"+{amount:.1f} L"
        else:
            action = "RESET"

        lines.append(
            f"{time_str} | {action} | "
            f"{before:.1f} → {after:.1f} | {user}"
)


    await update.message.reply_text("\n".join(lines))

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
            await update.message.reply_text(
                "Usage: /history [days]\nExample: /history 7"
            )
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
            f"❕No generator activity for last {days} day(s)"
        )
        return

    lines = [f"❕Generator history (last {days} day(s)):\n"]

    for start, stop, runtime, fuel in rows:
        start_s = start.replace("T", " ")[:16]
        stop_s = stop.replace("T", " ")[:16] if stop else "N/A"

        hours = runtime // 3600
        minutes = (runtime % 3600) // 60

        lines.append(
            f"{start_s} → {stop_s}\n"
            f"  Runtime: {hours}h {minutes}m\n"
            f"  Fuel used: {fuel:.1f} L"
        )

    await update.message.reply_text("\n".join(lines))


# ================= TELEGRAM =================

async def send(app: Application, text: str):
    await app.bot.send_message(chat_id=CHANNELID, text=text,reply_markup=bot_link_keyboard())

def bot_link_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Open bot", url=BOTURL)]
    ])

async def users_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only")
        return

    rows = get_whitelist_users()

    if not rows:
        await update.message.reply_text("ℹ️ Whitelist is empty")
        return

    lines = ["👥 Allowed users:\n"]

    for uid, username, added_at in rows:
        date = added_at.replace("T", " ")[:16] if added_at else "N/A"
        name = f"@{username}" if username else "—"
        lines.append(f"• {uid} | {name} | added: {date}")

    await update.message.reply_text("\n".join(lines))


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

# ================= restart msg =================
async def startup_message(app: Application):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await app.bot.send_message(
        chat_id=CHANNELID,
        text=(
            "❗️Generator bot restarted\n"
            f"Time: {now}"
        )
    )


# ================= COMMANDS =================

async def status_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    now = dt.datetime.now()
    fuel_left = get_effective_fuel_left_now(now)
    remaining_time = format_remaining_time(fuel_left)
    running = get_state("running", "0") == "1"

    day_runtime, day_fuel = get_stats(24)
    week_runtime, week_fuel = get_stats(24 * 7)

    msg = (
        f"❕STATUS: {GENERATORNAME}\n\n"
        f"State: {'🌀RUNNING' if running else '❌STOPPED'}\n"
        f"⛽️Fuel left: {fuel_left:.1f} L\n\n"
        f"⏳Estimated runtime: {remaining_time}\n\n"
        f"Last 24h:\n"
        f"⏱️  Runtime: {day_runtime // 3600}h {(day_runtime % 3600) // 60}m\n"
        f"⛽️🔽 Fuel used: {day_fuel:.1f} L\n\n"
        f"Last 7 days:\n"
        f"⏱️  Runtime: {week_runtime // 3600}h {(week_runtime % 3600) // 60}m\n"
        f"⛽️🔽 Fuel used: {week_fuel:.1f} L"
    )

    await update.message.reply_text(msg)

@whitelist_required
async def refuel_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /refuel <liters>")
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid fuel amount")
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
        f"❕Refuel recorded\n"
        f"🔄Added: {amount:.1f} L\n"
        f"⛽️Fuel level: {fuel_after:.1f} / {TANK_CAPACITY:.1f} L\n"
        f"👨🏻‍🦱By: {username}"
    )

@whitelist_required
async def reset_fuel_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /reset_fuel <liters>")
        return

    try:
        value = float(context.args[0])
        if value < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid fuel value")
        return

    if value > TANK_CAPACITY:
        await update.message.reply_text(
            f"Fuel value exceeds tank capacity ({TANK_CAPACITY:.1f} L)"
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
        f"Fuel level RESET\n"
        f"⛽️New level: {fuel_after:.1f} / {TANK_CAPACITY:.1f} L\n"
        f"👨🏻‍🦱By: {username}"
            )


# ================= MONITOR =================
async def monitor(app: Application):
    running = get_state("running", "0") == "1"

    while True:
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
                    app,
                    f"❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️\n"
                    f"⚠️ ALERT: Low fuel for {GENERATORNAME}\n"
                    f"⛽️Fuel left (est.): {fuel_now:.1f} L\n"
                    f"⏳Estimated runtime: {remaining_time}\n"
                    f"❗️Threshold: < {LOW_FUEL_HOURS:.2f} h"
                )
                set_state("low_fuel_alerted", 1)

            if rem_h >= LOW_FUEL_HOURS:
                set_state("low_fuel_alerted", 0)

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
                app,
                f"🌀{GENERATORNAME} STARTED\n"
                f"⛽️Fuel left: {fuel_now:.1f} L\n"
                f"⏳Estimated runtime: {remaining_time}"
            )

        # STOP
        if (not alive) and running:
            running = False
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
                app,
                f"❌{GENERATORNAME} STOPPED\n"
                f"⏱️Runtime: {seconds // 60} min\n"
                f"⛽️Fuel used: {used:.1f} L\n"
                f"⛽️Fuel left: {fuel_left:.1f} L\n"
                f"⏳Estimated runtime: {remaining_time}"
            )

        await asyncio.sleep(INTERVAL)


# ================== HELP =================


HELP_TEXT = (
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
)


async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


   
async def help_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

# ================= MAIN ==================
async def post_init(app: Application):
    await startup_message(app)
    app.create_task(monitor(app))


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


    app.post_init = post_init
    app.run_polling()




if __name__ == "__main__":
    main()
