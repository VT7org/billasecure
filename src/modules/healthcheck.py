import time
import requests
import importlib
from pathlib import Path
import speedtest
from pymongo import MongoClient
from telethon import events
from config import BOT, MONGO_URI, OWNER_ID, SUDO_USERS
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to check if the user is authorized
async def is_authorized_user(user_id):
    # Check if the user is the owner
    if str(user_id) == str(OWNER_ID):
        return True
    
    # Check if the user is in the config's SUDO_USERS list
    if str(user_id) in map(str, SUDO_USERS):
        return True

    # Check if the user is in the database sudo_users
    try:
        db = MongoClient(MONGO_URI).get_database()
        sudo_users = db.sudo_users.find_one({"user_id": user_id})
        if sudo_users:
            return True
    except Exception as e:
        logger.error(f"Error while checking sudo users: {e}")

    return False

# Speed Test
def perform_speed_test():
    logger.info("Performing speed test...")
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Mbps
        upload_speed = st.upload() / 1_000_000  # Mbps
        ping = st.results.ping
        logger.info(f"Speed Test - DL: {download_speed:.2f} Mbps, UL: {upload_speed:.2f} Mbps, Ping: {ping} ms")
        return download_speed, upload_speed, ping
    except Exception as e:
        logger.error("Speed test failed", exc_info=True)
        raise RuntimeError("Uɴᴀʙʟᴇ ᴛᴏ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ sᴘᴇᴇᴅᴛᴇsᴛ sᴇʀᴠᴇʀs. Tʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")

# Database Connection Test
def check_database_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return True, None
    except Exception as e:
        return False, str(e)

# ISP Info
def get_isp_info():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        return data.get("ip", "N/A"), data.get("city", "N/A"), data.get("country", "N/A"), data.get("org", "N/A")
    except requests.RequestException:
        return "N/A", "N/A", "N/A", "N/A"

# Module Health Check
def check_module_health(module_name):
    try:
        module = importlib.import_module(f"src.modules.{module_name}")
        if not hasattr(module, 'BOT'):
            return False, f"❌ {module_name} missing 'BOT' object."
        missing = [
            func for func in ['update_admins', 'handle_chat_action']
            if not callable(getattr(module, func, None))
        ]
        if missing:
            return False, f"❌ {module_name} ᴍɪssɪɴɢ: {', '.join(missing)}."
        return True, f"🌱 {module_name} ʟᴏᴀᴅᴇᴅ ғɪɴᴇ."
    except Exception as e:
        return False, f"❌ {module_name} ᴇʀʀᴏʀ: {str(e)}"

# /health - Basic Health Check
@BOT.on(events.NewMessage(pattern="/health"))
async def healthcheck(event):
    try:
        user_id = event.sender_id

        if not await is_authorized_user(user_id):
            await event.reply("❌ ᴄᴏᴍᴍᴀɴᴅ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ.")
            return
        
        start = time.time()
        msg = await BOT.send_message(event.chat_id, "Rᴜɴɴɪɴɢ ɢᴜᴀʀᴅɪᴀɴ ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋᴜᴘ🍃...")

        # Ping
        ping_time = time.time() - start

        # DB Check
        db_ok, db_error = check_database_connection()
        db_status = "Cᴏɴɴᴇᴄᴛᴇᴅ" if db_ok else f"Fᴀɪʟᴇᴅ: {db_error}"

        # ISP Info
        ip, city, country, isp = get_isp_info()

        # Module Checks
        modules = ["admincache", "mention", "start", "editmode", "nsfw", "purge", "broadcast", "pretender", "help", "delete"]
        module_report = []
        for m in modules:
            ok, status = check_module_health(m)
            module_report.append(f"{status} ({'✅' if ok else '❌'})")

        # Report
        report = [
            " **ɢᴜᴀʀᴅɪᴀɴ ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋᴜᴘ ʀᴇᴘᴏʀᴛ☘️:**",
            f"⏱️ ʀᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ: `{ping_time * 1000:.2f} ᴍs`",
            f"🐳 ᴅʙ sᴛᴀᴛᴜs: `{db_status}`",
            "",
            "🌐 **ISP Iɴғᴏ:**",
            f"Iᴘ: `{ip}`",
            f"Cɪᴛʏ: `{city}`, Cᴏᴜɴᴛʀʏ: `{country}`",
            f"Isᴘ: `{isp}`",
            "",
            "**Mᴏᴅᴜʟᴇs:**",
            *module_report,
            "",
            f"⏳ Tᴏᴛᴀʟ Tɪᴍᴇ: `{time.time() - start:.2f} sᴇᴄ`"
        ]

        await msg.edit("\n".join(report))
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        await event.reply(f"🔴 **ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋᴜᴘ ғᴀɪʟᴇᴅ:** `{e}`")

# /sptest - Speed Test Only
@BOT.on(events.NewMessage(pattern="/sptest"))
async def sptest(event):
    try:
        user_id = event.sender_id

        if not await is_authorized_user(user_id):
            await event.reply("❌ ᴄᴏᴍᴍᴀɴᴅ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ. ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ.")
            return
        
        msg = await event.respond("Rᴜɴɴɪɴɢ sᴘᴇᴇᴅ ᴛᴇsᴛ. ʜᴏʟᴅ ᴏɴ...")
        download_speed, upload_speed, ping = perform_speed_test()

        result = "\n".join([
            "🏎️ **Sᴘᴇᴇᴅ ᴛᴇsᴛ ʀᴇsᴜʟᴛs:**",
            f"📥 Dᴏᴡɴʟᴏᴀᴅ: `{download_speed:.2f} Mʙᴘs`",
            f"📤 Uᴘʟᴏᴀᴅ: `{upload_speed:.2f} Mʙᴘs`",
            f"🏓 Pɪɴɢ ʟᴀᴛᴇɴᴄʏ: `{ping} ᴍs`"
        ])
        await msg.edit(result)

    except RuntimeError as e:
        await event.reply(f"⚠️ {str(e)}")
    except Exception as e:
        logger.error("Unexpected error during speedtest", exc_info=True)
        await event.reply("⚠️ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏʀ ᴍᴀʏ ɪsᴘ ʙʟᴏᴄᴋᴇᴅ ᴛᴏ ᴄʜᴋ sᴘᴇᴇᴅᴛᴇsᴛ.")
