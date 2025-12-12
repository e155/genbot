import asyncio
import datetime as dt
import sqlite3
import subprocess

from telegram import Bot
from settings import (
    TOKEN, CHANNELID, GENERATORNAME, GENERATORADDR,
    INTERVAL, REPORTH, REPORTM,
    TANK_CAPACITY, FUEL_CONSUMPTION, INITIAL_FUEL, DB_FILE
)

bot = Bot(token=TOKEN)

# ------------------ Database ------------------

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
        cur = conn.execute("SELECT value FROM state WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set_state(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO state (key, value) VALUES (?, ?)",
            (key, str(value))
        )

# ------------------ ICMP Ping ------------------

def ping(host):
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", host],
        stdout=subprocess.DEVNULL
    )
    return result.returncode == 0

# ------------------ Fuel logic ------------------

def fuel_used(seconds):
    return (seconds / 3600) * FUEL_CONSUMPTION

# ------------------ Telegram ------------------

async def send(msg):
    await bot.send_message(chat_id=CHANNELID, text=msg)

# ------------------ Main logic ------------------

async def monitor():
    running = get_state("running", "0") == "1"
    start_time = get_state("start_time")
    fuel_left = float(get_state("fuel_left", INITIAL_FUEL))

    while True:
        alive = ping(GENERATORADDR)
        now = dt.datetime.now()

        # Generator started
        if alive and not running:
            running = True
            start_time = now.isoformat()
            set_state("running", 1)
            set_state("start_time", start_time)

            await send(
                f"🔌 {GENERATORNAME} STARTED\n"
                f"⛽ Fuel left: {fuel_left:.1f} L"
            )

        # Generator stopped
        if not alive and running:
            running = False
            stop_time = now
            start_dt = dt.datetime.fromisoformat(start_time)

            runtime = int((stop_time - start_dt).total_seconds())
            used = fuel_used(runtime)
            fuel_left = max(0, fuel_left - used)

            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("""
                    INSERT INTO generator_log
                    (start_time, stop_time, runtime_seconds, fuel_used)
                    VALUES (?, ?, ?, ?)
                """, (start_time, stop_time.isoformat(), runtime, used))

            set_state("running", 0)
            set_state("fuel_left", fuel_left)

            await send(
                f"⛔ {GENERATORNAME} STOPPED\n"
                f"⏱ Runtime: {runtime // 60} min\n"
                f"⛽ Fuel used: {used:.1f} L\n"
                f"🛢 Fuel left: {fuel_left:.1f} L"
            )

        # Daily report
        if now.hour == REPORTH and now.minute == REPORTM and now.second < INTERVAL:
            with sqlite3.connect(DB_FILE) as conn:
                cur = conn.execute("""
                    SELECT SUM(runtime_seconds), SUM(fuel_used)
                    FROM generator_log
                    WHERE date(start_time)=date('now')
                """)
                r = cur.fetchone()
                runtime = r[0] or 0
                used = r[1] or 0

            await send(
                f"📊 DAILY REPORT ({GENERATORNAME})\n"
                f"⏱ Runtime: {runtime // 3600}h {(runtime % 3600) // 60}m\n"
                f"⛽ Fuel used: {used:.1f} L\n"
                f"🛢 Fuel left: {fuel_left:.1f} L"
            )
            await asyncio.sleep(60)

        await asyncio.sleep(INTERVAL)

# ------------------ Entry ------------------

if __name__ == "__main__":
    init_db()
    asyncio.run(monitor())
