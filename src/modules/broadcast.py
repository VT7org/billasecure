# broadcast.py
import asyncio
from telethon import events
from telethon.errors import FloodWaitError
from config import BOT, MONGO_URI, OWNER_ID, SUDO_USERS
from pymongo import MongoClient
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
users_collection = db["users"]
active_groups_collection = db["active_groups"]

def get_sudo_users():
    mongo_users = [u["user_id"] for u in users_collection.find({"user_id": {"$exists": True}})]
    return set(mongo_users + list(SUDO_USERS))

async def is_bot_still_in_group(group_id):
    try:
        await BOT.get_entity(group_id)
        return True
    except Exception:
        return False

@BOT.on(events.NewMessage(pattern="/broadcast"))
async def broadcast(event):
    if event.sender_id != OWNER_ID and event.sender_id not in get_sudo_users():
        return await event.reply("🍁 Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("❗Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")

    users = list(users_collection.find())
    groups = list(active_groups_collection.find())

    total_users = len(users)
    total_groups = len(groups)
    success_users = failed_users = success_groups = failed_groups = 0

    await event.reply(f"🍃 Sᴛᴀʀᴛᴇᴅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ `{total_users}` ᴜsᴇʀs & `{total_groups}` ɢʀᴏᴜᴘs...")

    for user in users:
        chat_id = user.get("chat_id")
        if not chat_id or not str(chat_id).lstrip("-").isdigit():
            continue
        try:
            await BOT.forward_messages(chat_id, reply.id, from_peer=event.chat_id)
            success_users += 1
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception:
            failed_users += 1
        await asyncio.sleep(0.2)

    for group in groups:
        group_id = group.get("group_id")
        if not group_id or not str(group_id).lstrip("-").isdigit():
            continue
        try:
            if not await is_bot_still_in_group(group_id):
                active_groups_collection.delete_one({"group_id": group_id})
                failed_groups += 1
                continue
            await BOT.forward_messages(group_id, reply.id, from_peer=event.chat_id)
            success_groups += 1
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except Exception:
            failed_groups += 1
        await asyncio.sleep(0.2)

    await event.reply(
        f"☘️ **Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ**\n"
        f"👤 **Uꜱᴇʀs:** `{success_users}/{total_users}` success, `{failed_users}` failed\n"
        f"👥 **Gʀᴏᴜᴘs:** `{success_groups}/{total_groups}` success, `{failed_groups}` failed"
)
