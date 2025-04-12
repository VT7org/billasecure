from telethon import events
from telethon.tl.custom import Button
from config import BOT, SUDO_USERS, OWNER_ID, MONGO_URL
from pymongo import MongoClient
import heroku3
import logging
import asyncio

# MongoDB Setup
client = MongoClient(MONGO_URL)
db = client["billa_guardian"]
users_collection = db["users"]
groups_collection = db["groups"]

START_OP = [
    [Button.url("ᴀᴅᴅ ᴍᴇ ↗️", "https://t.me/BillaGuardianBot?startgroup=true&admin=delete_messages")],
    [Button.url("ꜱᴜᴘᴘᴏʀᴛ", "https://t.me/ignite_chatz"), Button.url("ᴄʜᴀɴɴᴇʟ", "https://t.me/BillaSpace")]
]

@BOT.on(events.NewMessage(pattern="/start"))
async def start(event):
    sender = await event.get_sender()
    chat = await event.get_chat()
    chat_id = event.chat_id

    if event.is_private:
        users_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"name": sender.first_name}},
            upsert=True
        )
    elif event.is_group or event.is_channel:
        groups_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"name": chat.title}},
            upsert=True
        )

    bot_name = (await BOT.get_me()).first_name
    TEXT = f"""
<b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ʙɪʟʟᴀ ɢᴜᴀʀᴅɪᴀɴ ʙᴏᴛ ⚡️</b>
<b><u>ɪ'ᴍ ʏᴏᴜʀ ɢʀᴏᴜᴘ’ꜱ ꜱʜɪᴇʟᴅ ᴀɢᴀɪɴꜱᴛ ꜱᴘᴀᴍ, ɴsғᴡ ɪᴍᴀɢᴇs, ᴜɴᴡᴀɴᴛᴇᴅ ᴍᴇᴅɪᴀ, ꜱɴᴇᴀᴋʏ ᴍsɢ ᴇᴅɪᴛꜱ & ᴍᴜᴄʜ ᴍᴏʀᴇ ᴜsᴇ /help ᴄᴍᴅ ᴛᴏ ᴋɴᴏᴡ ᴀʟʟ ᴄᴏʀᴇ ғᴜɴᴄᴛɪᴏɴs.</u></b>
<blockquote><b>
<b>• ɴsғᴡ-ᴄᴏɴᴛᴇɴᴛ ꜰɪʟᴛᴇʀ</b>
<b>• ᴅᴇʟᴇᴛᴇs ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇs</b>
<b>• ᴅᴇʟᴇᴛᴇs sʟᴀɴɢғᴜʟ/ɢᴀᴀʟɪ ᴡᴏʀᴅs</b>
<b>• ᴀᴜᴛᴏ ᴍᴇᴅɪᴀ ʀᴇᴍᴏᴠᴀʟ ᴛʜʀᴏᴜɢʜ /setdelay ᴄᴏᴍᴍᴀɴᴅ</b></blockquote>
<blockquote><b>✅ ᴀᴅᴅ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴀᴄᴛɪᴠᴀᴛᴇ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ.</b>
<b>/help ғᴏʀ ᴄᴏᴍᴍᴀɴᴅꜱ</b></blockquote>
"""
    await event.reply(TEXT, buttons=START_OP, parse_mode='html')

@BOT.on(events.NewMessage(pattern='/update'))
async def update_and_restart(event):
    # Check if the user is a SUDO_USER
    if event.sender_id not in SUDO_USERS:
        await event.reply("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    response = await event.reply("ᴜᴘᴅᴀᴛɪɴɢ ᴀɴᴅ ʀᴇsᴛᴀʀᴛɪɴɢ...")
    
    try:
        # Perform git pull to update the code
        os.system("git pull")
        os.system(f"kill -9 {os.getpid()} && bash start.sh")
        await response.edit("ᴜᴘᴅᴀᴛᴇᴅ ᴀɴᴅ ʀᴇsᴛᴀʀᴛᴇᴅ ʟᴏᴄᴀʟʟʏ!")
    except Exception as e:
        await response.edit(f"ғᴀɪʟᴇᴅ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴀɴᴅ ʀᴇsᴛᴀʀᴛ: {e}")

@BOT.on(events.NewMessage(pattern='/stop'))
async def stop_bot(event):
    # Check if the user is a SUDO_USER
    if event.sender_id not in SUDO_USERS:
        await event.reply("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    response = await event.reply("sᴛᴏᴘᴘɪɴɢ ʙᴏᴛ...")
    
    try:
        # Kill the current process
        os.system(f"kill -9 {os.getpid()}")
    except Exception as e:
        LOGS.error(e)
        await response.edit(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴛᴏᴘ ʙᴏᴛ: {e}")
