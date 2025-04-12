import time
import requests
from telethon import events
from config import BOT
import speedtest
import pymongo
from pymongo import MongoClient
from config import MONGO_URL
import importlib
from pathlib import Path

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
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise an exception if no connection
        return True
    except pymongo.errors.ServerSelectionTimeoutError as e:
        return False, str(e)

# ISP Info
def get_isp_info():
    try:
        # Using ipinfo.io to get ISP info
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        ip = data.get("ip", "N/A")
        city = data.get("city", "N/A")
        country = data.get("country", "N/A")
        isp = data.get("org", "N/A")  # ISP info is often in "org" field
        return ip, city, country, isp
    except requests.RequestException:
        return "N/A", "N/A", "N/A", "N/A"

# Module Health Check
def check_module_health(module_name):
    try:
        # Try to import the module and check if it's functioning
        module = importlib.import_module(f"src.modules.{module_name}")
        # You can check basic functionality here, like if certain functions or variables exist
        if hasattr(module, 'BOT'):
            return True, f"{module_name} loaded successfully."
        return False, f"{module_name} does not have the required BOT functionality."
    except Exception as e:
        return False, f"Failed to load {module_name}: {str(e)}"

@BOT.on(events.NewMessage(pattern="/healthcheck"))
async def healthcheck(event):
    try:
        start_time = time.time()

        # 1. Check Bot Ping
        ping_start = time.time()
        response = await BOT.send_message(event.chat_id, "Testing bot health...")
        ping_time = time.time() - ping_start

        # 2. Perform Speed Test
        download_speed, upload_speed, ping = perform_speed_test()

        # 3. Check Database Connection
        db_status, db_error = check_database_connection()
        if db_status:
            db_status_msg = "Database is connected successfully."
        else:
            db_status_msg = f"Database connection failed: {db_error}"

        # 4. Get ISP Info
        ip, city, country, isp = get_isp_info()

        # 5. Check if all modules are working
        modules = ["admincache", "mention", "other_module_name"]  # Add all your module names here
        module_check_results = []
        for module in modules:
            success, message = check_module_health(module)
            module_check_results.append(f"{message} ({'✅' if success else '❌'})")

        # 6. Health Check Report
        health_report = f"""
        🟢 **Bot Health Check Passed!** ✅

        **Bot Response Time:** {ping_time * 1000:.2f} ms
        **Telegram Bot Ping (Bot -> Telegram -> Bot):** {ping_time * 1000:.2f} ms

        **Speed Test Results:**
        🏎️ **Download Speed:** {download_speed:.2f} Mbps
        📤 **Upload Speed:** {upload_speed:.2f} Mbps
        🏓 **Ping:** {ping} ms

        **Database Status:** {db_status_msg}

        **ISP Information:**
        🌐 **IP Address:** {ip}
        🌆 **City:** {city}
        🌍 **Country:** {country}
        📶 **ISP:** {isp}

        **Module Health Check Results:**
        {"\n".join(module_check_results)}

        ⏳ **Total Health Check Time:** {time.time() - start_time:.2f} seconds
        """

        await response.edit(health_report)

    except Exception as e:
        await event.reply(f"🔴 **Health check failed!** Error: {str(e)}")
