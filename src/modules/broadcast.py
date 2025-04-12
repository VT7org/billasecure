import asyncio
from telethon import events
from config import BOT, MONGO_URI, OWNER_ID, SUDO_USERS
from pymongo import MongoClient
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
users_collection = db["users"]
groups_collection = db["groups"]

# Combine config SUDO and Mongo users
def get_sudo_users():
    mongo_users = [user["user_id"] for user in users_collection.find({"user_id": {"$exists": True}})]
    return set(mongo_users + list(SUDO_USERS))

@BOT.on(events.NewMessage(pattern="/broadcast"))
async def broadcast(event):
    if event.sender_id != OWNER_ID and event.sender_id not in get_sudo_users():
        return await event.reply("❌ Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("❗Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")

    users = list(users_collection.find())
    groups = list(groups_collection.find())

    total_users = len(users)
    total_groups = len(groups)
    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    await event.reply(f"📡 Sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ `{total_users}` ᴜsᴇʀs ᴀɴᴅ `{total_groups}` ɢʀᴏᴜᴘs...")

    for user in users:
        try:
            await BOT.forward_messages(
                int(user["chat_id"]),
                messages=reply.id,
                from_peer=event.chat_id
            )
            success_users += 1
        except Exception as e:
            failed_users += 1
            logger.error(f"User broadcast fail {user['chat_id']}: {e}")

    for group in groups:
        try:
            await BOT.forward_messages(
                int(group["chat_id"]),
                messages=reply.id,
                from_peer=event.chat_id
            )
            success_groups += 1
        except Exception as e:
            failed_groups += 1
            logger.error(f"Group broadcast fail {group['chat_id']}: {e}")

    await event.reply(
        f"✅ **Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇ**\n\n"
        f"👤 **Uꜱᴇʀs:** `{success_users}/{total_users}` sᴜᴄᴄᴇssғᴜʟ, `{failed_users}` ғᴀɪʟᴇᴅ.\n"
        f"👥 **Gʀᴏᴜᴘs:** `{success_groups}/{total_groups}` sᴜᴄᴄᴇssғᴜʟ, `{failed_groups}` ғᴀɪʟᴇᴅ."
        )
