# Copyright 2021 To 2024-present, Author: MrAKTech

import asyncio
import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors import ChatAdminRequired

from MrAKTech.config import Telegram, Domain
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.utils_bot import is_subscribed, is_user_joined, temp, get_time, broadcast_messages
from MrAKTech.tools.txt import tamilxd, BUTTON

# Lock for broadcast operations
lock = asyncio.Lock()


def get_all_media_file_data(m):
    media = m.video or m.document or m.audio
    if media:
        return media.file_id, media.file_unique_id[:6], media.file_name, media.file_size
    else:
        return None, None, None, None


@Client.on_message(filters.command("start"))
async def start(client, message):
    if not await u_db.sis_user_exist(message.from_user.id):
        await u_db.sadd_user(message.from_user.id)
        await client.send_message(
            Telegram.SULOG_CHANNEL,
            f"#NewUser \nID - `{message.from_user.id}` \nNᴀᴍᴇ - {message.from_user.mention}",
        )
    usr_cmd = message.text.split("_")[-1]
    if usr_cmd == "/start":
        if not await is_user_joined(client, message, Telegram.AUTH_CHANNEL2):
            return
        await message.reply_text(
            text=f" <b> Hᴇʟʟᴏ {message.from_user.first_name} \n\nɪ ᴀᴍ ᴀ ʙᴏᴛ ᴛʜᴀᴛ ᴘʀᴏᴠɪᴅᴇs ғɪʟᴇ ᴀᴄᴄᴇss ғᴏʀ @MrAKStreamBot ʙᴏᴛ. </b>\n\n/donation",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('📢 𝙼𝙰𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.MAIN),
                        InlineKeyboardButton('⚡ 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.AUTH_CHANNEL3)
                    ],[
                        InlineKeyboardButton('📢 𝙼𝙾𝚅𝙸𝙴 𝙶𝚁𝙾𝚄𝙿', url= Telegram.AUTH_GROUP)
               ],
                    [
                        InlineKeyboardButton("❤️ Create Like This Link ❤️", url=Telegram.BOTNAME),
                    ],
                    [
                        InlineKeyboardButton("🔰 Join Now 🔰", url="https://t.me/+1EgUhBbcIHQzMDU1"),
                    ]
                ]
            ),
        )
    else:
        if Telegram.AUTH_CHANNEL2 and not await is_subscribed(client, message, Telegram.AUTH_CHANNEL2):
            try:
                invite_link = await client.create_chat_invite_link(
                    int(Telegram.AUTH_CHANNEL2), creates_join_request=True
                )
            except ChatAdminRequired:
                await message.reply_text("MAKE SURE BOT IS ADMIN IN FORCESUB CHANNEL")
                return
            btn = [[InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 1 🔰", url= Telegram.AUTH_GROUP2),
                    InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 2 🔰", url= Telegram.AUTH_CHANNEL3)],
                    [InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 3 🔰", url= Telegram.AUTH_GROUP),
                    InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 4 🔰", url=invite_link.invite_link)],
                [
                    InlineKeyboardButton(
                        "🔄 Refresh / Try Again",
                        url=f"https://t.me/{(await client.get_me()).username}?start=MrAK_{usr_cmd}",
                    )
                ],
            ]
            try:
                return await client.send_message(
                    chat_id=message.from_user.id,
                    text=tamilxd.FORCE_SUB_TEXT.format(message.from_user.mention),
                    reply_markup=InlineKeyboardMarkup(btn),
                )
            except Exception as e:
                print(f"Force Sub Text Error\n{e}")
                return await client.send_message(
                    chat_id=message.from_user.id,
                    text=tamilxd.FORCE_SUB_TEXT.format(message.from_user.mention),
                    reply_markup=InlineKeyboardMarkup(btn),
                )
            #
        get_msg = await client.get_messages(
            chat_id=Telegram.FLOG_CHANNEL, message_ids=int(usr_cmd)
        )
        data = get_all_media_file_data(get_msg)
        stream_link = f"{Domain.TEMP_URL}watch/{get_msg.id}?hash={data[1]}"
        #

        tamil1 = await message.reply_text(
            "<b>Your 📁 File will be automatically deleted in ⏰ 10 minutes.↗ Forward it anywhere or save it privately before downloading</b>\n",
            disable_web_page_preview=True,
            quote=True,
        )

        tamil2 = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=data[0],
            caption=tamilxd.STREAM_TXT.format(caption=data[2].replace("_", " "), stream_link=stream_link),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📽 Sᴛʀᴇᴀᴍ & Dᴏᴡɴʟᴏᴀᴅ 💾", url=stream_link)]]
            ),
        )
        await asyncio.sleep(1800)
        await tamil1.delete()
        await tamil2.delete()
        await message.delete()


@Client.on_message(filters.command(["donate", "donation"]))
async def donate(app, message):
    await message.reply_text(
        text=tamilxd.DONATE_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=BUTTON.DONATE_BUTTONS,
        quote=True,
    )

@Client.on_callback_query(filters.regex(pattern=r"donate"))
async def donate_cb(_, query):
    await query.message.edit(
        text=tamilxd.DONATE_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=BUTTON.DONATE_BUTTONS,
    )
    await query.answer()

@Client.on_callback_query(filters.regex(pattern=r"close"))
async def close_cb(_, query):
    await query.message.delete()
    await query.answer()


# ------------------------[ BROADCAST FUNCTIONALITY ]--------------------------- #

@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    await query.message.edit("Trying to cancel broadcasting...")
    temp.BROADCAST_CANCEL = True

@Client.on_message(filters.command(["broadcast", "bcast", "pin_broadcast", "pin_bcast"]) & filters.private & filters.user(list(Telegram.OWNER_ID)) & filters.reply)
async def broadcast_to_users(bot, message):
    if lock.locked():
        return await message.reply('Currently broadcast processing, Wait for complete.')
    
    if message.command[0] in ['pin_broadcast', 'pin_bcast']:
        pin = True
    else:
        pin = False
    
    msg = await message.reply_text('Broadcasting your message...')
    broadcast_msg = message.reply_to_message
    total_users = await u_db.stotal_users_count()
    done = 0
    blocked = 0
    failed = 0
    success = 0
    start_time = time.time()
    temp.BROADCAST_CANCEL = False

    async with lock:
        async for user in await u_db.sget_all_users():
            if temp.BROADCAST_CANCEL:
                break
            sts = await broadcast_messages(user['id'], broadcast_msg, pin)
            if sts == "Success":
                success += 1
            elif sts == "Blocked":
                blocked += 1
            elif sts == "Failed":
                failed += 1
            done += 1
            if done % 20 == 0:
                btn = [[
                    InlineKeyboardButton('CANCEL', callback_data='broadcast_cancel')
                ]]
                await msg.edit(f"Broadcast Processing...\n\nTotal Users: <code>{total_users}</code>\nCompleted: <code>{done} / {total_users}</code>\nSuccess: <code>{success}</code>\nBlocked: <code>{blocked}</code>\nFailed: <code>{failed}</code>", reply_markup=InlineKeyboardMarkup(btn))
        time_taken = get_time(time.time() - start_time)
        await msg.edit(f"Broadcast Completed.\nTime Taken: <code>{time_taken}</code>\n\nTotal Users: <code>{total_users}</code>\nCompleted: <code>{done} / {total_users}</code>\nSuccess: <code>{success}</code>\nBlocked: <code>{blocked}</code>\nFailed: <code>{failed}</code>")

@Client.on_message(filters.command("stats") & filters.private & filters.user(list(Telegram.OWNER_ID)))
async def get_stats(bot, message):
    total_users = await u_db.stotal_users_count()
    await message.reply_text(
        f"**📊 Storage Bot Statistics**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"🤖 **Bot:** @{(await bot.get_me()).username}",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command("help") & filters.private & filters.user(list(Telegram.OWNER_ID)))
async def admin_help(bot, message):
    help_text = """
**🔧 Storage Bot Admin Commands**

📢 **Broadcast Commands:**
• `/broadcast` - Broadcast message to all users (reply to a message)
• `/bcast` - Same as broadcast
• `/pin_broadcast` - Broadcast and pin message for users
• `/pin_bcast` - Same as pin_broadcast

📊 **Statistics:**
• `/stats` - Get bot statistics

ℹ️ **Help:**
• `/help` - Show this help message

**Note:** All broadcast commands require you to reply to the message you want to broadcast.
    """
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
