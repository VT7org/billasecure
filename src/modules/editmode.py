from telethon import events
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import PeerChannel, PeerUser
from telethon.errors import ChatAdminRequiredError
from collections import defaultdict
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, OWNER_ID, SUDO_USERS, SUPPORT_ID
from config import BOT
from src.status import *
import time
import re
import html
import logging

message_cache = {}
# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# MongoDB initialization
mongo_BOT = MongoClient(MONGO_URI)
db = mongo_BOT[DB_NAME]
users_collection = db['users']
active_groups_collection = db['active_groups']
sudo_users_collection = db['sudo_users']
authorized_users_collection = db['authorized_users']


# Define a list to store sudo user IDs
SUDO_ID = [6257927828]
sudo_users = SUDO_ID.copy()  # Copy initial SUDO_ID list
sudo_users.append(OWNER_ID)  # Add owner to sudo users list initially


# Track groups where the bot is active
@BOT.on(events.NewMessage(func=lambda e: e.is_group))
async def track_groups(event):
    chat = await event.get_chat()
    group_id = chat.id
    group_name = chat.title or "Unknown Group"

    # Try to get invite link
    try:
        invite = await BOT(ExportChatInviteRequest(group_id))
        invite_link = f"https://t.me/{invite.link.split('/')[-1]}"
    except ChatAdminRequiredError:
        invite_link = "ɴᴏ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴀᴠᴀɪʟᴀʙʟᴇ"
    except Exception as e:
        print(f"Error getting invite link for {group_name}: {e}")
        invite_link = "ɴᴏ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴀᴠᴀɪʟᴀʙʟᴇ"

    # Realtime upsert (update or insert)
    active_groups_collection.update_one(
        {"group_id": group_id},
        {"$set": {
            "group_name": group_name,
            "invite_link": invite_link
        }},
        upsert=True
    )

# Cache messages when they are first sent
@BOT.on(events.NewMessage)
async def cache_message(event):
    if event.message and event.message.text:
        message_cache[(event.chat_id, event.id)] = event.message.text


@BOT.on(events.MessageEdited)
async def check_edit(event):
    try:
        chat = await event.get_chat()
        user = await event.get_sender()

        if not event.message or not event.message.edit_date:
            return

        old_text = message_cache.get((event.chat_id, event.id))
        new_text = event.message.text

        if old_text is not None and old_text == new_text:
            return

        message_cache[(event.chat_id, event.id)] = new_text

        is_channel_msg = getattr(event.message, "post_author", None) is not None or getattr(event.message, "sender_id", None) is None

        if is_channel_msg:
            await event.delete()
            await BOT.send_message(
                chat.id,
                "<blockquote><b>A ᴍᴇssᴀɢᴇ ꜱᴇɴᴛ ᴠɪᴀ ᴄʜᴀɴɴᴇʟ ᴏʀ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴡᴀꜱ ᴇᴅɪᴛᴇᴅ.\nɪᴛ ʜᴀꜱ ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ.</b></blockquote>",
                parse_mode='html'
            )
            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote><b>Dᴇʟᴇᴛᴇᴅ ᴀɴ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ꜱᴇɴᴛ ᴠɪᴀ ᴄʜᴀɴɴᴇʟ ɪɴ <code>{chat.id}</code>.</b></blockquote>",
                parse_mode='html'
            )
            return

        if user is None:
            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote><b>⚠️ ꜰᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴛʀɪᴇᴠᴇ ᴛʜᴇ ꜱᴇɴᴅᴇʀ ᴏꜰ ᴛʜᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇ.\nᴄʜᴀᴛ ɪᴅ: <code>{chat.id}</code>\nᴍᴇꜱꜱᴀɢᴇ ɪᴅ: <code>{event.id}</code></b></blockquote>",
                parse_mode='html'
            )
            return

        user_id = user.id
        user_first_name = html.escape(user.first_name)
        user_mention = f"<a href='tg://user?id={user_id}'>{user_first_name}</a>"

        is_owner = user_id == OWNER_ID
        is_sudo = user_id in sudo_users
        is_authorized = authorized_users_collection.find_one({"user_id": user_id, "group_id": chat.id})

        if is_owner or is_sudo or is_authorized:
            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote>Aᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ {user_mention} ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ ɪɴ <code>{chat.id}</code>.\n<b>Nᴏ ᴀᴄᴛɪᴏɴ ᴡᴀs ᴛᴀᴋᴇɴ.</b></blockquote>",
                parse_mode='html'
            )
            return

        try:
            chat_member = await BOT.get_permissions(chat, user)

            if chat_member.is_admin or chat_member.is_creator:
                user_role = "admin" if chat_member.is_admin else "creator"
                await BOT.send_message(
                    SUPPORT_ID,
                    f"<blockquote>Usᴇʀ {user_mention} is an <b>{user_role}</b> ɪɴ ᴄʜᴀᴛ <code>{chat.id}</code>.\n<b>Nᴏ ᴅᴇʟᴇᴛɪᴏɴ ᴡᴀs ᴘᴇʀғᴏʀᴍᴇᴅ.</b></blockquote>",
                    parse_mode='html'
                )
                return

        except Exception as e:
            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote><b>⚠️ ʙᴏᴛ ɴᴇᴇᴅꜱ ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ᴛᴏ ᴄʜᴇᴄᴋ ᴇᴅɪᴛꜱ\nᴄʜᴀᴛ ɪᴅ: <code>{chat.id}</code>\nᴇʀʀᴏʀ: <code>{e}</code></b></blockquote>",
                parse_mode='html'
            )
            return

        try:
            await event.delete()

            await BOT.send_message(
                chat.id,
                f"<blockquote><b>{user_mention} Jᴜsᴛ ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ.\nɪ ʜᴀᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ɪᴛ.</b></blockquote>",
                parse_mode='html'
            )

            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote><b>Dᴇʟᴇᴛᴇᴅ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀ {user_mention}\nɪɴ ᴄʜᴀᴛ <code>{chat.id}</code>.</b></blockquote>",
                parse_mode='html'
            )

        except Exception as e:
            await BOT.send_message(
                SUPPORT_ID,
                f"<blockquote><b>⚠️ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇ.\nᴄʜᴀᴛ ɪᴅ: <code>{chat.id}</code>\nᴍᴇꜱꜱᴀɢᴇ ɪᴅ: <code>{event.id}</code>\nᴇʀʀᴏʀ: <code>{e}</code></b></blockquote>",
                parse_mode='html'
            )

    except Exception as e:
        await BOT.send_message(
            SUPPORT_ID,
            f"<blockquote><b>⚠️ ᴜɴʜᴀɴᴅʟᴇᴅ ᴇxᴄᴇᴘᴛɪᴏɴ ɪɴ ᴄʜᴇᴄᴋ_ᴇᴅɪᴛ.\nᴇʀʀᴏʀ: <code>{e}</code></b></blockquote>",
            parse_mode='html'
        )

# Add sudo user
@BOT.on(events.NewMessage(pattern='/addsudo'))
async def add_sudo(event):
    user = await event.get_sender()
    chat = await event.get_chat()

    # Check if the user is the owner
    if user.id != OWNER_ID:
        await event.reply("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ  sᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    # Check if a username or user ID is provided
    if not event.pattern_match.group(1):
        await event.reply("Usᴀɢᴇ: /addsudo <ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ᴜsᴇʀ Iᴅ>")
        return

    sudo_user = event.pattern_match.group(1).strip()

    # Resolve the user ID from username if provided
    try:
        if sudo_user.startswith('@'):
            user_entity = await BOT.get_entity(sudo_user)
            sudo_user_id = user_entity.id
        else:
            sudo_user_id = int(sudo_user)
            user_entity = await BOT.get_entity(PeerUser(sudo_user_id))

        # Add sudo user ID to the database if not already present
        if sudo_users_collection.find_one({"user_id": sudo_user_id}):
            await event.reply(f"{user_entity.first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀ sᴜᴅᴏ ᴜsᴇʀ.")
            return

        # Add sudo user to the database
        sudo_users_collection.insert_one({
            "user_id": sudo_user_id,
            "username": user_entity.username,
            "first_name": user_entity.first_name
        })
        await event.reply(f"ᴀᴅᴅᴇᴅ {user_entity.first_name} ᴀs ᴀ sᴜᴅᴏ ᴜsᴇʀ.")
    except Exception as e:
        await event.reply(f"Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ sᴜᴘᴇʀ ᴜsᴇʀ: {e}")

# Remove sudo user
@BOT.on(events.NewMessage(pattern='/rmsudo'))
async def rmsudo(event):
    user = await event.get_sender()
    chat = await event.get_chat()

    # Check if the user is the owner
    if user.id != OWNER_ID:
        await event.reply("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ  sᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    # Check if a username or user ID is provided
    if not event.pattern_match.group(1):
        await event.reply("Usᴀɢᴇ: /rmsudo <ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ᴜsᴇʀ ɪᴅ>")
        return

    sudo_user = event.pattern_match.group(1).strip()

    try:
        if sudo_user.startswith('@'):
            user_entity = await BOT.get_entity(sudo_user)
            sudo_user_id = user_entity.id
        else:
            sudo_user_id = int(sudo_user)
            user_entity = await BOT.get_entity(PeerUser(sudo_user_id))

        # Remove sudo user from the database
        result = sudo_users_collection.delete_one({"user_id": sudo_user_id})
        if result.deleted_count > 0:
            await event.reply(f"Rᴇᴍᴏᴠᴇᴅ {user_entity.first_name} ᴀs ᴀ sᴜᴅᴏ ᴜsᴇʀ.")
        else:
            await event.reply(f"{user_entity.first_name} ɪs ɴᴏᴛ ᴀ sᴜᴅᴏ ᴜsᴇʀ.")
    except Exception as e:
        await event.reply(f"Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ sᴜᴅᴏ ᴜsᴇʀ: {e}")

# List sudo users
@BOT.on(events.NewMessage(pattern='/sudolist'))
async def sudo_list(event):
    user = await event.get_sender()

    # Check if the user is the owner
    if user.id != OWNER_ID:
        await event.reply("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    # Fetch sudo users from MongoDB
    sudo_users_cursor = sudo_users_collection.find({})
    text = "ʟɪsᴛ ᴏғ sᴜᴅᴏ ᴜsᴇʀs:\n"
    count = 1

    for user_data in sudo_users_cursor:
        try:
            user_mention = f"[{user_data['first_name']}](tg://user?id={user_data['user_id']})"
            text += f"{count}. {user_mention}\n"
            count += 1
        except Exception as e:
            await event.reply(f"Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ sᴜᴘᴇʀ ᴜsᴇʀ ᴅᴇᴛᴀɪʟs: {e}")
            return

    if not text.strip():
        await event.reply("Nᴏ sᴜᴘᴇʀ ᴜsᴇʀs ғᴏᴜɴᴅ.")
    else:
        await event.reply(text, parse_mode='markdown')

from functools import wraps
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import PeerUser, ChannelParticipantAdmin, ChannelParticipantCreator

# Decorator to check if user is allowed (admin, sudo, or owner)
def is_admin(func):
    @wraps(func)
    async def wrapper(event):
        user = await event.get_sender()
        chat = await event.get_chat()

        if user.id in SUDO_USERS or user.id == OWNER_ID:
            return await func(event)

        try:
            participant = await BOT(GetParticipantRequest(chat, user))
            if isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
                return await func(event)
            else:
                return await event.reply("🚫 Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        except Exception as e:
            return await event.reply(f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴇᴄᴋ ᴀᴅᴍɪɴ sᴛᴀᴛᴜs: {e}")
    return wrapper

# Authorize a user in a specific group
@BOT.on(events.NewMessage(pattern='/auth(?: |$)(.*)'))
@is_admin
async def auth(event):
    user = await event.get_sender()
    chat = await event.get_chat()

    sudo_user = event.pattern_match.group(1).strip() if event.pattern_match.group(1) else None

    if not sudo_user and not event.is_reply:
        await event.reply("Usᴀɢᴇ: /auth <@ᴜsᴇʀɴᴀᴍᴇ> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ʜɪs/ʜᴇʀ ᴍᴇssᴀɢᴇ.")
        return

    try:
        if not sudo_user and event.is_reply:
            reply = await event.get_reply_message()
            user_entity = await reply.get_sender()
            sudo_user_id = user_entity.id
        elif sudo_user.startswith('@'):
            user_entity = await BOT.get_entity(sudo_user)
            sudo_user_id = user_entity.id
        else:
            sudo_user_id = int(sudo_user)
            user_entity = await BOT.get_entity(PeerUser(sudo_user_id))

        if authorized_users_collection.find_one({"user_id": sudo_user_id, "group_id": chat.id}):
            await event.reply(f"{user_entity.first_name} ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
            return

        authorized_users_collection.insert_one({
            "user_id": sudo_user_id,
            "username": user_entity.username,
            "first_name": user_entity.first_name,
            "group_id": chat.id
        })
        await event.reply(f"✅ {user_entity.first_name} ʜᴀs ʙᴇᴇɴ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
    except Exception as e:
        await event.reply(f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴜᴛʜᴏʀɪᴢᴇ ᴜsᴇʀ: {e}")

# Unauthorize a user in a specific group
@BOT.on(events.NewMessage(pattern='/unauth(?: |$)(.*)'))
@is_admin
async def unauth(event):
    user = await event.get_sender()
    chat = await event.get_chat()

    sudo_user = event.pattern_match.group(1).strip() if event.pattern_match.group(1) else None

    if not sudo_user and not event.is_reply:
        await event.reply("Usᴀɢᴇ: /unauth <@ᴜsᴇʀɴᴀᴍᴇ> ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ʜɪs/ʜᴇʀ ᴍᴇssᴀɢᴇ.")
        return

    try:
        if not sudo_user and event.is_reply:
            reply = await event.get_reply_message()
            user_entity = await reply.get_sender()
            sudo_user_id = user_entity.id
        elif sudo_user.startswith('@'):
            user_entity = await BOT.get_entity(sudo_user)
            sudo_user_id = user_entity.id
        else:
            sudo_user_id = int(sudo_user)
            user_entity = await BOT.get_entity(PeerUser(sudo_user_id))

        if not authorized_users_collection.find_one({"user_id": sudo_user_id, "group_id": chat.id}):
            await event.reply(f"{user_entity.first_name} ɪs ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
            return

        authorized_users_collection.delete_one({"user_id": sudo_user_id, "group_id": chat.id})
        await event.reply(f"✅ {user_entity.first_name} ʜᴀs ʙᴇᴇɴ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
    except Exception as e:
        await event.reply(f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇ ᴜsᴇʀ: {e}")

# List all authorized users in a specific group
@BOT.on(events.NewMessage(pattern='/authlist'))
@is_admin
async def authlist(event):
    chat = await event.get_chat()

    try:
        # Fetch all authorized users for the current group
        authorized_users = authorized_users_collection.find({"group_id": chat.id})

        if not authorized_users:
            await event.reply("Nᴏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.")
            return

        # Prepare the list of authorized users
        user_list = []
        for user in authorized_users:
            user_info = f"• {user.get('first_name', 'Unknown')} (ID: {user['user_id']})"
            if user.get('username'):
                user_info += f" (@{user['username']})"
            user_list.append(user_info)

        # Send the list as a message
        await event.reply(f"🛡️ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ:\n\n" + "\n".join(user_list))
    except Exception as e:
        await event.reply(f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀs: {e}")

# Send bot statistics
@BOT.on(events.NewMessage(pattern='/stats'))
async def send_stats(event):
    user = await event.get_sender()

    if user.id != OWNER_ID:
        await event.reply("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ  ᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    try:
        users_count = users_collection.count_documents({})
        chat_count = active_groups_collection.count_documents({})  # Use correct collection

        stats_msg = f"Tᴏᴛᴀʟ Usᴇʀs: {users_count}\nTᴏᴛᴀʟ Gʀᴏᴜᴘs: {chat_count}\n"
        await event.reply(stats_msg)
    except Exception as e:
        logger.error(f"ᴇʀʀᴏʀ ɪɴ send_stats ғᴜɴᴄᴛɪᴏɴ: {e}")
        await event.reply("Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ sᴛᴀs.")

# List active groups
@BOT.on(events.NewMessage(pattern='/activegc'))
async def list_active_groups(event):
    user = await event.get_sender()

    if user.id != OWNER_ID:
        await event.reply("Yᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        return

    active_groups = list(active_groups_collection.find({}))
    cleaned_groups = []
    removed_count = 0

    for group in active_groups:
        group_id = group.get("group_id")
        if not group_id:
            continue

        try:
            await BOT.get_entity(group_id)
            cleaned_groups.append(group)
        except Exception:
            # Remove from DB if bot not in group
            active_groups_collection.delete_one({"group_id": group_id})
            removed_count += 1

    if not cleaned_groups:
        return await event.reply("Tʜᴇ ʙɪʟʟᴀ ɪs ɴᴏᴛ ᴀᴄᴛɪᴠᴇ ɪɴ ᴀɴʏ ɢʀᴏᴜᴘs (ᴀʟʟ ᴍɪɢʜᴛ ʜᴀᴠᴇ ʀᴇᴍᴏᴠᴇᴅ ᴛʜᴇ ʙᴏᴛ).")

    group_list_msg = "Aᴄᴛɪᴠᴇ ɢʀᴏᴜᴘs ᴡʜᴇʀᴇ ᴛʜᴇ ʙɪʟʟᴀ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ:\n\n"
    for group in cleaned_groups:
        group_name = group.get("group_name", "Unknown Group")
        invite_link = group.get("invite_link", "ɴᴏ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴀᴠᴀɪʟᴀʙʟᴇ")

        if invite_link.startswith("http"):
            group_list_msg += f"• <a href='{invite_link}'>[{group_name}]</a>\n"
        else:
            group_list_msg += f"• {group_name}\n"

    group_list_msg += f"\n🧹 `{removed_count}` ɪɴᴀᴄᴛɪᴠᴇ ɢʀᴏᴜᴘs ᴡᴇʀᴇ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴛʀᴀᴄᴋɪɴɢ."

    await event.reply(group_list_msg, parse_mode='html')
    
# Fetch active groups from MongoDB
def fetch_active_groups_from_db():
    try:
        active_groups = list(active_groups_collection.find({}, {"group_id": 1, "group_name": 1, "invite_link": 1, "_id": 0}))
        return active_groups
    except Exception as e:
        print(f"Fᴀɪʟᴇᴅ ᴛᴏ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ MᴏɴɢᴏDB: {e}")
        return None
