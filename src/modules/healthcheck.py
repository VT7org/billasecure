import time
import requests
import importlib
import logging
from pathlib import Path
import speedtest
import pymongo
from pymongo import MongoClient
from telethon import events
from config import BOT, MONGO_URI

# Setup logger
logger = logging.getLogger("HealthCheck")
logging.basicConfig(level=logging.INFO)

# Speed Test
def perform_speed_test():
    logger.info("Performing speed test...")
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # in Mbps
    upload_speed = st.upload() / 1_000_000  # in Mbps
    ping = st.results.ping
    logger.info(f"Speed Test Results - Download: {download_speed:.2f} Mbps, Upload: {upload_speed:.2f} Mbps, Ping: {ping} ms")
    return download_speed, upload_speed, ping

# Database Connection Test
def check_database_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        logger.info("MongoDB connection successful.")
        return True, None
    except pymongo.errors.ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False, str(e)

# ISP Info
def get_isp_info():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        ip = data.get("ip", "N/A")
        city = data.get("city", "N/A")
        country = data.get("country", "N/A")
        isp = data.get("org", "N/A")
        logger.info(f"ISP Info - IP: {ip}, City: {city}, Country: {country}, ISP: {isp}")
        return ip, city, country, isp
    except requests.RequestException as e:
        logger.error(f"Failed to fetch ISP info: {str(e)}")
        return "N/A", "N/A", "N/A", "N/A"

# Module Health Check
def check_module_health(module_name):
    try:
        module = importlib.import_module(f"src.modules.{module_name}")

        if not hasattr(module, 'BOT'):
            return False, f"❌ {module_name} does not contain a 'BOT' object."

        required_functions = ['update_admins', 'handle_chat_action']
        missing_functions = [
            func for func in required_functions
            if not hasattr(module, func) or not callable(getattr(module, func))
        ]

        if missing_functions:
            return False, f"❌ {module_name} is missing functions: {', '.join(missing_functions)}."

        return True, f"✅ {module_name} loaded and working properly."
    except Exception as e:
        return False, f"❌ Failed to load {module_name}: {str(e)}"

# General health check (no speed test)
@BOT.on(events.NewMessage(pattern="/health"))
async def healthcheck(event):
    try:
        start_time = time.time()

        # 1. Ping Test
        ping_start = time.time()
        response = await BOT.send_message(event.chat_id, "Testing bot health...")
        ping_time = time.time() - ping_start
        logger.info(f"Bot ping response time: {ping_time * 1000:.2f} ms")

        # 2. Database Check
        db_status, db_error = check_database_connection()
        db_status_msg = (
            "Database is connected successfully."
            if db_status else f"Database connection failed: {db_error}"
        )

        # 3. ISP Info
        ip, city, country, isp = get_isp_info()

        # 4. Module Checks
        modules = ["admincache", "mention"]  # Add all modules to check
        module_check_results = []
        for module in modules:
            success, message = check_module_health(module)
            logger.info(message)
            module_check_results.append(f"{message} ({'✅' if success else '❌'})")

        # Final Report
        report_lines = [
            "🟢 **Bot Health Check Passed!** ✅",
            "",
            f"**Bot Response Time:** {ping_time * 1000:.2f} ms",
            "",
            f"**Database Status:** {db_status_msg}",
            "",
            "**ISP Information:**",
            f"🌐 **IP Address:** {ip}",
            f"🌆 **City:** {city}",
            f"🌍 **Country:** {country}",
            f"📶 **ISP:** {isp}",
            "",
            "**Module Health Check Results:**",
            *module_check_results,
            "",
            f"⏳ **Total Health Check Time:** {time.time() - start_time:.2f} seconds"
        ]

        await response.edit("\n".join(report_lines))

        # Optional: Log to DB
        # db.health_logs.insert_one({ "timestamp": time.time(), "results": report_lines })

    except Exception as e:
        logger.exception("Health check failed")
        await event.reply(f"🔴 **Health check failed!** Error: {str(e)}")

# Speed test command separately
@BOT.on(events.NewMessage(pattern="/sptest"))
async def sptest(event):
    try:
        msg = await event.respond("Running speed test. Please wait...")
        download_speed, upload_speed, ping = perform_speed_test()

        result_text = "\n".join([
            "🏎️ **Speed Test Results:**",
            f"📥 **Download Speed:** {download_speed:.2f} Mbps",
            f"📤 **Upload Speed:** {upload_speed:.2f} Mbps",
            f"🏓 **Ping:** {ping} ms"
        ])

        await msg.edit(result_text)

    except Exception as e:
        logger.exception("Speed test failed")
        await event.reply(f"⚠️ Speed test failed: {str(e)}")
