import os
import logging
from telethon import TelegramClient
from dotenv import load_dotenv
from strings.helpers import DEV

# Load environment variables from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

# Load values from environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", str(OWNER_ID)).split()))
SUDO_USERS.append(OWNER_ID)
SUDO_USERS.extend(DEV)

SPOILER_MODE = os.getenv("SPOILER_MODE", "True").lower() == "true"
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "default_db_name")
LOGGER = os.getenv("LOGGER", "False").lower() == "true"
BOT_NAME = os.getenv("BOT_NAME", "Guardify")
SUPPORT_ID = int(os.getenv("SUPPORT_ID", "-1002440907656"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize the bot client
BOT = TelegramClient("billa_guardian", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
