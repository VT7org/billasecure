from telethon import events
from config import BOT, OWNER_ID, SUDO_USERS
from pymongo import MongoClient
from config import MONGO_URI
import logging

client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
gban_collection = db["global_bans"]

logger = logging.getLogger(__name__)

def is_gbanned(user_id):
    return gban_collection.find_one({"user_id": user_id})

def gban_user(user_id, reason):
    gban_collection.update_one(
        {"user_id": user_id},
        {"$set": {"reason": reason}},
        upsert=True
    )

def ungban_user(user_id):
    gban_collection.delete_one({"user_id": user_id})

@BOT.on(events.NewMessage(pattern="/gban"))
async def gban(event):
    if event.sender_id not in SUDO_USERS and event.sender_id != OWNER_ID:
        return await event.reply("🚫 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ Gʙᴀɴ.")

    user = await reply.get_sender()
    if is_gbanned(user.id):
        return await event.reply("❗️Uꜱᴇʀ ɪꜱ ᴀʟʀᴇᴀᴅʏ Gʙᴀɴɴᴇᴅ.")
    
    reason = " ".join(event.message.text.split()[1:]) or "Nᴏ Rᴇᴀꜱᴏɴ"
    gban_user(user.id, reason)
    await event.reply(f"✅ <b>Gʙᴀɴɴᴇᴅ</b> {user.first_name} [<code>{user.id}</code>] ꜰᴏʀ:\n<b>{reason}</b>", parse_mode='html')

@BOT.on(events.NewMessage(pattern="/ungban"))
async def ungban(event):
    if event.sender_id not in SUDO_USERS and event.sender_id != OWNER_ID:
        return await event.reply("🚫 ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("⚠️ Rᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ UɴGʙᴀɴ.")

    user = await reply.get_sender()
    if not is_gbanned(user.id):
        return await event.reply("✅ Uꜱᴇʀ ɪꜱ ɴᴏᴛ Gʙᴀɴɴᴇᴅ.")
    
    ungban_user(user.id)
    await event.reply(f"✅ <b>UɴGʙᴀɴɴᴇᴅ</b> {user.first_name} [<code>{user.id}</code>]", parse_mode='html')

# Delete messages from gbanned users
@BOT.on(events.NewMessage)
async def enforce_gban(event):
    if event.is_group and is_gbanned(event.sender_id):
        try:
            await event.delete()
            logger.info(f"Deleted message from Gbanned user {event.sender_id} in {event.chat_id}")
        except Exception as e:
            logger.warning(f"Failed to delete msg from Gbanned user: {e}")
