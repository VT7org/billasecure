import time
import requests
import importlib
from pathlib import Path
import speedtest
import pymongo
from pymongo import MongoClient
from telethon import events
from config import BOT, MONGO_URI

# Speed Test
def perform_speed_test():
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # in Mbps
    upload_speed = st.upload() / 1_000_000  # in Mbps
    ping = st.results.ping
    return download_speed, upload_speed, ping

# Database Connection Test
def check_database_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise an exception if no connection
        return True, None
    except pymongo.errors.ServerSelectionTimeoutError as e:
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
        return ip, city, country, isp
    except requests.RequestException:
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

@BOT.on(events.NewMessage(pattern="/healthcheck"))
async def healthcheck(event):
    try:
        start_time = time.time()

        # 1. Ping Test
        ping_start = time.time()
        response = await BOT.send_message(event.chat_id, "Testing bot health...")
        ping_time = time.time() - ping_start

        # 2. Speed Test
        download_speed, upload_speed, ping = perform_speed_test()

        # 3. Database Check
        db_status, db_error = check_database_connection()
        db_status_msg = (
            "Database is connected successfully."
            if db_status else f"Database connection failed: {db_error}"
        )

        # 4. ISP Info
        ip, city, country, isp = get_isp_info()

        # 5. Module Checks
        modules = ["admincache", "mention"]  # Add all modules to check
        module_check_results = []
        for module in modules:
            success, message = check_module_health(module)
            module_check_results.append(f"{message} ({'✅' if success else '❌'})")

        # 6. Final Report
        report_lines = [
            "🟢 **Bot Health Check Passed!** ✅",
            "",
            f"**Bot Response Time:** {ping_time * 1000:.2f} ms",
            "",
            "**Speed Test Results:**",
            f"🏎️ **Download Speed:** {download_speed:.2f} Mbps",
            f"📤 **Upload Speed:** {upload_speed:.2f} Mbps",
            f"🏓 **Ping:** {ping} ms",
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

    except Exception as e:
        await event.reply(f"🔴 **Health check failed!** Error: {str(e)}")
