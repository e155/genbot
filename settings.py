import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
TOKEN = os.getenv("TOKEN")
CHANNELID = os.getenv("CHANNELID")
BOTURL = os.getenv("BOTURL")
if TOKEN is None:
    raise Exception("Please setup the .env variable TELEGRAM_TOKEN.")

GENERATORNAME = os.getenv("GENERATORNAME")
GENERATORADDR = os.getenv("GENERATORADDR")
INTERVAL = int(os.getenv("INTERVAL",60))
REPORTH = int(os.getenv("REPORTH",7))
REPORTM = int(os.getenv("REPORTM",0))


# Generator parameters (fuel logic)
TANK_CAPACITY = int(os.getenv("TANK_CAPACITY", 240))
FUEL_CONSUMPTION = float(os.getenv("FUEL_CONSUMPTION", 16))
INITIAL_FUEL = float(os.getenv("INITIAL_FUEL", 190))
LOW_FUEL_HOURS = float(os.getenv("LOW_FUEL_HOURS", 4))


# Database file
DB_FILE = "generator.db"
