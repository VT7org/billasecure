from telethon import events
from config import BOT, SUPPORT_ID
import logging

logger = logging.getLogger(__name__)

@BOT.on(events.ChatAction)
async def handler(event):
    me = await BOT.get_me()
    bot_id = me.id

    if event.user_joined or event.user_added:
        if event.user_id == bot_id:
            added_by = event.action_message.from_id
            added_by_name = "Someone"
            if added_by:
                try:
                    user = await BOT.get_entity(added_by)
                    added_by_name = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
                except Exception:
                    pass
            msg = f"⚡️ <b>Bɪʟʟᴀ Gᴜᴀʀᴅɪᴀɴ ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ!</b>\n\n"
            msg += f"<b>Gʀᴏᴜᴘ:</b> {event.chat.title}\n<b>Gʀᴏᴜᴘ ID:</b> `{event.chat_id}`\n"
            msg += f"<b>ᴀᴅᴅᴇᴅ ʙʏ:</b> {added_by_name}"
            await event.reply(msg, parse_mode='html')
            await BOT.send_message(SUPPORT_ID, msg, parse_mode='html')
            logger.info(f"Bot added to {event.chat.title} ({event.chat_id}) by {added_by_name}")

    elif event.user_left or event.user_kicked:
        if event.user_id == bot_id:
            removed_by = event.action_message.from_id
            removed_by_name = "Someone"
            if removed_by:
                try:
                    user = await BOT.get_entity(removed_by)
                    removed_by_name = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
                except Exception:
                    pass
            msg = f"⚠️ <b>Bɪʟʟᴀ Gᴜᴀʀᴅɪᴀɴ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴀ ɢʀᴏᴜᴘ!</b>\n\n"
            msg += f"<b>Gʀᴏᴜᴘ:</b> {event.chat.title}\n<b>Gʀᴏᴜᴘ ID:</b> `{event.chat_id}`\n"
            msg += f"<b>ʀᴇᴍᴏᴠᴇᴅ ʙʏ:</b> {removed_by_name}"
            await BOT.send_message(SUPPORT_ID, msg, parse_mode='html')
            logger.info(f"Bot removed from {event.chat.title} ({event.chat_id}) by {removed_by_name}")
