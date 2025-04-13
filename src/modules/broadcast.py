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
active_groups_collection = db["active_groups"]  # For groups the bot is active in

# Combine config SUDO and Mongo users
def get_sudo_users():
    mongo_users = [user["user_id"] for user in users_collection.find({"user_id": {"$exists": True}})]
    return set(mongo_users + list(SUDO_USERS))

# Check if bot is still in the group
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
    active_groups = list(active_groups_collection.find())

    total_users = len(users)
    total_groups = len(active_groups)
    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    await event.reply(f"🍃 Sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ `{total_users}` ᴜsᴇʀs ᴀɴᴅ `{total_groups}` ᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘs...")

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
            logger.error(f"ᴜsᴇʀs ʙʀᴏᴀᴅᴄᴀsᴛ ғᴀɪʟᴇᴅ {user.get('chat_id')}: {e}")

    for group in active_groups:
        try:
            group_id = group.get("group_id")
            if not group_id:
                raise ValueError("Missing group_id")

            still_in = await is_bot_still_in_group(group_id)
            if not still_in:
                # Clean up if bot was removed or left
                active_groups_collection.delete_one({"group_id": group_id})
                logger.info(f"Rᴇᴍᴏᴠᴇᴅ ɪɴᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘs {group.get('group_name', 'Unknown')} ({group_id})")
                failed_groups += 1
                continue

            await BOT.forward_messages(
                int(group_id),
                messages=reply.id,
                from_peer=event.chat_id
            )
            success_groups += 1
        except Exception as e:
            failed_groups += 1
            logger.error(f"ɢʀᴏᴜᴘs ʙʀᴏᴀᴅᴄᴀsᴛ ғᴀɪʟᴇᴅ {group.get('group_name', 'Unknown')}: {e}")

    await event.reply(
        f"☘️ **Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴇᴅ**\n\n"
        f"👤 **Uꜱᴇʀs:** `{success_users}/{total_users}` sᴜᴄᴄᴇssғᴜʟ, `{failed_users}` ғᴀɪʟᴇᴅ.\n"
        f"👥 **Gʀᴏᴜᴘs:** `{success_groups}/{total_groups}` ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ, `{failed_groups}` ғᴀɪʟᴇᴅ."
            )
