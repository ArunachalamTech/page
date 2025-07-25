# Copyright 2021 To 2024-present, Author: MrAKTech

import logging
import asyncio
import random

from shortzy import Shortzy
from pyrogram import enums, errors
from pyrogram.errors import UserNotParticipant, FloodWait, UserIsBlocked
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from MrAKTech.config import Telegram, Domain
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.txt import tamilxd

LOGGER = logging.getLogger(__name__)
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


class temp(object):
    START_TIME = 0
    ME = None
    BOT_ID = None
    U_NAME = None
    B_NAME = None
    BROADCAST_CANCEL = False


async def get_domain_link(user):
    domain_tap = user["settings"]
    if domain_tap == "TempURL":
        return Domain.TEMP_URL
    elif domain_tap == "Cloudflare":
        return random.choice(Domain.CLOUDFLARE_URLS)
    else:
        return Domain.TEMP_URL


async def get_invite_link(bot, chat_id):
    try:
        link = await bot.create_chat_invite_link(chat_id)
    except errors.FloodWait as e:
        await asyncio.sleep(e.x)
        link = await bot.create_chat_invite_link(chat_id)
    return link


async def get_shortlink(channel_id, link):
    settings = await u_db.get_chl_settings(channel_id)
    url = settings["url"]
    api = settings["api"]
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link


# -------------[ SHORT LINK FUNCTION ]------------#


async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except:
        return False


async def short_link(link, user=None):
    if not user:
        return link
    api_key = user["shortener_api"]
    base_site = user["shortener_url"]

    if bool(api_key and base_site):
        shortzy = Shortzy(api_key, base_site)
        link = await shortzy.convert(link)

    return link


async def short_link_with_custom_shortener(link, shortener_url, api_key):
    """Create shortened link using custom shortener"""
    if not shortener_url or not api_key:
        return link
    
    try:
        from shortzy import Shortzy
        shortzy = Shortzy(api_key, shortener_url)
        shortened_link = await shortzy.convert(link)
        return shortened_link
    except Exception as e:
        LOGGER.error(f"Error shortening link: {e}")
        return link


async def is_subscribed(bot, query, channel_id = Telegram.AUTH_CHANNEL):
    try:
        user = await bot.get_chat_member(channel_id, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        print(e)
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True
    return False


# -----------[ USER VERIFICATION FUNCTIONS ]-----------#


async def is_user_joined(bot, message: Message, channel_id=Telegram.AUTH_CHANNEL):
    try:
        user = await bot.get_chat_member(
            chat_id=channel_id, user_id=message.from_user.id
        )
        if user.status == "BANNED":
            await message.reply_text(
                text=tamilxd.BAN_TXT,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
            return False
    except UserNotParticipant:
        invite_link = await get_invite_link(bot, chat_id=channel_id)
        ver = await message.reply_photo(
            photo=Telegram.VERIFY_PIC,
            caption=tamilxd.FORCE_SUB_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 1 🔰", url= Telegram.AUTH_GROUP2),
                    InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 2 🔰", url= Telegram.AUTH_CHANNEL3)],
                    [InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 3 🔰", url= Telegram.AUTH_GROUP),
                    InlineKeyboardButton("🔰 𝙲𝙷𝙰𝙽𝙽𝙴𝙻 4 🔰", url=invite_link.invite_link)]]
            ),
        )
        await asyncio.sleep(30)
        try:
            await ver.delete()
            await message.delete()
        except Exception:
            pass
        return False
    except Exception:
        await message.reply_text(
            text=tamilxd.SWCMD_TXT,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return False
    return True


async def is_user_banned(message):
    if await u_db.is_user_banned(message.from_user.id):
        await message.reply_text(
            text=tamilxd.BAN_TXT,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return True
    return False


async def is_user_exist(bot, message):
    if not bool(await u_db.is_user_exist(message.from_user.id)):
        await u_db.add_user(message.from_user.id)
        await bot.send_message(
            Telegram.ULOG_CHANNEL,
            f"**#NᴇᴡUsᴇʀ**\n**⬩ ᴜsᴇʀ ɴᴀᴍᴇ :** [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n**⬩ ᴜsᴇʀ ɪᴅ :** `{message.from_user.id}`",
        )


async def verify_user(bot, message):
    if await is_user_banned(message):
        return False
    await is_user_exist(bot, message)
    if not await is_user_joined(bot, message):
        return False
    return True


# ---------------------[ BROADCAST ]---------------------#


async def broadcast_messages(user_id, message, pin):
    try:
        m = await message.copy(chat_id=user_id)
        if pin:
            await m.pin(both_sides=True)
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message, pin)
    except UserIsBlocked:
        return "Blocked"
    except Exception as e:
        await u_db.delete_user(user_id)
        LOGGER.error(e)
        await add_inactive_user(user_id)
        return "Failed"


async def add_inactive_user(user_id):
    if not await u_db.iis_user_exist(user_id):
        await u_db.iadd_user(user_id)

# ---------------------[ GET TIME ]---------------------#


def get_time(seconds):
    """Get time in readable format"""

    result = ""
    days, remainder = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days} Days "
    hours, remainder = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours} Hours "
    minutes, seconds = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes} Minutes "
    seconds = int(seconds)
    if seconds != 0:
        result += f"{seconds} Seconds "
    if result == "":
        result += "🤷‍♂️"
    return result


# ---------------------[ OTHER FUNCTIONS ]---------------------#


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"


def readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result


#
