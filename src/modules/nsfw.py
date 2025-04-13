import re
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError
from telethon.tl.types import PeerChannel, PeerChat
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import os
import asyncio
import config
from config import BOT

SPOILER = config.SPOILER_MODE
slangf = 'slang_words.txt'

# Load slang words from the text file into a set for efficient lookups
with open(slangf, 'r') as f:
    slang_words = set(line.strip().lower() for line in f)

# Set up the image classification model for NSFW detection
model_name = "AdamCodd/vit-base-nsfw-detector"
feature_extractor = AutoImageProcessor.from_pretrained(model_name, use_fast=True)
model = AutoModelForImageClassification.from_pretrained(model_name)

# Function to process the image and detect NSFW content
def process_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = feature_extractor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            return torch.argmax(logits, dim=-1).item() == 1  # 1 for NSFW, 0 for safe
    except Exception as e:
        print(f"ᴇʀʀᴏʀ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ɪᴍᴀɢᴇ: {e}")
        return False

# Function to check if the media is NSFW (calls the image processing function in a separate thread)
async def check_nsfw_media(file_path):
    return await asyncio.to_thread(process_image, file_path)

# Event handler for media (photos) in groups
@BOT.on(events.NewMessage(func=lambda e: e.is_group and (e.photo)))
async def media_handler(event):
    try:
        file_path = await event.download_media()
        nsfw = await check_nsfw_media(file_path)

        if nsfw:
            name = event.sender.first_name
            try:
                await event.delete()  # Delete the NSFW message
            except Exception:
                pass
            warning_msg = await event.respond(f"**⚠️ ɴꜱꜰᴡ ᴅᴇᴛᴇᴄᴛᴇᴅ**\n{name}", parse_mode="md")

            # If spoiler mode is enabled, send a spoiler message
            if SPOILER:
                spoiler_msg = await event.respond("||ʏᴏᴜʀ ᴍᴇᴅɪᴀ ᴡᴀꜱ ʀᴇᴍᴏᴠᴇᴅ!!||", parse_mode="md")
                await asyncio.sleep(60)
                await spoiler_msg.delete()

            await asyncio.sleep(60)
            await warning_msg.delete()

        if file_path and os.path.exists(file_path):
            os.remove(file_path)  # Clean up the downloaded file
    except Exception as e:
        print(f"ᴇʀʀᴏʀ: {e}")

# Compile regex pattern to match slang words
slang_pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in slang_words) + r')\b', re.IGNORECASE)

# Event handler for detecting and censoring slang in messages
@BOT.on(events.NewMessage(pattern=None))
async def slang(event):
    if event.is_group:
        try:
            sender = await event.client.get_permissions(event.chat_id, event.sender_id)
            is_admin = sender.is_admin or sender.is_creator  # Check if the sender is an admin
        except (ChatAdminRequiredError, UserNotParticipantError):
            is_admin = False

        if not is_admin:
            sentence = event.raw_text
            sent = re.sub(r'\W+', ' ', sentence)  # Replace non-alphanumeric characters with space
            isslang = False

            # Check each word for slang words
            for word in sent.split():
                if word.lower() in slang_words:
                    isslang = True
                    try:
                        await event.delete()  # Delete message if slang word is found
                    except Exception:
                        pass
                    # Replace slang word with spoiler format including space before and after
                    sentence = sentence.replace(word, f'|| {word} ||')

            if isslang and SPOILER:
                name = (await event.get_sender()).first_name
                msgtxt = (
                    f"**{name}, ʏᴏᴜʀ ᴍᴇssᴀɢᴇ ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ ᴅᴜᴇ ᴛᴏ ᴜsᴇ "
                    f"ᴏғ ɪɴᴀᴘᴘʀᴏᴘɪᴀᴛᴇ ᴏʀ ᴀʙᴜsɪᴠɪɴɢ ʟᴀɴɢᴜᴀɢᴇ (sʟᴀɴɢ ᴡᴏʀᴅs).**\n\n"
                    f"**ʜᴇʀᴇ ɪs ᴀ ᴄᴇɴsᴏʀᴇᴅ ᴠᴇʀsɪᴏɴ ᴏғ ʏᴏᴜʀ ᴀʙᴜsɪᴠᴇ ᴍsɢ:**\n\n{sentence}"
                )
                await event.reply(msgtxt, parse_mode="md")
