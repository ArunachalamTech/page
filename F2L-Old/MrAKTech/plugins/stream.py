# (c) @MrAKTech

import asyncio
import random

from pyrogram import filters, Client, enums
from pyrogram.errors import FloodWait, BadMsgNotification
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from MrAKTech import StreamBot
from MrAKTech.config import Telegram, Domain, Server
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.utils_bot import short_link, verify_user
from MrAKTech.tools.human_readable import humanbytes
from MrAKTech.tools.file_properties import get_name, get_hash, get_media_file_size
from MrAKTech.tools.extract_info import smart_replace_placeholders_in_caption, create_safe_format_dict
from MrAKTech.tools.extract_info import extract_quality, extract_season_number, extract_episode_number, replace_placeholders_in_caption


async def safe_send_message(client, chat_id, text, **kwargs):
    """Send message with retry logic for BadMsgNotification errors"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await client.send_message(chat_id, text, **kwargs)
        except BadMsgNotification as e:
            if attempt == max_retries - 1:
                # Last attempt failed, log and raise
                print(f"Failed to send message after {max_retries} attempts: {e}")
                raise
            # Wait before retry
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Unexpected error sending message: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)


async def safe_reply_message(message, text, **kwargs):
    """Reply to message with retry logic for BadMsgNotification errors"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await message.reply_text(text, **kwargs)
        except BadMsgNotification as e:
            if attempt == max_retries - 1:
                # Last attempt failed, log and raise
                print(f"Failed to reply to message after {max_retries} attempts: {e}")
                raise
            # Wait before retry
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Unexpected error replying to message: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)


async def handle_linkmode_file(c: Client, m: Message, user):
    """Handle file in linkmode - store for batch processing"""
    mediax = m.document or m.video or m.audio
    
    # Get file info
    file_caption = m.caption if m.caption else ""
    file_captionx = file_caption.replace(".mkv", "")
    
    # Forward to log channel
    log_msg = await m.forward(chat_id=Telegram.FLOG_CHANNEL)
    
    # Get file name
    file_name = get_name(log_msg) or ""
    
    # Extract quality, season, episode info
    quality = extract_quality(file_name) or extract_quality(file_captionx) or ""
    season = extract_season_number(file_name) or extract_season_number(file_captionx) or ""
    episode = extract_episode_number(file_name) or extract_episode_number(file_captionx) or ""
    
    # Create file data structure
    file_data = {
        "file_name": file_name,
        "original_caption": file_captionx,
        "file_size": humanbytes(get_media_file_size(m)),
        "log_msg_id": str(log_msg.id),
        "file_hash": get_hash(log_msg),
        "quality": quality,
        "season": season,
        "episode": episode,
        "file_unique_id": mediax.file_unique_id
    }
    
    # Store file in pending files
    await u_db.add_pending_file(m.from_user.id, file_data)
    
    # Get current count
    pending_files = await u_db.get_pending_files(m.from_user.id)
    file_count = len(pending_files)
    
    # Send confirmation
    await safe_reply_message(
        m,
        f"📁 <b>File added to linkmode queue</b>\n\n"
        f"📄 <b>File:</b> {file_name}\n"
        f"📊 <b>Files in queue:</b> {file_count}\n\n"
        f"📤 Use /complete to process all files\n"
        f"📋 Use /pending to see queued files\n"
        f"❌ Use /clear to clear the queue",
        quote=True
    )
    
    # Log the file
    await safe_reply_message(
        log_msg,
        f"**[LINKMODE] RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n **Fɪʟᴇ Uɴɪǫᴜᴇ ID:** {mediax.file_unique_id}\n**Queue Position:** {file_count}",
        disable_web_page_preview=True,
        quote=True,
    )


@StreamBot.on_message(
    (filters.private) & (filters.document | filters.video | filters.audio), group=4
)
async def private_receive_handler(c: Client, m: Message):
    if not await verify_user(c, m):
        return
    
    user = await u_db.get_user(m.from_user.id)
    
    # Check if user is in linkmode
    linkmode_status = user.get("linkmode", False)
    
    if linkmode_status:
        # Handle linkmode - store file for batch processing
        await handle_linkmode_file(c, m, user)
        return
    
    # Normal mode processing
    mediax = m.document or m.video or m.audio
    if m.document or m.video or m.audio:
        if m.caption:
            file_caption = f"{m.caption}"
        else:
            file_caption = ""
    file_captionx = file_caption.replace(".mkv", "")
    log_msg = await m.forward(chat_id=Telegram.FLOG_CHANNEL)
    caption_position = user["method"]
    c_caption = user["caption"]
    
    # Extract quality, season, and episode information from both filename and original caption
    file_name = get_name(log_msg) or ""
    auto_extract = user.get("auto_extract", True)
    
    if auto_extract:
        # Use smart extraction that combines filename and original caption data
        c_caption = smart_replace_placeholders_in_caption(c_caption, file_name, file_captionx)
    
    storage = f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{log_msg.id}"
    storagex = await short_link(storage, user)
    stream_linkx = f"{random.choice(Domain.CLOUDFLARE_URLS)}watch/{str(log_msg.id)}?hash={get_hash(log_msg)}"
    stream_link = await short_link(stream_linkx, user)
    online_link = await short_link(
        f"{random.choice(Domain.CLOUDFLARE_URLS)}dl/{str(log_msg.id)}?hash={get_hash(log_msg)}",
        user,
    )
    high_link = await short_link(
        f"{random.choice(Domain.MRAKFAST_URLS)}dl/{str(log_msg.id)}?hash={get_hash(log_msg)}",
        user,
    )
    
    # Generate web_link for page mode
    page_mode = await u_db.get_page_mode(m.from_user.id)
    if page_mode:
        # Get user's page code for privacy
        page_code = await u_db.get_page_code(m.from_user.id)
        if not page_code:
            # Generate new page code if not exists
            page_code = await u_db.regenerate_page_code(m.from_user.id)
        web_link = f"{Server.URL}/sl/{str(log_msg.id)}/{page_code}"
    else:
        web_link = stream_link  # Default to stream_link if page mode is disabled
    
    try:
        # Create basic format dictionary
        basic_format_dict = {
            "file_name": "" if get_name(log_msg) is None else get_name(log_msg),
            "caption": "" if file_captionx is None else file_captionx,
            "file_size": (
                ""
                if humanbytes(get_media_file_size(m)) is None
                else humanbytes(get_media_file_size(m))
            ),
            "download_link": "" if online_link is None else online_link,
            "fast_link": "" if high_link is None else high_link,
            "stream_link": "" if stream_link is None else stream_link,
            "storage_link": "" if storagex is None else storagex,
            "web_link": "" if web_link is None else web_link,
        }
        
        # Create safe format dictionary with all placeholders
        safe_format_dict = create_safe_format_dict(basic_format_dict, file_name, file_captionx)
        
        if caption_position == "links":
            await safe_reply_message(
                m,
                c_caption.format(**safe_format_dict),
                quote=True,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ 📥", url=stream_link)]]
                ),
            )
        elif caption_position == "files":
            await c.send_cached_media(
                chat_id=m.from_user.id,
                file_id=mediax.file_id,
                caption=c_caption.format(**safe_format_dict),
                parse_mode=enums.ParseMode.HTML,
            )
        await safe_reply_message(
            log_msg,
            f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n**Uꜱᴇʀ ɪᴅ :** `{m.from_user.id}`\n **Fɪʟᴇ Uɴɪǫᴜᴇ ID:** {mediax.file_unique_id}\n**Stream ʟɪɴᴋ :** {stream_linkx}\n**High ʟɪɴᴋ :** {high_link}\n**Storage ʟɪɴᴋ :** {storage}",
            disable_web_page_preview=True,
            quote=True,
        )

    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)
        await c.send_message(
            chat_id=Telegram.ELOG_CHANNEL,
            text=f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.x)}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n**𝚄𝚜𝚎𝚛 𝙸𝙳 :** `{str(m.from_user.id)}`",
            disable_web_page_preview=True,
        )