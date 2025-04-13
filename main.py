import sys
import glob
import asyncio
import logging
import importlib.util
import urllib3
import signal
from pathlib import Path
from config import BOT, MONGO_URI
from pymongo import MongoClient

# Logging setup
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
active_groups_collection = db["active_groups"]

# Plugin loader
def load_plugins(plugin_name):
    path = Path(f"src/modules/{plugin_name}.py")
    try:
        spec = importlib.util.spec_from_file_location(f"src.modules.{plugin_name}", path)
        load = importlib.util.module_from_spec(spec)
        load.logger = logging.getLogger(plugin_name)
        spec.loader.exec_module(load)
        sys.modules[f"src.modules.{plugin_name}"] = load
        print(f"ꜱᴛᴏʀᴍ ʜᴀꜱ ɪᴍᴘᴏʀᴛᴇᴅ {plugin_name}")
    except Exception as e:
        print(f"ꜰᴀɪʟᴇᴅ ᴛᴏ ʟᴏᴀᴅ ᴘʟᴜɢɪɴ {plugin_name}: {e}")

files = glob.glob("src/modules/*.py")
for name in files:
    patt = Path(name)
    plugin_name = patt.stem
    load_plugins(plugin_name)

print("\nɢᴜᴀʀᴅɪғʏ ɪꜱ ᴅᴇᴘʟᴏʏᴇᴅ ꜱᴜᴄᴄᴇꜱꜰᴜʟʟʏ")

# Auto clean inactive groups every 1 min
async def auto_clean_inactive_groups():
    while True:
        active_groups = list(active_groups_collection.find({}))
        for group in active_groups:
            group_id = group.get("group_id")
            if not group_id:
                continue
            try:
                await BOT.get_entity(group_id)
            except Exception:
                active_groups_collection.delete_one({"group_id": group_id})
                print(f"[Auto-Clean] Rᴇᴍᴏᴠᴇᴅ ɪɴᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘ {group_id}")
        await asyncio.sleep(60)

# Graceful shutdown support
shutdown_event = asyncio.Event()

def handle_shutdown():
    print("\n[ꜱʜᴜᴛᴅᴏᴡɴ] ᴄᴀᴜɢʜᴛ ꜱɪɢɴᴀʟ, ᴄʟᴇᴀɴɪɴɢ ᴜᴘ...")
    shutdown_event.set()

for sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, lambda s, f: handle_shutdown())

# Main async runner
async def main():
    clean_task = asyncio.create_task(auto_clean_inactive_groups())
    bot_task = asyncio.create_task(BOT.run_until_disconnected())
    await shutdown_event.wait()

    print("[ꜱʜᴜᴛᴅᴏᴡɴ] ꜱᴛᴏᴘᴘɪɴɢ ᴛᴀꜱᴋꜱ...")
    clean_task.cancel()
    await BOT.disconnect()

    print("[ꜱʜᴜᴛᴅᴏᴡɴ] ᴇxɪᴛ ᴄᴏᴍᴘʟᴇᴛᴇ.")

# Start loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
