import asyncio
import datetime as dt
import sqlite3
import subprocess

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
    LOW_FUEL_HOURS
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

def get_effective_fuel_left_now() -> float:
    """
    Returns current fuel estimate.
    If generator is running, subtract fuel used since start_time (not persisted).
    """
    base_fuel = float(get_state("fuel_left", INITIAL_FUEL))
    running = get_state("running", "0") == "1"
    start_time = get_state("start_time")

    if not running or not start_time:
        return base_fuel

    try:
        start_dt = dt.datetime.fromisoformat(start_time)
    except ValueError:
        return base_fuel

    elapsed = int((dt.datetime.now() - start_dt).total_seconds())
    used = fuel_used(elapsed)
    return max(0.0, base_fuel - used)



# ================ Ref history ============
async def refuel_history_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /refuel_history <days>")
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
        lines.append(
            f"{time_str} | +{amount:.1f} L | "
            f"{before:.1f} → {after:.1f} | {user}"
        )

    await update.message.reply_text("\n".join(lines))

# ================= History =====================

async def history_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /history <days>")
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
            f"No generator activity for last {days} days"
        )
        return

    lines = [f"Generator history (last {days} days):\n"]

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
    await app.bot.send_message(chat_id=CHANNELID, text=text)

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
            "Generator bot restarted\n"
            f"Time: {now}"
        )
    )


# ================= COMMANDS =================

async def status_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    fuel_left = get_effective_fuel_left_now()
    remaining_time = format_remaining_time(fuel_left)
    running = get_state("running", "0") == "1"

    day_runtime, day_fuel = get_stats(24)
    week_runtime, week_fuel = get_stats(24 * 7)

    msg = (
        f"STATUS: {GENERATORNAME}\n\n"
        f"State: {'RUNNING' if running else 'STOPPED'}\n"
        f"Fuel left: {fuel_left:.1f} L\n\n"
        f"Estimated runtime: {remaining_time}\n\n"
        f"Last 24h:\n"
        f"  Runtime: {day_runtime // 3600}h {(day_runtime % 3600) // 60}m\n"
        f"  Fuel used: {day_fuel:.1f} L\n\n"
        f"Last 7 days:\n"
        f"  Runtime: {week_runtime // 3600}h {(week_runtime % 3600) // 60}m\n"
        f"  Fuel used: {week_fuel:.1f} L"
    )

    await update.message.reply_text(msg)

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

    fuel_before = float(get_state("fuel_left", INITIAL_FUEL))
    fuel_after = min(TANK_CAPACITY, fuel_before + amount)

    set_state("fuel_left", fuel_after)

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
            dt.datetime.now().isoformat(),
            amount,
            fuel_before,
            fuel_after,
            user_id,
            username
        ))
    # allow alert to trigger again after refuel
    set_state("low_fuel_alerted", 0)


    await update.message.reply_text(
        f"Refuel recorded\n"
        f"Added: {amount:.1f} L\n"
        f"Fuel level: {fuel_after:.1f} / {TANK_CAPACITY:.1f} L\n"
        f"By: {username}"
    )


# ================= MONITOR =================
async def monitor(app: Application):
    running = get_state("running", "0") == "1"
    start_time = get_state("start_time")
    fuel_left = float(get_state("fuel_left", INITIAL_FUEL))

    while True:
        alive = ping(GENERATORADDR)
        now = dt.datetime.now()

        # Low-fuel alert (while running)
        if running:
            fuel_now = get_effective_fuel_left_now()
            rem_h = remaining_hours_from_fuel(fuel_now)

            alerted = get_state("low_fuel_alerted", "0") == "1"

            if (rem_h < LOW_FUEL_HOURS) and (not alerted):
                remaining_time = format_remaining_time(fuel_now)
                await send(
                    app,
                    f"ALERT: Low fuel for {GENERATORNAME}\n"
                    f"Fuel left (est.): {fuel_now:.1f} L\n"
                    f"Estimated runtime: {remaining_time}\n"
                    f"Threshold: < {LOW_FUEL_HOURS:.2f} h"
                )
                set_state("low_fuel_alerted", 1)

            # Reset alert flag if refueled above threshold again
            if rem_h >= LOW_FUEL_HOURS:
                set_state("low_fuel_alerted", 0)

        # START
        if alive and not running:
            running = True
            start_time = now.isoformat()

            set_state("running", 1)
            set_state("start_time", start_time)

            # NOTE: use effective fuel for nice message
            fuel_now = get_effective_fuel_left_now()
            remaining_time = format_remaining_time(fuel_now)

            await send(
                app,
                f"{GENERATORNAME} STARTED\n"
                f"Fuel left: {fuel_now:.1f} L\n"
                f"Estimated runtime: {remaining_time}"
            )

        # STOP
        if (not alive) and running:
            running = False
            stop_time = now
            start_dt = dt.datetime.fromisoformat(start_time)

            runtime = int((stop_time - start_dt).total_seconds())
            used = fuel_used(runtime)

            fuel_left = max(0.0, fuel_left - used)
            remaining_time = format_remaining_time(fuel_left)

            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""
                    INSERT INTO generator_log
                    (start_time, stop_time, runtime_seconds, fuel_used)
                    VALUES (?, ?, ?, ?)
                """, (start_time, stop_time.isoformat(), runtime, used))

            set_state("running", 0)
            set_state("fuel_left", fuel_left)

            await send(
                app,
                f"{GENERATORNAME} STOPPED\n"
                f"Runtime: {runtime // 60} min\n"
                f"Fuel used: {used:.1f} L\n"
                f"Fuel left: {fuel_left:.1f} L\n"
                f"Estimated runtime: {remaining_time}"
            )

        # DAILY REPORT
        if (
            now.hour == REPORTH
            and now.minute == REPORTM
            and now.second < INTERVAL
        ):
            day_runtime, day_fuel = get_stats(24)

            fuel_now = get_effective_fuel_left_now()
            remaining_time = format_remaining_time(fuel_now)

            await send(
                app,
                f"DAILY REPORT: {GENERATORNAME}\n"
                f"Runtime: {day_runtime // 3600}h {(day_runtime % 3600)//60}m\n"
                f"Fuel used: {day_fuel:.1f} L\n"
                f"Fuel left: {fuel_now:.1f} L\n"
                f"Estimated runtime: {remaining_time}"
            )

            await asyncio.sleep(60)

        await asyncio.sleep(INTERVAL)


# ================== HELP =================


HELP_TEXT = (
    "Generator monitoring bot\n\n"
    "Available commands:\n\n"
    "/status\n"
    "  Show generator status\n"
    "  Statistics for last 24 hours and last 7 days\n\n"
    "/refuel <liters>\n"
    "  Add fuel to the tank\n"
    "  Example: /refuel 50\n"
    "/rhistory <days>\n"
    "  Show refueling history\n"
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
    app.post_init = post_init
    app.run_polling()




if __name__ == "__main__":
    main()
