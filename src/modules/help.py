from telethon import events
from telethon.tl.custom import Button
from config import BOT

media_msg = f"""
**•─╼⃝𖠁 ᴍᴇᴅɪᴀ ɢ ᴄᴏᴍᴍᴀɴᴅꜱ: 𖠁⃝╾─•**

🔸 ᴍᴀɴʏ ᴄᴏᴍᴍᴀɴᴅꜱ ᴏᴘᴇʀᴀᴛᴇ ɪɴ ᴀ ᴘᴀꜱꜱɪᴠᴇ ᴏʀ ᴀᴜᴛᴏᴍᴀᴛᴇᴅ ᴍᴀɴɴᴇʀ

🔸/setdelay - <ᴛɪᴍᴇ ɪɴ ᴍɪɴᴜᴛᴇ> ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴍᴇᴅɪᴀ ɪɴ ᴄʜᴀᴛ ɪɴ ᴀ ᴄᴜsᴛᴏᴍ ᴘᴇʀɪᴏᴅ ᴏғ ᴛɪᴍᴇ

"""

edit_msg = f"""
**•─╼⃝𖠁 ᴇᴅɪᴛ ɢ ᴄᴏᴍᴍᴀɴᴅs: 𖠁⃝╾─•**

🔸 /auth - ᴀᴜᴛʜ ᴀ ᴜꜱᴇʀ ɪɴ ᴄʜᴀᴛ ᴛᴏ ᴘʀᴇᴠᴇɴᴛ ᴅᴇʟᴇᴛɪᴏɴ !!

🔸 /unauth - ᴜɴᴀᴜᴛʜ ᴀ ᴜꜱᴇʀ ᴛᴏ ᴀʟʟᴏᴡ ᴍᴇꜱꜱᴀɢᴇ !!

🔸 /authusers - ꜱʜᴏᴡꜱ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ !! (ᴏᴡɴᴇʀ ᴏɴʟʏ)

🔸 /atag -  ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴍᴇɴᴛɪᴏɴs ᴏʀ ᴛᴀɢ ᴀᴅᴍɪɴs ᴏɴʟʏ ᴏғ ᴛʜᴀᴛ ɢʀᴏᴜᴘ !!

🔸 /utag - ᴛᴏ ᴛᴀɢ ᴏʀ ᴄʀᴇᴀᴛᴇ ᴍᴇɴᴛɪᴏɴs ᴛᴏ ᴀʟʟ ᴜsᴇʀs ᴏғ ɢʀᴏᴜᴘ !!

🔸 /stop - ᴛᴏ ᴀʙᴏʀᴛ ᴏʀ sᴛᴏᴘ ᴛʜᴇ ᴛᴀɢɢɪɴɢ ᴘʀᴏᴄᴇss ɪᴍᴍᴇᴅɪᴀᴛᴇʟʏ !!

🔸 /stats - ꜱᴛᴀᴛɪᴛɪᴄꜱ ᴏғ ʙɪʟʟᴀ ɢᴜᴀʀᴅɪᴀɴ !!

🔸 /activegc - ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ɢᴄ'ꜱ ᴡʜᴇʀᴇ ʙɪʟʟᴀ ɪꜱ !! (ᴏᴡɴᴇʀ/sᴜᴅᴏ ᴏɴʟʏ)

🔸 /reload -  ʀᴇʟᴏᴀᴅs ᴀᴅᴍɪɴ ʟɪsᴛ ᴏғ ɢʀᴏᴜᴘ-ᴄʜᴀᴛs !! (ᴀᴅᴍɪɴ ᴏɴʟʏ)

🔸/pretender - ᴏɴ/ᴏғғ ᴛᴇʟʟs ᴡʜɪᴄʜ ᴜsᴇʀ ᴄʜᴀɴɢᴇᴅ ᴛʜᴇɪʀ ɴᴀᴍᴇ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴡɪᴛʜɪɴ ɢʀᴏᴜᴘ !!
"""       

START_OP = [
    [
      Button.inline("• ᴍᴇᴅɪᴀ ɢᴜᴀʀᴅx •", data="media"),
      Button.inline("• ᴇᴅɪᴛ ɢᴜᴀʀᴅx •", data="edit")
    ],
    [
      Button.url("ᴜᴘᴅᴀᴛᴇꜱ", "https://t.me/BillaSpace")
    ]
  ]

@BOT.on(events.NewMessage(pattern="/help"))
async def start(event):
    KEX = await event.client.get_me()
    bot_name = KEX.first_name

    if event.is_private:
        TEXT = f"""
<b>✨ •─╼⃝𖠁 ʜᴇʟᴘ ᴍᴇɴᴜ 𖠁⃝╾─• ✨</b>
"""
        await event.respond(TEXT, buttons=START_OP, parse_mode='html')
    else:
        TEXT = "ᴄᴏɴᴛᴀᴄᴛ ᴍᴇ ɪɴ ᴘᴍ ꜰᴏʀ ʜᴇʟᴘ!"
        BUTTON = [[Button.url("ʜᴇʟᴘ", f"https://t.me/BillaGuardianbot?start=help")]]
        await event.reply(TEXT, buttons=BUTTON, parse_mode='html')


@BOT.on(events.CallbackQuery(pattern=r"media"))
async def help_media(event):
    await event.edit(media_msg,
          buttons=[[Button.inline("🔙 ʙᴀᴄᴋ", data="help_back"),],],
          )

@BOT.on(events.CallbackQuery(pattern=r"edit"))
async def help_edit(event):
    await event.edit(edit_msg,
        buttons=[[Button.inline("🔙 ʙᴀᴄᴋ", data="help_back"),],],
      )

@BOT.on(events.CallbackQuery(pattern=r"help_back"))
async def help_back(event):
    TEXT = f"""
<b>✨ •─╼⃝𖠁 ʜᴇʟᴘ ᴍᴇɴᴜ 𖠁⃝╾─• ✨</b>
"""
    await event.edit(TEXT, buttons=START_OP, parse_mode='html')

@BOT.on(events.NewMessage(pattern="/start help"))
async def start_help(event):
    if event.is_private:
        TEXT = f"""
<b>✨ •─╼⃝𖠁 ʜᴇʟᴘ ᴍᴇɴᴜ 𖠁⃝╾─• ✨</b>
"""
        await event.respond(TEXT, buttons=START_OP, parse_mode='html')
        return
