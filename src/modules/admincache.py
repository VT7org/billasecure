# src/modules/admincache.py

from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
from config import BOT
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
        return await event.reply("❌ This command only works in groups.")
    
    await update_admins(event.chat_id)
    await event.reply("♻️ Aᴅᴍɪɴs ᴄᴀᴄʜᴇ ʀᴇʟᴏᴀᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")

@BOT.on(events.ChatAction)
async def handle_chat_action(event):
    if not (event.is_group or event.is_channel):
        return

    # Clear admin cache on any possible change
    if event.user_added or event.user_joined or event.user_kicked or event.user_left or \
       getattr(event, "promoted", False) or getattr(event, "demoted", False) or \
       hasattr(event, "new_rights") or hasattr(event, "prev_rights"):
        await update_admins(event.chat_id)
