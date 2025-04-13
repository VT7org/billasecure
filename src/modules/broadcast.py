import asyncio
import logging
from telethon import events
from config import BOT, MONGO_URI, OWNER_ID, SUDO_USERS
from pymongo import MongoClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
users_collection = db["users"]
active_groups_collection = db["active_groups"]

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
    groups = list(active_groups_collection.find())

    total_users = len(users)
    total_groups = len(groups)
    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    await event.reply(f"🍃 Sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ <code>{total_users}</code> ᴜsᴇʀs ᴀɴᴅ <code>{total_groups}</code> ɢʀᴏᴜᴘs...", parse_mode="html")

    # Broadcast to users
    for user in users:
        try:
            await BOT.send_message(
                int(user["chat_id"]),
                message=reply.message or None,
                file=reply.media if reply.media else None,
                parse_mode="html",
                buttons=reply.buttons,
                link_preview=reply.link_preview,
                reply_to=None
            )
            success_users += 1
        except Exception as e:
            logger.error(f"ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ ғᴀɪʟᴇᴅ {user.get('chat_id')}: {e}")
            failed_users += 1

    # Broadcast to groups
    for group in groups:
        group_id = group.get("group_id")
        if not group_id:
            failed_groups += 1
            continue

        try:
            still_in_group = await is_bot_still_in_group(group_id)
            if not still_in_group:
                active_groups_collection.delete_one({"group_id": group_id})
                logger.info(f"Rᴇᴍᴏᴠᴇᴅ ɪɴᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘ {group.get('group_name', 'Unknown')} ({group_id})")
                failed_groups += 1
                continue

            await BOT.send_message(
                int(group_id),
                message=reply.message or None,
                file=reply.media if reply.media else None,
                parse_mode="html",
                buttons=reply.buttons,
                link_preview=reply.link_preview,
                reply_to=None
            )
            success_groups += 1
        except Exception as e:
            logger.error(f"ɢʀᴏᴜᴘ ʙʀᴏᴀᴅᴄᴀsᴛ ғᴀɪʟᴇᴅ {group.get('group_name', 'Unknown')} ({group_id}): {e}")
            failed_groups += 1

    await event.reply(
        f"☘️ <b>Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
        f"👤 <b>Uꜱᴇʀs:</b> <code>{success_users}/{total_users}</code> sᴜᴄᴄᴇssғᴜʟ, <code>{failed_users}</code> ғᴀɪʟᴇᴅ.\n"
        f"👥 <b>Gʀᴏᴜᴘs:</b> <code>{success_groups}/{total_groups}</code> ʙʀᴏᴀᴅᴄᴀsᴛᴇᴅ, <code>{failed_groups}</code> ғᴀɪʟᴇᴅ.",
        parse_mode="html"
    )
