import asyncio
from datetime import datetime, timedelta
from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.types import ChannelParticipantsAdmins, User
from config import BOT, OWNER_ID
from src.vxcore import get_collections, logger

tagging_status = {}
last_used = {}
MAX_TAG_LIMIT = 100
COOLDOWN_SECONDS = 4

sudo_users = get_collections().get("sudo_users")

async def get_tag_string(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

async def is_admin_or_owner(event):
    try:
        user = await event.client.get_permissions(event.chat_id, event.sender_id)
        return user.is_admin or event.sender_id == OWNER_ID
    except Exception:
        return False

async def is_sudo(user_id):
    try:
        return await sudo_users.find_one({"_id": user_id}) is not None or user_id == OWNER_ID
    except Exception:
        return False

async def is_on_cooldown(user_id, cmd, cooldown_seconds=COOLDOWN_SECONDS):
    now = datetime.utcnow()
    key = f"{user_id}:{cmd}"
    if key in last_used and (now - last_used[key]).total_seconds() < cooldown_seconds:
        return True
    last_used[key] = now
    return False

async def batch_send_tags(event, users, batch_size=10, delay=2, reply_msg=None, silent=False):
    chat_id = event.chat_id
    tagging_status[chat_id] = True
    total_tagged = 0
    batch = []

    for user in users:
        if not tagging_status.get(chat_id):
            return await event.respond(f"✅ Tᴀɢɢɪɴɢ sᴛᴏᴘᴘᴇᴅ. Tᴏᴛᴀʟ ᴛᴀɢɢᴇᴅ: {total_tagged}")

        try:
            tag = await get_tag_string(user)
            batch.append(tag)

            if len(batch) == batch_size:
                msg = "\n".join(batch)
                if reply_msg:
                    sender_name = getattr(reply_msg.sender, 'first_name', 'Anonymous')
                    msg += f"\n\n➡️ {sender_name} says: {reply_msg.text}"
                await BOT.send_message(
                    chat_id, msg, parse_mode="md", reply_to=reply_msg.id if reply_msg else event.id, silent=silent
                )
                total_tagged += len(batch)
                batch = []
                await asyncio.sleep(delay)

        except FloodWaitError as f:
            await asyncio.sleep(f.seconds)
        except Exception as e:
            logger.error(f"Tagging error: {e}")
            continue

    if batch:
        msg = "\n".join(batch)
        if reply_msg:
            sender_name = getattr(reply_msg.sender, 'first_name', 'Anonymous')
            msg += f"\n\n➡️ {sender_name} says: {reply_msg.text}"
        await BOT.send_message(
            chat_id, msg, parse_mode="md", reply_to=reply_msg.id if reply_msg else event.id, silent=silent
        )
        total_tagged += len(batch)

    await event.respond(f"✅ Tᴀɢɢɪɴɢ ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ. Tᴏᴛᴀʟ ᴜsᴇʀs ᴛᴀɢɢᴇᴅ: {total_tagged}")

@BOT.on(events.NewMessage(pattern="/utag(?:\s+silent)?"))
async def tag_all(event):
    if event.is_private:
        return await event.reply("❌ Usᴇʀs-ᴛᴀɢɢᴇʀ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ᴀ ɢʀᴏᴜᴘ-ᴄʜᴀᴛ.")

    if not await is_admin_or_owner(event):
        return await event.reply("⚠️ Oɴʟʏ ᴀᴅᴍɪɴs ᴀɴᴅ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")

    if await is_on_cooldown(event.sender_id, "/utag"):
        return await event.reply("⏳ Sʟᴏᴡ ᴅᴏᴡɴ! Tʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ᴍᴏᴍᴇɴᴛ.")

    silent = "silent" in event.raw_text.lower()
    reply_msg = await event.get_reply_message()

    try:
        users = [user async for user in BOT.iter_participants(event.chat_id)]
        if len(users) > MAX_TAG_LIMIT:
            users = users[:MAX_TAG_LIMIT]
            await event.reply(f"⚠️ Tᴏᴏ ᴍᴀɴʏ ᴜsᴇʀs. Oɴʟʏ ᴛᴀɢɢɪɴɢ ғɪʀsᴛ {MAX_TAG_LIMIT}.")
    except Exception as e:
        return await event.reply(f"⚠️ Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴜsᴇʀs: {e}")

    await batch_send_tags(event, users, reply_msg=reply_msg, silent=silent)

@BOT.on(events.NewMessage(pattern="/atag(?:\s+silent)?"))
async def tag_admins(event):
    if event.is_private:
        return await event.reply("❌ ᴀᴅᴍɪɴ-ᴛᴀɢ ᴏɴʟʏ ᴡᴏʀᴋs ɪɴ ᴀ ɢʀᴏᴜᴘ ᴄʜᴀᴛ.")

    if not await is_admin_or_owner(event):
        return await event.reply("⚠️ Oɴʟʏ ᴀᴅᴍɪɴs ᴀɴᴅ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")

    if await is_on_cooldown(event.sender_id, "/atag"):
        return await event.reply("⏳ Pʟᴇᴀsᴇ ᴡᴀɪᴛ ʙᴇғᴏʀᴇ ᴛᴀɢɢɪɴɢ ᴀɢᴀɪɴ.")

    silent = "silent" in event.raw_text.lower()
    reply_msg = await event.get_reply_message()

    try:
        users = [user async for user in BOT.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins)]
    except Exception as e:
        return await event.reply(f"⚠️ Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴀᴅᴍɪɴs: {e}")

    await batch_send_tags(event, users, reply_msg=reply_msg, silent=silent)

@BOT.on(events.NewMessage(pattern="/stop"))
async def stop_tagging(event):
    if not await is_admin_or_owner(event):
        return await event.reply("⚠️ Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ sᴛᴏᴘ ᴛᴀɢɢɪɴɢ.")

    chat_id = event.chat_id
    if tagging_status.get(chat_id):
        tagging_status[chat_id] = False
        await event.reply("✅ ᴛᴀɢɢɪɴɢ ᴘʀᴏᴄᴇss sᴛᴏᴘᴘᴇᴅ.")
    else:
        await event.reply("ℹ️ Nᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀɢɢɪɴɢ ᴛᴏ sᴛᴏᴘ.")
