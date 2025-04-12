from telethon import events
from config import BOT, SUDO_USERS, OWNER_ID, MONGO_URI
from pymongo import MongoClient
import asyncio

client = MongoClient(MONGO_URI)
db = client["billa_guardian"]
users_collection = db["users"]
groups_collection = db["groups"]

@BOT.on(events.NewMessage(pattern="/broadcast"))
async def broadcast(event):
    if event.sender_id not in SUDO_USERS and event.sender_id != OWNER_ID:
        return await event.reply("❌ You are not authorized to use this command.")

    reply = await event.get_reply_message()
    if not reply:
        return await event.reply("Please reply to the message you want to broadcast.")

    users = list(users_collection.find())
    groups = list(groups_collection.find())

    total_users = len(users)
    total_groups = len(groups)

    success_users, failed_users = 0, 0
    success_groups, failed_groups = 0, 0

    await event.reply(f"Broadcasting to {total_users} users and {total_groups} groups...")

    for user in users:
        try:
            await BOT.forward_messages(
                int(user["chat_id"]),
                messages=reply.id,
                from_peer=event.chat_id
            )
            success_users += 1
        except Exception:
            failed_users += 1

    for group in groups:
        try:
            await BOT.forward_messages(
                int(group["chat_id"]),
                messages=reply.id,
                from_peer=event.chat_id
            )
            success_groups += 1
        except Exception:
            failed_groups += 1

    await event.reply(
        f"✅ Broadcast Complete.\n"
        f"Users: {success_users}/{total_users} successful, {failed_users} failed.\n"
        f"Groups: {success_groups}/{total_groups} successful, {failed_groups} failed."
)
