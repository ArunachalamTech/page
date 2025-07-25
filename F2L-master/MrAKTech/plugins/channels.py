# (c) @MrAKTech

import asyncio
import random

from pyrogram import filters, enums
from pyrogram.errors import FloodWait, PeerIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from MrAKTech import StreamBot
from MrAKTech.config import Telegram, Domain
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.human_readable import humanbytes
from MrAKTech.tools.file_properties import get_name, get_hash, get_media_file_size
from MrAKTech.tools.utils_bot import get_shortlink
from MrAKTech.tools.extract_info import smart_replace_placeholders_in_caption, create_safe_format_dict


@StreamBot.on_chat_join_request(filters.group | filters.channel & ~filters.private)
async def approve(_, m: Message):
    op = m.chat
    kk = m.from_user
    try:
        await StreamBot.approve_chat_join_request(op.id, kk.id)
        await StreamBot.send_message(
            kk.id,
            "**Hello {}!\n\n Your Request To {} was Approved**".format(
                m.from_user.mention, m.chat.title
            ),
        )
    except PeerIdInvalid as e:
        print(f"{kk.id} isn't start bot(means Channel & group) Err : {e}")
    except Exception as err:
        print(str(err))


@StreamBot.on_message(
    filters.channel
    & ~filters.group
    & (filters.document | filters.video)
    & ~filters.forwarded,
    group=-1,
)
async def channel_receive_handler(bot, msg):
    if await u_db.is_channel_exist(msg.chat.id):
        try:
            log_msg = await msg.forward(chat_id=Telegram.FLOG_CHANNEL)
            file_caption = f"{msg.caption}"
            storage = f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{log_msg.id}"
            online_link = f"{random.choice(Domain.CLOUDFLARE_URLS)}watch/{str(log_msg.id)}?hash={get_hash(log_msg)}"
            down_link = f"{random.choice(Domain.CLOUDFLARE_URLS)}dl/{str(log_msg.id)}?hash={get_hash(log_msg)}"
            high_link = f"{random.choice(Domain.MRAKFAST_URLS)}dl/{str(log_msg.id)}?hash={get_hash(log_msg)}"
            settings = await u_db.get_chl_settings(msg.chat.id)
            await log_msg.reply_text(
                text=f"**Channel Name:** `{msg.chat.title}`\n**CHANNEL ID:** `{msg.chat.id}`\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {online_link}\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {high_link}\n**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** {storage}",
                quote=True,
            )
            if settings["method"] == "Button":
                if settings["url"] and settings["api"]:
                    await bot.edit_message_reply_markup(
                        chat_id=msg.chat.id,
                        message_id=msg.id,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "Dᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥",
                                        url=await get_shortlink(
                                            msg.chat.id, online_link
                                        ),
                                    )
                                ]
                            ]
                        ),
                    )
                else:
                    await bot.edit_message_reply_markup(
                        chat_id=msg.chat.id,
                        message_id=msg.id,
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥", url=online_link)]]
                        ),
                    )
            elif settings["method"] == "Caption":
                # Extract quality, season, and episode information for channels
                file_name = get_name(log_msg) or ""
                channel_caption = settings["caption"]
                
                # Use smart extraction that combines filename and original caption data
                channel_caption = smart_replace_placeholders_in_caption(channel_caption, file_name, file_caption)
                
                if settings["url"] and settings["api"]:
                    # Create basic format dictionary for shortlink version
                    basic_format_dict = {
                        "file_name": "" if get_name(log_msg) is None else get_name(log_msg),
                        "caption": "" if file_caption is None else file_caption,
                        "file_size": (
                            ""
                            if humanbytes(get_media_file_size(msg)) is None
                            else humanbytes(get_media_file_size(msg))
                        ),
                        "download_link": (
                            ""
                            if await get_shortlink(msg.chat.id, down_link) is None
                            else await get_shortlink(msg.chat.id, down_link)
                        ),
                        "fast_link": (
                            ""
                            if await get_shortlink(msg.chat.id, high_link) is None
                            else await get_shortlink(msg.chat.id, high_link)
                        ),
                        "stream_link": (
                            ""
                            if await get_shortlink(msg.chat.id, online_link) is None
                            else await get_shortlink(msg.chat.id, online_link)
                        ),
                        "storage_link": (
                            ""
                            if await get_shortlink(msg.chat.id, storage) is None
                            else await get_shortlink(msg.chat.id, storage)
                        ),
                    }
                    
                    # Create safe format dictionary with all placeholders
                    safe_format_dict = create_safe_format_dict(basic_format_dict, file_name, file_caption, chat_id=msg.chat.id)
                    
                    # Generate web_link for page mode
                    from MrAKTech.tools.extract_info import generate_web_link_async
                    web_link = await generate_web_link_async(
                        chat_id=msg.chat.id,
                        filename=file_name,
                        format_dict=safe_format_dict
                    )
                    safe_format_dict['web_link'] = web_link
                    
                    # Format caption and ensure it's not empty
                    formatted_caption = channel_caption.format(**safe_format_dict)
                    if not formatted_caption or not formatted_caption.strip():
                        formatted_caption = f"📁 {file_name}\n📥 Download: {download_link}"
                    
                    await bot.edit_message_caption(
                        chat_id=msg.chat.id,
                        message_id=msg.id,
                        caption=formatted_caption,
                        parse_mode=enums.ParseMode.HTML,
                    )
                else:
                    # Create basic format dictionary for direct link version
                    basic_format_dict = {
                        "file_name": "" if get_name(log_msg) is None else get_name(log_msg),
                        "caption": "" if file_caption is None else file_caption,
                        "file_size": (
                            ""
                            if humanbytes(get_media_file_size(msg)) is None
                            else humanbytes(get_media_file_size(msg))
                        ),
                        "download_link": "" if down_link is None else down_link,
                        "fast_link": "" if high_link is None else high_link,
                        "stream_link": "" if online_link is None else online_link,
                        "storage_link": "" if storage is None else storage,
                    }
                    
                    # Create safe format dictionary with all placeholders
                    safe_format_dict = create_safe_format_dict(basic_format_dict, file_name, file_caption, chat_id=msg.chat.id)
                    
                    # Generate web_link for page mode
                    from MrAKTech.tools.extract_info import generate_web_link_async
                    web_link = await generate_web_link_async(
                        chat_id=msg.chat.id,
                        filename=file_name,
                        format_dict=safe_format_dict
                    )
                    safe_format_dict['web_link'] = web_link
                    
                    # Format caption and ensure it's not empty
                    formatted_caption = channel_caption.format(**safe_format_dict)
                    if not formatted_caption or not formatted_caption.strip():
                        formatted_caption = f"📁 {file_name}\n📥 Download: {download_link}"
                    
                    await bot.edit_message_caption(
                        chat_id=msg.chat.id,
                        message_id=msg.id,
                        caption=formatted_caption,
                        parse_mode=enums.ParseMode.HTML,
                    )
        except FloodWait as w:
            print(f"Sleeping for {str(w.x)}s")
            await asyncio.sleep(w.x)
            await bot.send_message(
                chat_id=Telegram.ELOG_CHANNEL,
                text=f"GOT FLOODWAIT OF {str(w.x)}s FROM {msg.chat.title}\n\n**CHANNEL ID:** `{str(msg.chat.id)}`",
                disable_web_page_preview=True,
            )
        except Exception as e:
            await bot.send_message(
                chat_id=Telegram.ELOG_CHANNEL,
                text=f"**#ERROR_TRACKEBACK:** `{e}`"+f"\n\n**CHANNEL ID:** `{str(msg.chat.id)}`",
                disable_web_page_preview=True,
            )
            print(
                f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Give me edit permission in updates and bin Channel!{e}**"
            )
    else:
        ax = await msg.reply_text(
            text="I'm not currently connected to your channel. Please connect with your channel. Once I'm added, kindly resend the file.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Connect With Me",
                            url=f"https://t.me/{(await bot.get_me()).username}?start=channel_{msg.chat.id}",
                        )
                    ]
                ]
            ),
            quote=True,
        )
        await asyncio.sleep(60)
        await ax.delete()
