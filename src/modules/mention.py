import asyncio
from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.types import ChannelParticipantsAdmins, User
from config import BOT

tagging_status = {}

async def get_tag_string(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

async def batch_send_tags(event, users, batch_size=10, delay=2, reply_msg=None):
    chat_id = event.chat_id
    tagging_status[chat_id] = True
    total_tagged = 0
    batch = []

    for user in users:
        if not tagging_status.get(chat_id):
            return await event.respond(f"✅ Tagging stopped. Total tagged: {total_tagged}")

        try:
            tag = await get_tag_string(user)
            batch.append(tag)

            if len(batch) == batch_size:
                msg = "\n".join(batch)
                if reply_msg:
                    sender_name = getattr(reply_msg.sender, 'first_name', 'Anonymous')
                    msg += f"\n\n➡️ {sender_name} says: {reply_msg.text}"
                await BOT.send_message(
                    chat_id, msg, parse_mode="md", reply_to=reply_msg.id if reply_msg else event.id
                )
                total_tagged += len(batch)
                batch = []
                await asyncio.sleep(delay)

        except FloodWaitError as f:
            await asyncio.sleep(f.seconds)
        except Exception:
            continue

    if batch:
        msg = "\n".join(batch)
        if reply_msg:
            sender_name = getattr(reply_msg.sender, 'first_name', 'Anonymous')
            msg += f"\n\n➡️ {sender_name} says: {reply_msg.text}"
        await BOT.send_message(
            chat_id, msg, parse_mode="md", reply_to=reply_msg.id if reply_msg else event.id
        )
        total_tagged += len(batch)

    await event.respond(f"✅ Tagging completed. Total users tagged: {total_tagged}")

@BOT.on(events.NewMessage(pattern="/utag"))
async def tag_all(event):
    if event.is_private:
        return await event.reply("❌ Use this in a group.")

    reply_msg = await event.get_reply_message()
    try:
        users = [user async for user in BOT.iter_participants(event.chat_id)]
    except Exception as e:
        return await event.reply(f"⚠️ Failed to fetch users: {e}")

    await batch_send_tags(event, users, reply_msg=reply_msg)

@BOT.on(events.NewMessage(pattern="/atag"))
async def tag_admins(event):
    if event.is_private:
        return await event.reply("❌ Use this in a group.")

    reply_msg = await event.get_reply_message()
    try:
        users = [user async for user in BOT.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins)]
    except Exception as e:
        return await event.reply(f"⚠️ Failed to fetch admins: {e}")

    await batch_send_tags(event, users, reply_msg=reply_msg)

@BOT.on(events.NewMessage(pattern="/stop"))
async def stop_tagging(event):
    chat_id = event.chat_id
    if tagging_status.get(chat_id):
        tagging_status[chat_id] = False
        await event.reply("✅ Tagging process stopped.")
    else:
        await event.reply("There's no active tagging to stop.")
