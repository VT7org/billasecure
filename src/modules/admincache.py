# src/modules/admincache.py
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
from config import BOT
import asyncio
from vxcore import admin_cache

async def update_admins(chat_id):
    try:
        admins = await BOT.get_participants(chat_id, filter=ChannelParticipantsAdmins)
        admin_ids = [admin.id for admin in admins]
        admin_cache[chat_id] = admin_ids
    except Exception:
        pass

@BOT.on(events.NewMessage(pattern="/reload"))
async def reload_admin_cache(event):
    if not (event.is_group or event.is_channel):
        return await event.reply("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ɢʀᴏᴜᴘs.")
    
    await update_admins(event.chat_id)
    await event.reply("♻️ ᴀᴅᴍɪɴ ᴄᴀᴄʜᴇ ʀᴇʟᴏᴀᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.")

# Auto-update on admin change or bot added
@BOT.on(events.ChatAction)
async def handle_chat_action(event):
    if not (event.is_group or event.is_channel):
        return

    if event.user_added or event.user_joined or event.user_kicked:
        return  # skip joins

    if event.promoted or event.demoted or event.added_by or event.is_channel:
        await update_admins(event.chat_id)
