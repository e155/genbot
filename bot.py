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

# ================= COMMANDS =================

async def status_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    fuel_left = float(get_state("fuel_left", INITIAL_FUEL))
    running = get_state("running", "0") == "1"

    day_runtime, day_fuel = get_stats(24)
    week_runtime, week_fuel = get_stats(24 * 7)

    msg = (
        f"STATUS: {GENERATORNAME}\n\n"
        f"State: {'RUNNING' if running else 'STOPPED'}\n"
        f"Fuel left: {fuel_left:.1f} L\n\n"
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

    fuel_left = float(get_state("fuel_left", INITIAL_FUEL))
    new_level = min(TANK_CAPACITY, fuel_left + amount)

    set_state("fuel_left", new_level)

    await update.message.reply_text(
        f"Refueled: {amount:.1f} L\n"
        f"Fuel level: {new_level:.1f} / {TANK_CAPACITY:.1f} L"
    )

# ================= MONITOR =================

async def monitor(app: Application):
    running = get_state("running", "0") == "1"
    start_time = get_state("start_time")
    fuel_left = float(get_state("fuel_left", INITIAL_FUEL))

    while True:
        alive = ping(GENERATORADDR)
        now = dt.datetime.now()

        # START
        if alive and not running:
            running = True
            start_time = now.isoformat()

            set_state("running", 1)
            set_state("start_time", start_time)

            await send(
                app,
                f"{GENERATORNAME} STARTED\nFuel left: {fuel_left:.1f} L"
            )

        # STOP
        if not alive and running:
            running = False
            stop_time = now
            start_dt = dt.datetime.fromisoformat(start_time)

            runtime = int((stop_time - start_dt).total_seconds())
            used = fuel_used(runtime)
            fuel_left = max(0.0, fuel_left - used)

            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""
                    INSERT INTO generator_log
                    (start_time, stop_time, runtime_seconds, fuel_used)
                    VALUES (?, ?, ?, ?)
                """, (
                    start_time,
                    stop_time.isoformat(),
                    runtime,
                    used
                ))

            set_state("running", 0)
            set_state("fuel_left", fuel_left)

            await send(
                app,
                f"{GENERATORNAME} STOPPED\n"
                f"Runtime: {runtime // 60} min\n"
                f"Fuel used: {used:.1f} L\n"
                f"Fuel left: {fuel_left:.1f} L"
            )

        # DAILY REPORT
        if (
            now.hour == REPORTH
            and now.minute == REPORTM
            and now.second < INTERVAL
        ):
            day_runtime, day_fuel = get_stats(24)

            await send(
                app,
                f"DAILY REPORT: {GENERATORNAME}\n"
                f"Runtime: {day_runtime // 3600}h {(day_runtime % 3600)//60}m\n"
                f"Fuel used: {day_fuel:.1f} L\n"
                f"Fuel left: {fuel_left:.1f} L"
            )

            await asyncio.sleep(60)

        await asyncio.sleep(INTERVAL)

# ================= HELP =================


HELP_TEXT = (
    "Generator monitoring bot\n\n"
    "Available commands:\n\n"
    "/status\n"
    "  Show generator status\n"
    "  Statistics for last 24 hours and last 7 days\n\n"
    "/refuel <liters>\n"
    "  Add fuel to the tank\n"
    "  Example: /refuel 50"
)

async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

async def help_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

# ================= MAIN ==================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))   
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("refuel", refuel_cmd))

    async def post_init(app: Application):
        app.create_task(monitor(app))

    app.post_init = post_init

    app.run_polling()

if __name__ == "__main__":
    main()
