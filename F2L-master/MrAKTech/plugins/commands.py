import asyncio
import time
import os
import requests
import re
import random

from telegraph import upload_file
import logging
from platform import python_version

from pyrogram import filters, enums, __version__
from pyrogram.errors import BadMsgNotification, FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums.parse_mode import ParseMode

from MrAKTech import StreamBot
from MrAKTech.config import Telegram
from MrAKTech.tools.txt import tamilxd, BUTTON
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.utils_bot import temp, readable_time, verify_user, is_check_admin


async def safe_reply_message(message, text, **kwargs):
    """Reply to message with retry logic for BadMsgNotification errors"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await message.reply_text(text, **kwargs)
        except BadMsgNotification as e:
            if attempt == max_retries - 1:
                print(f"Failed to reply to message after {max_retries} attempts: {e}")
                raise
            await asyncio.sleep(2 ** attempt)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Unexpected error replying to message: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)


logger = logging.getLogger(__name__)


@StreamBot.on_message(
    filters.command("stop") & filters.private & filters.user(list(Telegram.OWNER_ID))
)
async def alive(bot: StreamBot, message: Message):  # type: ignore
    print("Stopping...")
    ax = await message.reply("Stopping...")
    try:
        await StreamBot.stop()
    except:  # noqa: E722
        pass
    print("Bot Stopped")
    await ax.edit_text("Bot Stopped")


@StreamBot.on_message(filters.command("alive"))
async def alivex(bot: StreamBot, message: Message):  # type: ignore
    txt = (
        f"**{temp.B_NAME}** ```RUNNING```\n"
        f"-> Current Uptime: `{readable_time((time.time() - temp.START_TIME))}`\n"
        f"-> Python: `{python_version()}`\n"
        f"-> Pyrogram: `{__version__}`"
    )
    await message.reply_text(txt, quote=True)


@StreamBot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await verify_user(client, message):
        return
    chat_id = message.text.split("_")[-1]
    if chat_id == "/start":
        await message.reply_photo(
            photo="https://graph.org/file/8cd764fbdf3ccd34abe22.jpg",
            caption=tamilxd.START_TXT.format(
                message.from_user.first_name, message.from_user.id
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=BUTTON.START_BUTTONS,
            quote=True,
        )
    else:
        if "channel" in message.text:
            tamil = await message.reply_text(
                "Geting your channel data, Please Wait...", quote=True
            )
            chat = await client.get_chat(chat_id)
            if chat.type != enums.ChatType.CHANNEL:
                await tamil.edit_text("This is Invalid command.")
            if not await is_check_admin(client, chat_id, message.from_user.id):
                await tamil.edit_text("You are not an admin in this channel.")
            else:
                username = chat.username
                username = "@" + username if username else "private"
                chatx = await u_db.add_channel(
                    int(message.from_user.id), int(chat_id), chat.title, username
                )
                await tamil.edit_text(
                    (
                        "<b>Channel added successfully.</b>"
                        if chatx
                        else "<b>This channel already added!...</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("≺≺ Back", callback_data="channels")]]
                    ),
                )
        else:
            await message.reply_text("**Invalid Command**", quote=True)


@StreamBot.on_message(filters.private & filters.command(["about"]))
async def about(bot, update):
    await update.reply_text(
        text=tamilxd.ABOUT_TXT,
        disable_web_page_preview=True,
        reply_markup=BUTTON.ABOUT_BUTTONS,
        quote=True,
    )


@StreamBot.on_message(filters.command("help") & filters.private)
async def help_handler(bot, message):
    await message.reply_text(
        text=tamilxd.HELP_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=BUTTON.HELP_BUTTONS,
        quote=True,
    )


# thiss is for shortner
@StreamBot.on_message(filters.command(["shortner", "shortener"]) & filters.private)
async def shortner(bot, message):
    if not await verify_user(bot, message):
        return
    user_id = message.from_user.id
    userxdb = await u_db.get_user_details(user_id)
    buttons = []
    if userxdb["shortener_url"] and userxdb["shortener_api"] is not None:
        buttons.append(
            [InlineKeyboardButton("Show shortner", callback_data="show_shortner")]
        )
        buttons.append(
            [
                InlineKeyboardButton(
                    "Default shortner", callback_data="delete_shortner"
                ),
                InlineKeyboardButton("Change shortner", callback_data="add_shortner"),
            ]
        )
    else:
        buttons.append(
            [InlineKeyboardButton("Set shortner", callback_data="add_shortner")]
        )
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])
    await message.reply_text(
        text=tamilxd.CUSTOM_SHORTNER_TXT,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# this is for caption
@StreamBot.on_message(filters.command("caption"))
async def caption(bot, message):
    if not await verify_user(bot, message):
        return
    user_id = message.from_user.id
    caption = await u_db.get_caption(user_id)
    buttons = []
    if caption is not None:
        buttons.append(
            [InlineKeyboardButton("Show caption", callback_data="show_caption")]
        )
        buttons.append(
            [
                InlineKeyboardButton("Default caption", callback_data="delete_caption"),
                InlineKeyboardButton("Change caption", callback_data="add_caption"),
            ]
        )
    else:
        buttons.append(
            [InlineKeyboardButton("Set caption", callback_data="add_caption")]
        )
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])
    await message.reply_text(
        text=tamilxd.CUSTOM_CAPTION_TXT,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@StreamBot.on_message(filters.command("settings"))
async def settings(client, message):
    await message.reply_text(
        "<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ᴀꜱ ʏᴏʜʀ ᴡɪꜱʜ </b>",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Personal settings", callback_data="settings"),
                ],
                [InlineKeyboardButton("Channels settings", callback_data="channels")],
                [InlineKeyboardButton("≺≺ Close", callback_data="close")],
            ]
        ),
    )


# this is for user settings
@StreamBot.on_message(filters.command(["usetting", "us", "usettings"]))
async def settings(client, message):  # noqa: F811
    userxdb = await u_db.get_user_details(message.from_user.id)
    button = [
        [
            InlineKeyboardButton(
                (
                    "✅ Custom caption"
                    if userxdb["caption"] is not None
                    else "📝 Custom caption"
                ),
                callback_data="custom_caption",
            )
        ],
        [
            InlineKeyboardButton(
                (
                    "✅ Custom shortner"
                    if userxdb["shortener_url"] and userxdb["shortener_api"] is not None
                    else "🖼️ Custom shortner"
                ),
                callback_data="custom_shortner",
            )
        ],
        [
            InlineKeyboardButton("📤 Upload mode", callback_data="toggle_mode"),
            InlineKeyboardButton(
                userxdb["method"] if userxdb["method"] else "Links",
                callback_data="toggle_mode",
            ),
        ],
        [InlineKeyboardButton("Close ✗", callback_data="close")],
    ]
    await message.reply_text(
        text=tamilxd.SETTINGS_TXT.format(
            CAPTION="✅ Exists" if userxdb["caption"] is not None else "❌ Not Exists",
            URLX=(
                userxdb["shortener_url"]
                if userxdb["shortener_url"] is not None
                else "❌ Not Exists"
            ),
            APIX=(
                userxdb["shortener_api"]
                if userxdb["shortener_api"] is not None
                else "❌ Not Exists"
            ),
            STORAGEX=userxdb["storage"],
            METHODX=userxdb["method"],
            AUTO_EXTRACT="✅ Enabled" if userxdb.get("auto_extract", True) else "❌ Disabled",
            LINKMODE="✅ Enabled" if userxdb.get("linkmode", False) else "❌ Disabled",
        ),
        reply_markup=InlineKeyboardMarkup(button),
        disable_web_page_preview=True,
        quote=True,
    )


# this is for channels settings
@StreamBot.on_message(filters.command(["channels", "csetting", "cs", "csettings"]))
async def settings(bot, msg):  # noqa: F811
    buttons = []
    channels = await u_db.get_user_channels(msg.from_user.id)
    for channel in channels:
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{channel['title']}",
                    callback_data=f"editchannels_{channel['chat_id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton("✚ Add Channel ✚", callback_data="addchannel")]
    )
    buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="main")])
    await msg.reply_text(
        "<b><u>My Channels</b></u>\n\n<b>you can manage your target chats in here</b>",
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
    )


# this is for features
@StreamBot.on_message(filters.command("features") & filters.private)
async def about_handler(bot, message):
    hs = await message.reply_photo(
        photo="https://graph.org/file/68a0935f0d19ffd647a09.jpg",
        caption=(tamilxd.COMMENTS_TXT.format(message.from_user.mention)),
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("↻ ᴄʟᴏsᴇ ↻", callback_data="close")]]
        ),
    )
    await asyncio.sleep(150)
    await hs.delete()
    await message.delete()


# this is for id get
@StreamBot.on_message(filters.command("id"))
async def get_id(bot: StreamBot, message: Message):  # type: ignore
    file_id = None
    user_id = None

    if message.reply_to_message:
        rep = message.reply_to_message

        if rep.audio:
            file_id = f"**File ID**: `{rep.audio.file_id}`"
            file_id += "**File Type**: `audio`"

        elif rep.document:
            file_id = f"**File ID**: `{rep.document.file_id}`"
            file_id += f"**File Type**: `{rep.document.mime_type}`"

        elif rep.photo:
            file_id = f"**File ID**: `{rep.photo.file_id}`"
            file_id += "**File Type**: `photo`"

        elif rep.sticker:
            file_id = f"**Sicker ID**: `{rep.sticker.file_id}`\n"
            if rep.sticker.set_name and rep.sticker.emoji:
                file_id += f"**Sticker Set**: `{rep.sticker.set_name}`\n"
                file_id += f"**Sticker Emoji**: `{rep.sticker.emoji}`\n"
                if rep.sticker.is_animated:
                    file_id += f"**Animated Sticker**: `{rep.sticker.is_animated}`\n"
                else:
                    file_id += "**Animated Sticker**: `False`\n"
            else:
                file_id += "**Sticker Set**: __None__\n"
                file_id += "**Sticker Emoji**: __None__"

        elif rep.video:
            file_id = f"**File ID**: `{rep.video.file_id}`\n"
            file_id += "**File Type**: `video`"

        elif rep.animation:
            file_id = f"**File ID**: `{rep.animation.file_id}`\n"
            file_id += "**File Type**: `GIF`"

        elif rep.voice:
            file_id = f"**File ID**: `{rep.voice.file_id}`\n"
            file_id += "**File Type**: `Voice Note`"

        elif rep.video_note:
            file_id = f"**File ID**: `{rep.animation.file_id}`\n"
            file_id += "**File Type**: `Video Note`"

        elif rep.location:
            file_id = "**Location**:\n"
            file_id += f"**longitude**: `{rep.location.longitude}`\n"
            file_id += f"**latitude**: `{rep.location.latitude}`"

        elif rep.venue:
            file_id = "**Location**:\n"
            file_id += f"**longitude**: `{rep.venue.location.longitude}`\n"
            file_id += f"**latitude**: `{rep.venue.location.latitude}`\n\n"
            file_id += "**Address**:\n"
            file_id += f"**title**: `{rep.venue.title}`\n"
            file_id += f"**detailed**: `{rep.venue.address}`\n\n"

        elif rep.from_user:
            user_id = rep.from_user.id

    if user_id:
        if rep.forward_from:
            user_detail = (
                f"**Forwarded User ID**: `{message.reply_to_message.forward_from.id}`\n"
            )
        else:
            user_detail = f"**User ID**: `{message.reply_to_message.from_user.id}`\n"
        user_detail += f"**Message ID**: `{message.reply_to_message.id}`"
        await message.reply(user_detail)
    elif file_id:
        if rep.forward_from:
            user_detail = (
                f"**Forwarded User ID**: `{message.reply_to_message.forward_from.id}`\n"
            )
        else:
            user_detail = f"**User ID**: `{message.reply_to_message.from_user.id}`\n"
        user_detail += f"**Message ID**: `{message.reply_to_message.id}`\n\n"
        user_detail += file_id
        await message.reply(user_detail, quote=True)

    else:
        await message.reply(f"**Chat ID**: `{message.chat.id}`", quote=True)


# this is for telegraph
@StreamBot.on_message(filters.command("telegraph"))
async def telegraph_upload(bot, message):
    if not (reply_to_message := message.reply_to_message):
        return await message.reply("Reply to any photo or video.")
    file = reply_to_message.photo or reply_to_message.video or None
    if file is None:
        return await message.reply("Invalid media.")
    if file.file_size >= 5242880:
        await message.reply_text(text="Send less than 5MB")
        return
    text = await message.reply_text(text="Processing....", quote=True)
    media = await reply_to_message.download()
    try:
        response = upload_file(media)
    except Exception as e:
        await text.edit_text(text=f"Error - {e}")
        return
    try:
        os.remove(media)
    except:  # noqa: E722
        pass
    await text.edit_text(
        f"<b>❤️ Your Telegram Link Complete 👇</b>\n\n<code>https://telegra.ph/{response[0]}</code></b>"
    )


# this is for GPT codes
@StreamBot.on_message(filters.command(["askgpt", "gpt"]))
async def gpt(app, message: Message):
    text = "".join(message.text.split(" ")[1:])
    if len(text) == 0:
        return await message.reply_text(
            "Cannot reply to empty message.", parse_mode=ParseMode.MARKDOWN
        )
    m = await message.reply_text("Getting Request....", parse_mode=ParseMode.MARKDOWN)
    url = "https://api.safone.dev/chatgpt"
    payloads = {
        "message": text,
        # "version": 3,
        "chat_mode": "assistant",
        "dialog_messages": '[{"bot":"","user":""}]',
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payloads, headers=headers)
        results = response.json()
        res = results["message"]

        await m.edit_text(f"{res}")
    except Exception as e:
        await m.edit_text(f"Error :-\n{e}")


# this is for  donate
@StreamBot.on_message(filters.command(["donate"]))
async def donate(app, message: Message):
    await message.reply_text(
        text=tamilxd.DONATE_TXT,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=BUTTON.DONATE_BUTTONS,
        quote=True,
    )


# Auto extraction commands
@StreamBot.on_message(filters.command(["extract", "autoextract"]))
async def extract_toggle(bot, message):
    if not await verify_user(bot, message):
        return
    user_id = message.from_user.id
    auto_extract = await u_db.get_auto_extract(user_id)

    buttons = []
    buttons.append([
        InlineKeyboardButton(
            "✅ Enable Auto Extract" if not auto_extract else "❌ Disable Auto Extract",
            callback_data="toggle_extract"
        )
    ])
    buttons.append([InlineKeyboardButton("Close", callback_data="close")])

    status = "Enabled" if auto_extract else "Disabled"
    await message.reply_text(
        f"<b><u>🔍 AUTO EXTRACTION SETTINGS</u></b>\n\n"
        f"<b>Current Status:</b> {status}\n\n"
        f"<b>📝 What it does:</b>\n"
        f"• Automatically extracts quality (1080p, 720p, 4K, etc.)\n"
        f"• Finds season numbers (S01, S02, etc.)\n"
        f"• Detects episode numbers (E01, E02, etc.)\n"
        f"• Replaces placeholders in your custom caption\n\n"
        f"<b>🎯 Supported placeholders:</b>\n"
        f"<code>{{quality}}</code> - Video quality\n"
        f"<code>{{season}}</code> - Season number\n"
        f"<code>{{episode}}</code> - Episode number",
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# Example caption command
@StreamBot.on_message(filters.command(["examples", "example"]))
async def show_examples(bot, message):
    if not await verify_user(bot, message):
        return
    
    example_text = """<b><u>📝 CAPTION EXAMPLES WITH AUTO EXTRACTION</u></b>

<b>🎬 Example 1:</b>
<code>🎥 {file_name}

📺 Quality: {quality}
🎞️ Season: {season} | Episode: {episode}
📦 Size: {file_size}

📥 Download: {download_link}
🖥️ Stream: {stream_link}</code>

<b>🎬 Example 2:</b>
<code>📁 File: {file_name}
🔍 [{quality}] S{season}E{episode}
📊 Size: {file_size}

⬇️ {download_link}</code>

<b>🎬 Example 3:</b>
<code>🎦 **{file_name}**

🌟 Quality: **{quality}**
📺 Season {season} - Episode {episode}
💾 {file_size}

📱 Watch Online: {stream_link}
💿 Download: {download_link}</code>

<b>💡 Note:</b> These placeholders will be automatically replaced with extracted information from your file names!"""
    
    await message.reply_text(
        example_text,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔍 Configure Auto Extract", callback_data="toggle_extract"),
            InlineKeyboardButton("Close", callback_data="close")
        ]])
    )


# Test extraction command
@StreamBot.on_message(filters.command(["test", "testextract"]))
async def test_extraction(bot, message):
    if not await verify_user(bot, message):
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "<b>📋 Test Extraction</b>\n\n"
            "<b>Usage:</b> <code>/test filename</code>\n\n"
            "<b>Example:</b> <code>/test Game.of.Thrones.S08E06.1080p.WEB-DL.x264.mkv</code>\n\n"
            "This will show you what quality, season, and episode information can be extracted from the filename.",
            quote=True
        )
        return
    
    # Get filename from command
    filename = " ".join(message.command[1:])
    
    # Import extraction functions
    from MrAKTech.tools.extract_info import extract_quality, extract_season_number, extract_episode_number, extract_combined_info
    
    # Test individual extractions
    quality = extract_quality(filename)
    season = extract_season_number(filename)
    episode = extract_episode_number(filename)
    
    # Test combined extraction (filename only in this case)
    combined_info = extract_combined_info(filename)
    
    result_text = f"""<b><u>🔍 EXTRACTION TEST RESULT</u></b>

<b>📁 Filename:</b> <code>{filename}</code>

<b>📊 Extracted Information:</b>
🎞️ <b>Quality:</b> <code>{quality or 'Not detected'}</code>
📺 <b>Season:</b> <code>{season or 'Not detected'}</code>
🎬 <b>Episode:</b> <code>{episode or 'Not detected'}</code>

<b>🧠 Smart Extraction (Best Result):</b>
🎞️ <b>Final Quality:</b> <code>{combined_info['quality'] or 'Not detected'}</code>
📺 <b>Final Season:</b> <code>{combined_info['season'] or 'Not detected'}</code>
🎬 <b>Final Episode:</b> <code>{combined_info['episode'] or 'Not detected'}</code>

<b>💡 The bot now checks both filename AND original caption to get the most complete information!</b>"""
    
    await message.reply_text(
        result_text,
        disable_web_page_preview=True,
        quote=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📝 See Examples", callback_data="show_examples"),
            InlineKeyboardButton("Close", callback_data="close")
        ]])
    )


# Linkmode commands
@StreamBot.on_message(filters.command("linkmode") & filters.private)
async def linkmode_toggle(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 2:
        # Show current status
        linkmode_status = await u_db.get_linkmode(user_id)
        await message.reply_text(
            f"<b>🔗 LINKMODE STATUS</b>\n\n"
            f"<b>Current Status:</b> {'✅ ON' if linkmode_status else '❌ OFF'}\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/linkmode on</code> - Enable linkmode\n"
            f"<code>/linkmode off</code> - Disable linkmode\n\n"
            f"<b>📋 What is Linkmode?</b>\n"
            f"• Collect multiple files before generating links\n"
            f"• Use custom captions with advanced placeholders\n"
            f"• Default caption provided if no custom caption is set\n"
            f"• Support for multiple shortener services\n"
            f"• Batch processing with /complete command",
            quote=True
        )
        return
    
    if args[1].lower() == "on":
        await u_db.set_linkmode(user_id, True)
        await message.reply_text(
            "✅ <b>LINKMODE ENABLED</b>\n\n"
            "🔗 You are now in linkmode!\n"
            "📁 Send your files and use /complete when done\n"
            "💡 Default caption will be used if no custom caption is set\n"
            "⚙️ Use /setlinkmodecaption to set custom captions\n"
            "🔗 Use /shortlink1, /shortlink2, /shortlink3 to set shorteners",
            quote=True
        )
    elif args[1].lower() == "off":
        await u_db.set_linkmode(user_id, False)
        await u_db.clear_pending_files(user_id)
        await message.reply_text(
            "❌ <b>LINKMODE DISABLED</b>\n\n"
            "🔄 Switched back to normal mode\n"
            "🗑️ Cleared any pending files",
            quote=True
        )
    else:
        await message.reply_text(
            "❌ <b>Invalid option</b>\n\n"
            "Use: <code>/linkmode on</code> or <code>/linkmode off</code>",
            quote=True
        )


@StreamBot.on_message(filters.command("complete") & filters.private)
async def complete_linkmode(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    linkmode_status = await u_db.get_linkmode(user_id)
    
    if not linkmode_status:
        await message.reply_text(
            "❌ <b>Linkmode is not enabled</b>\n\n"
            "Use <code>/linkmode on</code> to enable linkmode first",
            quote=True
        )
        return
    
    pending_files = await u_db.get_pending_files(user_id)
    
    if not pending_files:
        await message.reply_text(
            "📭 <b>No pending files</b>\n\n"
            "Send some files first, then use /complete",
            quote=True
        )
        return
    
    processing_msg = await message.reply_text(
        f"⏳ <b>Processing {len(pending_files)} files...</b>\n\n"
        "Please wait while I generate your links",
        quote=True
    )
    
    # Process files and generate links
    await process_linkmode_files(bot, message, pending_files, processing_msg)


@StreamBot.on_message(filters.command(["shortlink1", "shortlink2", "shortlink3"]) & filters.private)
async def set_shortlink(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    args = message.text.split()
    command = args[0].lower()
    shortlink_num = command[-1]  # Extract number from command
    
    if len(args) < 2:
        # Show current shortlink
        shortlink_data = await u_db.get_shortlink(user_id, shortlink_num)
        status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
        
        await message.reply_text(
            f"<b>🔗 SHORTLINK {shortlink_num.upper()} STATUS</b>\n\n"
            f"<b>Status:</b> {status}\n"
            f"<b>URL:</b> <code>{shortlink_data['url'] or 'Not set'}</code>\n"
            f"<b>API:</b> <code>{shortlink_data['api'] or 'Not set'}</code>\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/shortlink{shortlink_num} {{url}} {{api}}</code>\n"
            f"<code>/shortlink{shortlink_num} off</code> - Disable\n\n"
            f"<b>Example:</b>\n"
            f"<code>/shortlink{shortlink_num} short.com your_api_key</code>",
            quote=True
        )
        return
    
    if args[1].lower() == "off":
        await u_db.delete_shortlink(user_id, shortlink_num)
        await message.reply_text(
            f"❌ <b>SHORTLINK {shortlink_num.upper()} DISABLED</b>\n\n"
            f"🔗 Shortlink {shortlink_num} has been turned off",
            quote=True
        )
        return
    
    if len(args) < 3:
        await message.reply_text(
            f"❌ <b>Invalid format</b>\n\n"
            f"<b>Usage:</b>\n"
            f"<code>/shortlink{shortlink_num} {{url}} {{api}}</code>\n\n"
            f"<b>Example:</b>\n"
            f"<code>/shortlink{shortlink_num} short.com your_api_key</code>",
            quote=True
        )
        return
    
    url = args[1]
    api = args[2]
    
    await u_db.set_shortlink(user_id, shortlink_num, url, api)
    await message.reply_text(
        f"✅ <b>SHORTLINK {shortlink_num.upper()} SET</b>\n\n"
        f"🔗 <b>URL:</b> <code>{url}</code>\n"
        f"🔑 <b>API:</b> <code>{api}</code>\n\n"
        f"This shortener will be used for stream_link_{shortlink_num}, download_link_{shortlink_num}, and storage_link_{shortlink_num}",
        quote=True
    )


@StreamBot.on_message(filters.command("list_shortlinks") & filters.private)
async def list_shortlinks(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    shortlinks = await u_db.get_all_shortlinks(user_id)
    
    text = "<b>🔗 YOUR SHORTLINKS</b>\n\n"
    
    for i in range(1, 4):
        shortlink_data = shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
        status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
        text += f"<b>Shortlink {i}:</b> {status}\n"
        if shortlink_data["url"]:
            text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
            text += f"   • API: <code>{shortlink_data['api']}</code>\n"
        text += "\n"
    
    text += "<b>📝 Commands:</b>\n"
    text += "• <code>/shortlink1 {url} {api}</code>\n"
    text += "• <code>/shortlink2 {url} {api}</code>\n"
    text += "• <code>/shortlink3 {url} {api}</code>\n"
    text += "• <code>/shortlink1 off</code> (to disable)\n"
    
    await message.reply_text(text, quote=True)


@StreamBot.on_message(filters.command(["delete_shortlink1", "delete_shortlink2", "delete_shortlink3"]) & filters.private)
async def delete_shortlink_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    command = message.text.split()[0].lower()
    shortlink_num = command[-1]  # Extract number from command
    
    await u_db.delete_shortlink(user_id, shortlink_num)
    await message.reply_text(
        f"🗑️ <b>SHORTLINK {shortlink_num.upper()} DELETED</b>\n\n"
        f"✅ Shortlink {shortlink_num} has been removed",
        quote=True
    )


@StreamBot.on_message(filters.command("setlinkmodecaption") & filters.private)
async def set_linkmode_caption_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    # Get current captions
    caption1 = await u_db.get_linkmode_caption(user_id, 1)
    caption2 = await u_db.get_linkmode_caption(user_id, 2)
    caption3 = await u_db.get_linkmode_caption(user_id, 3)
    active_caption = await u_db.get_active_linkmode_caption(user_id)
    
    buttons = []
    
    # Add caption buttons
    buttons.append([
        InlineKeyboardButton(
            f"📝 Caption 1 {'✅' if caption1 else '❌'}",
            callback_data="linkmode_caption_1"
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            f"📝 Caption 2 {'✅' if caption2 else '❌'}",
            callback_data="linkmode_caption_2"
        )
    ])
    buttons.append([
        InlineKeyboardButton(
            f"📝 Caption 3 {'✅' if caption3 else '❌'}",
            callback_data="linkmode_caption_3"
        )
    ])
    
    # Add active caption selection
    if caption1 or caption2 or caption3:
        buttons.append([
            InlineKeyboardButton(
                f"🎯 Active: Caption {active_caption or 'None'}",
                callback_data="select_active_caption"
            )
        ])
    
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    
    text = "<b>🎨 LINKMODE CAPTION SETTINGS</b>\n\n"
    text += f"<b>Caption 1:</b> {'✅ Set' if caption1 else '❌ Not set'}\n"
    text += f"<b>Caption 2:</b> {'✅ Set' if caption2 else '❌ Not set'}\n"
    text += f"<b>Caption 3:</b> {'✅ Set' if caption3 else '❌ Not set'}\n\n"
    text += f"<b>Active Caption:</b> {active_caption or 'None selected'}\n\n"
    text += "<b>📋 Available Placeholders:</b>\n"
    text += "• <code>{filenamefirst}</code> - First file name\n"
    text += "• <code>{filenamelast}</code> - Last file name\n"
    text += "• <code>{filecaptionfirst}</code> - First file caption\n"
    text += "• <code>{filecaptionlast}</code> - Last file caption\n"
    text += "• <code>{stream_link_1}</code>, <code>{stream_link_2}</code>, <code>{stream_link_3}</code>\n"
    text += "• <code>{download_link_1}</code>, <code>{download_link_2}</code>, <code>{download_link_3}</code>\n"
    text += "• <code>{storage_link_1}</code>, <code>{storage_link_2}</code>, <code>{storage_link_3}</code>\n"
    text += "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>"
    
    await message.reply_text(
        text,
        quote=True,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@StreamBot.on_message(filters.command("pending") & filters.private)
async def show_pending_files(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    pending_files = await u_db.get_pending_files(user_id)
    
    if not pending_files:
        await message.reply_text(
            "📭 <b>No pending files</b>\n\n"
            "Send some files in linkmode to see them here",
            quote=True
        )
        return
    
    text = f"📁 <b>PENDING FILES ({len(pending_files)})</b>\n\n"
    
    for i, file_data in enumerate(pending_files, 1):
        text += f"<b>{i}.</b> {file_data.get('file_name', 'Unknown')}\n"
        text += f"   📊 Size: {file_data.get('file_size', 'Unknown')}\n"
        if file_data.get('quality'):
            text += f"   🎞️ Quality: {file_data.get('quality')}\n"
        text += "\n"
    
    text += "<b>📋 Commands:</b>\n"
    text += "• <code>/complete</code> - Process all files\n"
    text += "• <code>/clear</code> - Clear the queue\n"
    text += "• <code>/linkmode off</code> - Exit linkmode"
    
    await message.reply_text(text, quote=True)


@StreamBot.on_message(filters.command("clear") & filters.private)
async def clear_pending_files(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    pending_files = await u_db.get_pending_files(user_id)
    
    if not pending_files:
        await message.reply_text(
            "📭 <b>No files to clear</b>\n\n"
            "Your queue is already empty",
            quote=True
        )
        return
    
    await u_db.clear_pending_files(user_id)
    await message.reply_text(
        f"🗑️ <b>QUEUE CLEARED</b>\n\n"
        f"✅ Removed {len(pending_files)} files from queue",
        quote=True
    )


async def process_linkmode_files(bot, message, pending_files, processing_msg):
    """Process files in linkmode and generate consolidated caption with all files"""
    user_id = message.from_user.id
    
    # Get active linkmode caption
    active_caption_num = await u_db.get_active_linkmode_caption(user_id)
    active_caption = None
    
    if active_caption_num:
        # Get the active caption
        active_caption = await u_db.get_linkmode_caption(user_id, active_caption_num)
    
    # If no active caption is set or the caption is empty, use default
    if not active_caption:
        active_caption = Telegram.DEFAULT_LINK_MODE_CAPTION
        await processing_msg.edit_text("💡 <b>Using default linkmode caption</b>\n\nProcessing files...")
    else:
        await processing_msg.edit_text("⚙️ <b>Processing files with custom caption</b>...")
    
    # Get shortlinks
    shortlinks = await u_db.get_all_shortlinks(user_id)
    
    # Process files with async concurrency for better performance
    tasks = []
    for i, file_data in enumerate(pending_files):
        task = create_linkmode_format_dict(user_id, file_data, pending_files, i, shortlinks)
        tasks.append(task)
    
    # Process all files concurrently
    try:
        all_files_data = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions
        all_files_data = [data for data in all_files_data if not isinstance(data, Exception)]
    except Exception as e:
        await processing_msg.edit_text("❌ <b>Failed to process files</b>")
        return
    
    if not all_files_data:
        await processing_msg.edit_text("❌ <b>Failed to process any files</b>")
        return
    
    # Create consolidated caption
    consolidated_caption = await create_consolidated_caption(active_caption, all_files_data, shortlinks)
    
    # Send the consolidated result
    await processing_msg.edit_text("✅ <b>Processing complete!</b>")
    await send_long_message(message, consolidated_caption, quote=True, disable_web_page_preview=True)
    
    # Clear pending files
    await u_db.clear_pending_files(user_id)


async def create_consolidated_caption(template, all_files_data, shortlinks):
    """Create one consolidated caption with all files grouped under each shortener section"""
    if not all_files_data:
        return "❌ No files to process"
    
    # Multi-level sorting: Season → Episode → File Size (low to high)
    def parse_file_size(size_str):
        """Convert file size string to bytes for sorting"""
        if not size_str:
            return 0
        
        size_str = size_str.upper().strip()
        
        # Extract number and unit
        # More flexible pattern to handle various formats like "1.78 GiB", "557.33 MiB", "2GB", "500MB", etc.
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?I?B?)', size_str)
        if not match:
            # Try to extract just numbers if no unit found
            number_match = re.match(r'(\d+(?:\.\d+)?)', size_str)
            if number_match:
                return int(float(number_match.group(1)) * 1024**2)  # Assume MB
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        # Convert to bytes
        multipliers = {
            'B': 1,
            'KB': 1024,
            'KIB': 1024,
            'MB': 1024**2,
            'MIB': 1024**2,
            'GB': 1024**3,
            'GIB': 1024**3,
            'TB': 1024**4,
            'TIB': 1024**4,
            '': 1024**2  # Default to MB if no unit
        }
        
        multiplier = multipliers.get(unit, 1024**2)  # Default to MB
        bytes_result = int(number * multiplier)
        
        return bytes_result
    
    def parse_season(season_str):
        """Extract season number for sorting"""
        if not season_str:
            return 0
        
        # Extract number from season string (S01, S1, Season 1, etc.)
        season_str = str(season_str).upper().strip()
        match = re.search(r'(\d+)', season_str)
        if match:
            season_num = int(match.group(1))
            return season_num
        return 0
    
    def parse_episode(episode_str):
        """Extract episode number for sorting"""
        if not episode_str:
            return 0
        
        # Extract number from episode string (E01, E1, EP01, Episode 1, etc.)
        episode_str = str(episode_str).upper().strip()
        match = re.search(r'(\d+)', episode_str)
        if match:
            episode_num = int(match.group(1))
            return episode_num
        return 0
    
    def get_sort_key(file_data):
        """Generate sort key with priority: Season → Episode → File Size"""
        season_num = parse_season(file_data.get('season', ''))
        episode_num = parse_episode(file_data.get('episode', ''))
        size_bytes = parse_file_size(file_data.get('file_size', ''))
        
        # Return tuple for multi-level sorting
        sort_key = (season_num, episode_num, size_bytes)
        return sort_key
    
    # Sort files by Season → Episode → File Size (all low to high)
    all_files_data_sorted = sorted(all_files_data, key=get_sort_key)
    
    # Use sorted files for processing
    all_files_data = all_files_data_sorted
    
    # Replace global placeholders first (those that apply to all files)
    first_file = all_files_data[0]
    last_file = all_files_data[-1]
    
    result = template
    
    # Replace global placeholders
    global_replacements = {
        '{filenamefirst}': first_file.get('filenamefirst', ''),
        '{filenamelast}': last_file.get('filenamelast', ''),
        '{filecaptionfirst}': first_file.get('filecaptionfirst', ''),
        '{filecaptionlast}': last_file.get('filecaptionlast', ''),
    }
    
    for placeholder, value in global_replacements.items():
        if placeholder in result:
            result = result.replace(placeholder, str(value) if value else '')
    
    # Parse the template to create consolidated output
    # We need to identify sections for each shortener and list all files under each section
    
    lines = result.split('\n')
    processed_lines = []
    
    # File-specific placeholders that should be expanded to list all files
    file_placeholders = [
        '{file_name}', '{filename}', '{file_size}', '{quality}', '{season}', '{episode}',
        '{stream_link}', '{download_link}', '{storage_link}',
        '{stream_link_1}', '{stream_link_2}', '{stream_link_3}',
        '{download_link_1}', '{download_link_2}', '{download_link_3}',
        '{storage_link_1}', '{storage_link_2}', '{storage_link_3}'
    ]
    
    # Shortener-specific placeholders
    shortener_placeholders = [
        '{stream_link_1}', '{download_link_1}', '{storage_link_1}',
        '{stream_link_2}', '{download_link_2}', '{storage_link_2}',
        '{stream_link_3}', '{download_link_3}', '{storage_link_3}'
    ]
    
    # Track static lines to avoid duplication
    static_lines_added = set()
    
    for line in lines:
        # Check if this line contains shortener-specific placeholders
        contains_shortener_placeholders = any(placeholder in line for placeholder in shortener_placeholders)
        
        # Check if this line contains other file-specific placeholders
        contains_other_file_placeholders = any(placeholder in line for placeholder in file_placeholders if placeholder not in shortener_placeholders)
        
        if contains_shortener_placeholders:
            # This line should be expanded to list all files for this shortener
            for i, file_data in enumerate(all_files_data):
                # Create a copy of the line and replace placeholders for this file
                file_line = line
                
                # Replace all placeholders for this file
                file_replacements = {
                    '{file_name}': file_data.get('file_name', ''),
                    '{filename}': file_data.get('filename', ''),
                    '{file_size}': file_data.get('file_size', ''),
                    '{quality}': file_data.get('quality', ''),
                    '{season}': file_data.get('season', ''),
                    '{episode}': file_data.get('episode', ''),
                    '{stream_link}': file_data.get('stream_link', ''),
                    '{download_link}': file_data.get('download_link', ''),
                    '{storage_link}': file_data.get('storage_link', ''),
                    '{stream_link_1}': file_data.get('stream_link_1', ''),
                    '{stream_link_2}': file_data.get('stream_link_2', ''),
                    '{stream_link_3}': file_data.get('stream_link_3', ''),
                    '{download_link_1}': file_data.get('download_link_1', ''),
                    '{download_link_2}': file_data.get('download_link_2', ''),
                    '{download_link_3}': file_data.get('download_link_3', ''),
                    '{storage_link_1}': file_data.get('storage_link_1', ''),
                    '{storage_link_2}': file_data.get('storage_link_2', ''),
                    '{storage_link_3}': file_data.get('storage_link_3', ''),
                }
                
                # Apply replacements for this file
                for placeholder, value in file_replacements.items():
                    if placeholder in file_line:
                        file_line = file_line.replace(placeholder, str(value) if value else '')
                
                processed_lines.append(file_line)
                
                # Add blank line after each file link (except for the last file)
                if i < len(all_files_data) - 1:
                    processed_lines.append("")
        
        elif contains_other_file_placeholders:
            # This line contains file placeholders but not shortener links, replicate for each file
            for i, file_data in enumerate(all_files_data):
                # Create a copy of the line and replace placeholders for this file
                file_line = line
                
                # Replace all placeholders for this file
                file_replacements = {
                    '{file_name}': file_data.get('file_name', ''),
                    '{filename}': file_data.get('filename', ''),
                    '{file_size}': file_data.get('file_size', ''),
                    '{quality}': file_data.get('quality', ''),
                    '{season}': file_data.get('season', ''),
                    '{episode}': file_data.get('episode', ''),
                    '{stream_link}': file_data.get('stream_link', ''),
                    '{download_link}': file_data.get('download_link', ''),
                    '{storage_link}': file_data.get('storage_link', ''),
                }
                
                # Apply replacements for this file
                for placeholder, value in file_replacements.items():
                    if placeholder in file_line:
                        file_line = file_line.replace(placeholder, str(value) if value else '')
                
                processed_lines.append(file_line)
                
                # Add blank line after each file link (except for the last file)
                if i < len(all_files_data) - 1:
                    processed_lines.append("")
        
        else:
            # This line doesn't contain file placeholders, keep as is (but avoid duplicates)
            line_key = line.strip()
            if line_key and line_key not in static_lines_added:
                static_lines_added.add(line_key)
                processed_lines.append(line)
            elif not line_key:  # Empty line
                processed_lines.append(line)
    
    # Join all processed lines
    result = '\n'.join(processed_lines)
    
    # Format links in the final result before returning
    from MrAKTech.tools.link_formatter import format_links_in_text
    result = format_links_in_text(result, "HTML")
    
    # Safety check - if result is extremely long, use fallback
    max_total_length = 15000  # Maximum total length before fallback (practical limit for splitting)
    if len(result) > max_total_length:
        print(f"Warning: Consolidated caption too long ({len(result)} chars), using fallback")
        return create_fallback_consolidated_caption(template, all_files_data)
    
    return result


def create_fallback_consolidated_caption(template, all_files_data):
    """Create a fallback consolidated caption when template parsing fails"""
    from MrAKTech.tools.link_formatter import format_links_in_text
    
    if not all_files_data:
        return "❌ No files to process"
    
    first_file = all_files_data[0]
    
    # Basic header
    header = first_file.get("filenamefirst", "Files")
    result = f"{header}\n\n❤️‍🔥 Uploaded By - [@MrAK_LinkZzz]\n\n"
    
    # Add files using regular stream links
    result += "⬆️ ᴅɪʀᴇᴄᴛ ғɪʟᴇs / ᴏɴʟɪɴᴇ ᴡᴀᴛᴄʜɪɴɢ / ꜰᴀꜱᴛ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ ʟɪɴᴋ ⚡️\n\n"
    
    for file_data in all_files_data:
        link = file_data.get("stream_link", "")
        if link:
            size = file_data.get("file_size", "")
            quality = file_data.get("quality", "")
            # Quality already includes brackets, so just add a space if it exists
            quality_text = f" {quality}" if quality else ""
            result += f"🗂️ {size}{quality_text} :- {link}\n"
    
    result += "\n📱 sʜᴀʀᴇ ᴡɪᴛʜ ғʀɪᴇɴᴅs 📌"
    
    # Format links in the final result before returning
    result = format_links_in_text(result, "HTML")
    
    return result


async def create_linkmode_format_dict(user_id, current_file_data, all_files, current_index, shortlinks):
    """Create format dictionary for linkmode with all placeholders"""
    from MrAKTech.tools.utils_bot import short_link_with_custom_shortener
    from MrAKTech.config import Domain, Telegram
    
    # Basic file info
    file_data = current_file_data
    file_name = file_data.get("file_name", "")
    file_size = file_data.get("file_size", "")
    original_caption = file_data.get("original_caption", "")
    
    # File name variations
    first_file = all_files[0] if all_files else file_data
    last_file = all_files[-1] if all_files else file_data
    
    filenamefirst = first_file.get("file_name", "")
    filenamelast = last_file.get("file_name", "")
    filecaptionfirst = first_file.get("original_caption", "")
    filecaptionlast = last_file.get("original_caption", "")
    
    # Basic links
    log_msg_id = file_data.get("log_msg_id", "")
    file_hash = file_data.get("file_hash", "")
    
    # Create base URLs
    base_stream_url = f"{random.choice(Domain.CLOUDFLARE_URLS)}watch/{log_msg_id}?hash={file_hash}"
    base_download_url = f"{random.choice(Domain.CLOUDFLARE_URLS)}dl/{log_msg_id}?hash={file_hash}"
    base_storage_url = f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{log_msg_id}"
    
    # Create shortened links for each shortener concurrently
    
    tasks = []
    tasks.append(create_shortened_link(base_stream_url, shortlinks.get("shortlink1", {})))
    tasks.append(create_shortened_link(base_stream_url, shortlinks.get("shortlink2", {})))
    tasks.append(create_shortened_link(base_stream_url, shortlinks.get("shortlink3", {})))
    tasks.append(create_shortened_link(base_download_url, shortlinks.get("shortlink1", {})))
    tasks.append(create_shortened_link(base_download_url, shortlinks.get("shortlink2", {})))
    tasks.append(create_shortened_link(base_download_url, shortlinks.get("shortlink3", {})))
    tasks.append(create_shortened_link(base_storage_url, shortlinks.get("shortlink1", {})))
    tasks.append(create_shortened_link(base_storage_url, shortlinks.get("shortlink2", {})))
    tasks.append(create_shortened_link(base_storage_url, shortlinks.get("shortlink3", {})))
    
    # Process all shortening tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Extract results (handle exceptions by using original URLs)
    stream_link_1 = results[0] if not isinstance(results[0], Exception) else base_stream_url
    stream_link_2 = results[1] if not isinstance(results[1], Exception) else base_stream_url
    stream_link_3 = results[2] if not isinstance(results[2], Exception) else base_stream_url
    download_link_1 = results[3] if not isinstance(results[3], Exception) else base_download_url
    download_link_2 = results[4] if not isinstance(results[4], Exception) else base_download_url
    download_link_3 = results[5] if not isinstance(results[5], Exception) else base_download_url
    storage_link_1 = results[6] if not isinstance(results[6], Exception) else base_storage_url
    storage_link_2 = results[7] if not isinstance(results[7], Exception) else base_storage_url
    storage_link_3 = results[8] if not isinstance(results[8], Exception) else base_storage_url
    
    # Regular links (without shorteners)
    stream_link = base_stream_url
    download_link = base_download_url
    storage_link = base_storage_url
    
    # Quality, season, episode extraction
    quality = file_data.get("quality", "")
    season = file_data.get("season", "")
    episode = file_data.get("episode", "")
    
    result_dict = {
        "filenamefirst": filenamefirst,
        "filenamelast": filenamelast,
        "filecaptionfirst": filecaptionfirst,
        "filecaptionlast": filecaptionlast,
        "file_name": file_name,
        "filename": file_name,  # Add this alias
        "file_size": file_size,
        "quality": quality,
        "season": season,
        "episode": episode,
        "stream_link": stream_link,
        "download_link": download_link,
        "storage_link": storage_link,
        "stream_link_1": stream_link_1,
        "stream_link_2": stream_link_2,
        "stream_link_3": stream_link_3,
        "download_link_1": download_link_1,
        "download_link_2": download_link_2,
        "download_link_3": download_link_3,
        "storage_link_1": storage_link_1,
        "storage_link_2": storage_link_2,
        "storage_link_3": storage_link_3,
    }
    
    return result_dict


async def create_shortened_link(original_url, shortener_config):
    """Create shortened link using specified shortener or return original URL"""
    url = shortener_config.get("url")
    api = shortener_config.get("api")
    
    if not url or not api:
        return original_url
    
    try:
        from MrAKTech.tools.utils_bot import short_link_with_custom_shortener
        shortened = await short_link_with_custom_shortener(original_url, url, api)
        return shortened
    except Exception as e:
        return original_url
        

@StreamBot.on_message(filters.command("setcaption1") & filters.private)
async def set_caption1_cmd(bot, message):
    """Set caption 1 for linkmode"""
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    await message.reply_text(
        "📝 <b>SET LINKMODE CAPTION 1</b>\n\n"
        "Please send your caption template for Caption 1.\n\n"
        "<b>📋 Available Placeholders:</b>\n"
        "• <code>{filenamefirst}</code> - First file name\n"
        "• <code>{filenamelast}</code> - Last file name\n"
        "• <code>{filecaptionfirst}</code> - First file caption\n"
        "• <code>{filecaptionlast}</code> - Last file caption\n"
        "• <code>{stream_link_1}</code>, <code>{stream_link_2}</code>, <code>{stream_link_3}</code>\n"
        "• <code>{download_link_1}</code>, <code>{download_link_2}</code>, <code>{download_link_3}</code>\n"
        "• <code>{storage_link_1}</code>, <code>{storage_link_2}</code>, <code>{storage_link_3}</code>\n"
        "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>\n\n"
        "💡 <i>Send /cancel to cancel this operation</i>",
        quote=True
    )
    
    # Set user state to expect caption 1
    await u_db.set_user_state(user_id, "waiting_caption_1")


@StreamBot.on_message(filters.command("setcaption2") & filters.private)
async def set_caption2_cmd(bot, message):
    """Set caption 2 for linkmode"""
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    await message.reply_text(
        "📝 <b>SET LINKMODE CAPTION 2</b>\n\n"
        "Please send your caption template for Caption 2.\n\n"
        "<b>📋 Available Placeholders:</b>\n"
        "• <code>{filenamefirst}</code> - First file name\n"
        "• <code>{filenamelast}</code> - Last file name\n"
        "• <code>{filecaptionfirst}</code> - First file caption\n"
        "• <code>{filecaptionlast}</code> - Last file caption\n"
        "• <code>{stream_link_1}</code>, <code>{stream_link_2}</code>, <code>{stream_link_3}</code>\n"
        "• <code>{download_link_1}</code>, <code>{download_link_2}</code>, <code>{download_link_3}</code>\n"
        "• <code>{storage_link_1}</code>, <code>{storage_link_2}</code>, <code>{storage_link_3}</code>\n"
        "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>\n\n"
        "💡 <i>Send /cancel to cancel this operation</i>",
        quote=True
    )
    
    # Set user state to expect caption 2
    await u_db.set_user_state(user_id, "waiting_caption_2")


@StreamBot.on_message(filters.command("setcaption3") & filters.private)
async def set_caption3_cmd(bot, message):
    """Set caption 3 for linkmode"""
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    await message.reply_text(
        "📝 <b>SET LINKMODE CAPTION 3</b>\n\n"
        "Please send your caption template for Caption 3.\n\n"
        "<b>📋 Available Placeholders:</b>\n"
        "• <code>{filenamefirst}</code> - First file name\n"
        "• <code>{filenamelast}</code> - Last file name\n"
        "• <code>{filecaptionfirst}</code> - First file caption\n"
        "• <code>{filecaptionlast}</code> - Last file caption\n"
        "• <code>{stream_link_1}</code>, <code>{stream_link_2}</code>, <code>{stream_link_3}</code>\n"
        "• <code>{download_link_1}</code>, <code>{download_link_2}</code>, <code>{download_link_3}</code>\n"
        "• <code>{storage_link_1}</code>, <code>{storage_link_2}</code>, <code>{storage_link_3}</code>\n"
        "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>\n\n"
        "💡 <i>Send /cancel to cancel this operation</i>",
        quote=True
    )
    
    # Set user state to expect caption 3
    await u_db.set_user_state(user_id, "waiting_caption_3")


@StreamBot.on_message(filters.command("cancel") & filters.private)
async def cancel_operation_cmd(bot, message):
    """Cancel any ongoing operation"""
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    # Clear any waiting state
    await u_db.set_user_state(user_id, None)
    
    await message.reply_text(
        "❌ <b>OPERATION CANCELLED</b>\n\n"
        "✅ Any pending operation has been cancelled",
        quote=True
    )


@StreamBot.on_message(filters.command("linkhelp") & filters.private)
async def linkhelp_cmd(bot, message):
    """Show how to use links in captions"""
    if not await verify_user(bot, message):
        return
    
    help_text = """<b>🔗 LINK FORMATTING GUIDE</b>

<b>📝 How to add clickable links in your captions:</b>

<b>🎯 Method 1 - Markdown Format:</b>
<code>[Link Text](https://example.com)</code>

<b>🎯 Method 2 - HTML Format:</b>
<code>&lt;a href="https://example.com"&gt;Link Text&lt;/a&gt;</code>

<b>💡 Examples:</b>

<b>1. Tutorial Link:</b>
<code>[How to open shortener URL](https://t.me/shotner_solution/6)</code>

<b>2. Channel Link:</b>
<code>[Join our channel](@Back2flix_Links)</code>

<b>3. Multiple Links:</b>
<code>Download links:
[Mirror 1](https://link1.com)
[Mirror 2](https://link2.com)
[Mirror 3](https://link3.com)</code>

<b>✅ Your Example Caption:</b>
<code>Maargan (2025) Tamil HQ HDTS

❤️‍🔥 Uploaded By - [@Back2flix_Links]

🗂️ 200MB :- https://lksfy.com/C6ztokG2D
🗂️ 400MB :- https://lksfy.com/eoCeA

✔️ Note: [How to open lksfty Url](https://t.me/shotner_solution/6)

📱 Share with friends 📌</code>

<b>🎨 Tips:</b>
• Links work in both regular and linkmode captions
• You can mix regular URLs and clickable links
• Use meaningful link text for better user experience
• Test your links before sharing"""
    
    await send_long_message(
        message,
        help_text,
        quote=True,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Set Caption", callback_data="add_caption"),
                InlineKeyboardButton("🔗 Linkmode", callback_data="custom_linkmode")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )


@StreamBot.on_message(filters.command("linkexample") & filters.private)
async def link_example_cmd(bot, message):
    """Show examples of proper link formatting in captions"""
    if not await verify_user(bot, message):
        return
    
    example_text = """<b>🔗 LINK FORMATTING EXAMPLES</b>

<b>✅ WORKING EXAMPLES:</b>

<b>Example 1 - Mixed Links:</b>
<code>{filenamefirst}

S{season} EP{episode} : {stream_link_1}

<b>[Join Channel](https://telegram.me/MrAK_LinkZzz)</b>

<a href="https://telegram.me/MrAK_LinkZzz">Join</a></code>

<b>Example 2 - All Markdown:</b>
<code>🎬 {filenamefirst}

[📺 Watch Online]({stream_link_1})
[📥 Download]({download_link_1})
[📱 Join Channel](https://telegram.me/MrAK_LinkZzz)</code>

<b>Example 3 - All HTML:</b>
<code>&lt;b&gt;{filenamefirst}&lt;/b&gt;

&lt;a href="{stream_link_1}"&gt;📺 Watch Online&lt;/a&gt;
&lt;a href="{download_link_1}"&gt;📥 Download&lt;/a&gt;
&lt;a href="https://telegram.me/MrAK_LinkZzz"&gt;📱 Join&lt;/a&gt;</code>

<b>💡 How it Works:</b>
• The bot automatically converts all links to HTML format
• Markdown links <code>[text](url)</code> become <code>&lt;a href="url"&gt;text&lt;/a&gt;</code>
• HTML links remain unchanged
• Mixed formats work perfectly!

<b>🎯 Result:</b> All your links will be clickable in Telegram, regardless of the original format!</b>"""
    
    await send_long_message(
        message,
        example_text,
        quote=True,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Set Caption", callback_data="add_caption"),
                InlineKeyboardButton("🔗 Linkmode", callback_data="custom_linkmode")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )


async def send_long_message(message, text, **kwargs):
    """Send a long message by splitting it into chunks if it exceeds Telegram's limit"""
    from MrAKTech.tools.link_formatter import format_links_in_text
    
    # Format links in the text before sending
    text = format_links_in_text(text, "HTML")
    
    max_length = 4096  # Telegram's message limit
    max_chunks = 10  # Maximum number of chunks to prevent spam
    
    # Ensure parse_mode is set to HTML for proper link formatting
    if 'parse_mode' not in kwargs:
        kwargs['parse_mode'] = ParseMode.HTML
    
    if len(text) <= max_length:
        return await message.reply_text(text, **kwargs)
    
    # If text is extremely long, truncate it
    max_total_length = max_length * max_chunks
    if len(text) > max_total_length:
        text = text[:max_total_length - 100] + "\n\n⚠️ Message truncated due to length limit"
    
    # Split the text into chunks
    chunks = []
    current_chunk = ""
    
    # Split by lines to preserve formatting
    lines = text.split('\n')
    
    for line in lines:
        # If adding this line would exceed the limit, save current chunk and start new one
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                # Line itself is too long, split it
                while len(line) > max_length:
                    chunks.append(line[:max_length])
                    line = line[max_length:]
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
        
        # Stop if we've reached the maximum number of chunks
        if len(chunks) >= max_chunks:
            break
    
    if current_chunk and len(chunks) < max_chunks:
        chunks.append(current_chunk)
    
    # Send first chunk as reply
    messages = []
    if chunks:
        messages.append(await message.reply_text(chunks[0], **kwargs))
        
        # Send remaining chunks as regular messages
        for chunk in chunks[1:]:
            messages.append(await message.reply_text(chunk, **kwargs))
    
    return messages


@StreamBot.on_message(filters.command(["setactivecaption1", "setactivecaption2", "setactivecaption3"]) & filters.private)
async def set_active_caption_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    command = message.text.split()[0].lower()
    caption_num = int(command[-1])  # Extract number from command
    
    # Check if the caption exists
    caption = await u_db.get_linkmode_caption(user_id, caption_num)
    if not caption:
        await message.reply_text(
            f"❌ <b>Caption {caption_num} not found</b>\n\n"
            f"Please set caption {caption_num} first using:\n"
            f"<code>/setlinkmodecaption</code> → Caption {caption_num} → Add Caption",
            quote=True
        )
        return
    
    # Set as active caption
    await u_db.set_active_linkmode_caption(user_id, caption_num)
    
    await message.reply_text(
        f"✅ <b>CAPTION {caption_num} SET AS ACTIVE</b>\n\n"
        f"🎯 Caption {caption_num} is now your active linkmode caption\n\n"
        f"<b>Preview:</b>\n"
        f"<code>{caption[:200]}{'...' if len(caption) > 200 else ''}</code>\n\n"
        f"💡 This caption will be used when you run /complete in linkmode",
        quote=True,
        disable_web_page_preview=True
    )


@StreamBot.on_message(filters.command("getactivecaption") & filters.private)
async def get_active_caption_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    active_caption_num = await u_db.get_active_linkmode_caption(user_id)
    
    if not active_caption_num:
        await message.reply_text(
            "ℹ️ <b>No active caption set</b>\n\n"
            "🔄 Default caption will be used for linkmode\n\n"
            "<b>Set an active caption:</b>\n"
            "• <code>/setactivecaption1</code>\n"
            "• <code>/setactivecaption2</code>\n"
            "• <code>/setactivecaption3</code>",
            quote=True
        )
        return
    
    active_caption = await u_db.get_linkmode_caption(user_id, active_caption_num)
    
    await message.reply_text(
        f"🎯 <b>ACTIVE CAPTION: {active_caption_num}</b>\n\n"
        f"<b>Current Active Caption:</b>\n"
        f"<code>{active_caption[:300]}{'...' if len(active_caption) > 300 else ''}</code>\n\n"
        f"<b>Change active caption:</b>\n"
        f"• <code>/setactivecaption1</code>\n"
        f"• <code>/setactivecaption2</code>\n"
        f"• <code>/setactivecaption3</code>",
        quote=True,
        disable_web_page_preview=True
    )


@StreamBot.on_message(filters.command("clearactivecaption") & filters.private)
async def clear_active_caption_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    await u_db.set_active_linkmode_caption(user_id, None)
    
    await message.reply_text(
        "🔄 <b>ACTIVE CAPTION CLEARED</b>\n\n"
        "✅ No active caption is set\n"
        "🔄 Default caption will be used for linkmode\n\n"
        "<b>Set a new active caption:</b>\n"
        "• <code>/setactivecaption1</code>\n"
        "• <code>/setactivecaption2</code>\n"
        "• <code>/setactivecaption3</code>",
        quote=True
    )


# PAGE MODE SHORTLINK MANAGEMENT COMMANDS

@StreamBot.on_message(filters.command(["pageshortlink1", "psl1"]) & filters.private)
async def pageshortlink1_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CONFIGURE PAGE SHORTLINK 1</b>\n\n"
            "<b>Usage:</b> <code>/pageshortlink1 api_key domain_name</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/pageshortlink1 abc123xyz example.com</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• API: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink1', {}).get('api', 'Not set')}</code>\n"
            f"• Domain: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink1', {}).get('domain', 'Not set')}</code>",
            quote=True
        )
        return
    
    try:
        args = message.text.split(None, 2)
        api_key = args[1]
        domain = args[2] if len(args) > 2 else None
        
        # Update shortlink settings
        shortlinks = await u_db.get_page_shortlinks(user_id)
        if 'shortlink1' not in shortlinks:
            shortlinks['shortlink1'] = {}
        
        shortlinks['shortlink1']['api'] = api_key
        if domain:
            shortlinks['shortlink1']['domain'] = domain
        
        await u_db.set_page_shortlinks(user_id, shortlinks)
        
        await message.reply_text(
            "✅ <b>PAGE SHORTLINK 1 UPDATED</b>\n\n"
            f"🔑 <b>API:</b> <code>{api_key}</code>\n"
            f"🌐 <b>Domain:</b> <code>{domain or 'Using default'}</code>\n\n"
            "Your first shortlink is now configured for page mode!",
            quote=True
        )
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Failed to update shortlink settings. Please check your input format.\n\n"
            "<b>Usage:</b> <code>/pageshortlink1 api_key domain_name</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["pageshortlink2", "psl2"]) & filters.private)
async def pageshortlink2_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CONFIGURE PAGE SHORTLINK 2</b>\n\n"
            "<b>Usage:</b> <code>/pageshortlink2 api_key domain_name</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/pageshortlink2 xyz456abc example2.com</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• API: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink2', {}).get('api', 'Not set')}</code>\n"
            f"• Domain: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink2', {}).get('domain', 'Not set')}</code>",
            quote=True
        )
        return
    
    try:
        args = message.text.split(None, 2)
        api_key = args[1]
        domain = args[2] if len(args) > 2 else None
        
        shortlinks = await u_db.get_page_shortlinks(user_id)
        if 'shortlink2' not in shortlinks:
            shortlinks['shortlink2'] = {}
        
        shortlinks['shortlink2']['api'] = api_key
        if domain:
            shortlinks['shortlink2']['domain'] = domain
        
        await u_db.set_page_shortlinks(user_id, shortlinks)
        
        await message.reply_text(
            "✅ <b>PAGE SHORTLINK 2 UPDATED</b>\n\n"
            f"🔑 <b>API:</b> <code>{api_key}</code>\n"
            f"🌐 <b>Domain:</b> <code>{domain or 'Using default'}</code>\n\n"
            "Your second shortlink is now configured for page mode!",
            quote=True
        )
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Failed to update shortlink settings. Please check your input format.\n\n"
            "<b>Usage:</b> <code>/pageshortlink2 api_key domain_name</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["pageshortlink3", "psl3"]) & filters.private)
async def pageshortlink3_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CONFIGURE PAGE SHORTLINK 3</b>\n\n"
            "<b>Usage:</b> <code>/pageshortlink3 api_key domain_name</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/pageshortlink3 def789ghi example3.com</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• API: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink3', {}).get('api', 'Not set')}</code>\n"
            f"• Domain: <code>{(await u_db.get_page_shortlinks(user_id)).get('shortlink3', {}).get('domain', 'Not set')}</code>",
            quote=True
        )
        return
    
    try:
        args = message.text.split(None, 2)
        api_key = args[1]
        domain = args[2] if len(args) > 2 else None
        
        shortlinks = await u_db.get_page_shortlinks(user_id)
        if 'shortlink3' not in shortlinks:
            shortlinks['shortlink3'] = {}
        
        shortlinks['shortlink3']['api'] = api_key
        if domain:
            shortlinks['shortlink3']['domain'] = domain
        
        await u_db.set_page_shortlinks(user_id, shortlinks)
        
        await message.reply_text(
            "✅ <b>PAGE SHORTLINK 3 UPDATED</b>\n\n"
            f"🔑 <b>API:</b> <code>{api_key}</code>\n"
            f"🌐 <b>Domain:</b> <code>{domain or 'Using default'}</code>\n\n"
            "Your third shortlink is now configured for page mode!",
            quote=True
        )
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Failed to update shortlink settings. Please check your input format.\n\n"
            "<b>Usage:</b> <code>/pageshortlink3 api_key domain_name</code>",
            quote=True
        )

# VERIFY MODE SHORTLINK COMMANDS

@StreamBot.on_message(filters.command(["verifyshortlink1", "vsl1"]) & filters.private)
async def verifyshortlink1_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CONFIGURE VERIFY SHORTLINK 1</b>\n\n"
            "<b>Usage:</b> <code>/verifyshortlink1 api_key domain_name</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/verifyshortlink1 verify123 verify1.com</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• API: <code>{(await u_db.get_verify_shortlinks(user_id)).get('shortlink1', {}).get('api', 'Not set')}</code>\n"
            f"• Domain: <code>{(await u_db.get_verify_shortlinks(user_id)).get('shortlink1', {}).get('domain', 'Not set')}</code>",
            quote=True
        )
        return
    
    try:
        args = message.text.split(None, 2)
        api_key = args[1]
        domain = args[2] if len(args) > 2 else None
        
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        if 'shortlink1' not in verify_shortlinks:
            verify_shortlinks['shortlink1'] = {}
        
        verify_shortlinks['shortlink1']['api'] = api_key
        if domain:
            verify_shortlinks['shortlink1']['domain'] = domain
        
        await u_db.set_verify_shortlinks(user_id, verify_shortlinks)
        
        await message.reply_text(
            "✅ <b>VERIFY SHORTLINK 1 UPDATED</b>\n\n"
            f"🔑 <b>API:</b> <code>{api_key}</code>\n"
            f"🌐 <b>Domain:</b> <code>{domain or 'Using default'}</code>\n\n"
            "Your first verify shortlink is now configured!",
            quote=True
        )
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Failed to update verify shortlink settings. Please check your input format.\n\n"
            "<b>Usage:</b> <code>/verifyshortlink1 api_key domain_name</code>",
            quote=True
        )

# BUTTON NAME CUSTOMIZATION COMMANDS

@StreamBot.on_message(filters.command(["watchbuttonname", "wbn"]) & filters.private)
async def watch_button_name_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CUSTOMIZE WATCH BUTTON NAME</b>\n\n"
            "<b>Usage:</b> <code>/watchbuttonname Your Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/watchbuttonname Watch Online</code>\n"
            "• <code>/watchbuttonname Stream Now</code>\n"
            "• <code>/watchbuttonname 🎬 Play</code>\n\n"
            f"<b>Current Name:</b> <code>{(await u_db.get_page_settings(user_id))['button_names']['watch']}</code>",
            quote=True
        )
        return
    
    button_text = message.text.split(None, 1)[1]
    if len(button_text) > 20:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Button name too long! Please keep it under 20 characters.",
            quote=True
        )
        return
    
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['button_names']['watch'] = button_text
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>WATCH BUTTON NAME UPDATED</b>\n\n"
        f"🎮 <b>New Name:</b> <code>{button_text}</code>\n\n"
        "This name will appear on all your shortlink pages!",
        quote=True
    )

@StreamBot.on_message(filters.command(["downloadbuttonname", "dbn"]) & filters.private)
async def download_button_name_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CUSTOMIZE DOWNLOAD BUTTON NAME</b>\n\n"
            "<b>Usage:</b> <code>/downloadbuttonname Your Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/downloadbuttonname Download Now</code>\n"
            "• <code>/downloadbuttonname Get File</code>\n"
            "• <code>/downloadbuttonname 📥 Download</code>\n\n"
            f"<b>Current Name:</b> <code>{(await u_db.get_page_settings(user_id))['button_names']['download']}</code>",
            quote=True
        )
        return
    
    button_text = message.text.split(None, 1)[1]
    if len(button_text) > 20:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Button name too long! Please keep it under 20 characters.",
            quote=True
        )
        return
    
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['button_names']['download'] = button_text
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>DOWNLOAD BUTTON NAME UPDATED</b>\n\n"
        f"📥 <b>New Name:</b> <code>{button_text}</code>\n\n"
        "This name will appear on all your shortlink pages!",
        quote=True
    )

@StreamBot.on_message(filters.command(["telegrambuttonname", "tbn"]) & filters.private)
async def telegram_button_name_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2:
        await message.reply_text(
            "📝 <b>CUSTOMIZE TELEGRAM BUTTON NAME</b>\n\n"
            "<b>Usage:</b> <code>/telegrambuttonname Your Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/telegrambuttonname Join Channel</code>\n"
            "• <code>/telegrambuttonname Follow Us</code>\n"
            "• <code>/telegrambuttonname 📢 Channel</code>\n\n"
            f"<b>Current Name:</b> <code>{(await u_db.get_page_settings(user_id))['button_names']['telegram']}</code>",
            quote=True
        )
        return
    
    button_text = message.text.split(None, 1)[1]
    if len(button_text) > 20:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Button name too long! Please keep it under 20 characters.",
            quote=True
        )
        return
    
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['button_names']['telegram'] = button_text
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>TELEGRAM BUTTON NAME UPDATED</b>\n\n"
        f"📱 <b>New Name:</b> <code>{button_text}</code>\n\n"
        "This name will appear on all your shortlink pages!",
        quote=True
    )

# CUSTOM BUTTONS MANAGEMENT

@StreamBot.on_message(filters.command(["addcustombutton", "acb"]) & filters.private)
async def add_custom_button_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2 or '|' not in message.text:
        await message.reply_text(
            "📝 <b>ADD CUSTOM BUTTON</b>\n\n"
            "<b>Usage:</b> <code>/addcustombutton Name | URL</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/addcustombutton Join Channel | https://t.me/your_channel</code>\n"
            "• <code>/addcustombutton Support | https://t.me/support_bot</code>\n"
            "• <code>/addcustombutton Website | https://example.com</code>\n\n"
            "<b>Note:</b> You can add up to 5 custom buttons.",
            quote=True
        )
        return
    
    try:
        button_data = message.text.split(None, 1)[1]
        if '|' not in button_data:
            raise ValueError("Invalid format")
        
        name, url = [x.strip() for x in button_data.split('|', 1)]
        
        if not name or not url:
            raise ValueError("Name and URL required")
        
        if len(name) > 20:
            await message.reply_text(
                "❌ <b>ERROR</b>\n\n"
                "Button name too long! Please keep it under 20 characters.",
                quote=True
            )
            return
        
        if not url.startswith(('http://', 'https://', 'tg://', 't.me')):
            await message.reply_text(
                "❌ <b>ERROR</b>\n\n"
                "Invalid URL format. Please use a valid URL starting with http://, https://, tg://, or t.me",
                quote=True
            )
            return
        
        page_settings = await u_db.get_page_settings(user_id)
        custom_buttons = page_settings.get('custom_buttons', [])
        
        if len(custom_buttons) >= 5:
            await message.reply_text(
                "❌ <b>ERROR</b>\n\n"
                "You already have 5 custom buttons (maximum limit).\n"
                "Please remove a button first using <code>/removecustombutton number</code>",
                quote=True
            )
            return
        
        custom_buttons.append({
            'name': name,
            'url': url
        })
        
        page_settings['custom_buttons'] = custom_buttons
        await u_db.update_page_settings(user_id, page_settings)
        
        await message.reply_text(
            "✅ <b>CUSTOM BUTTON ADDED</b>\n\n"
            f"📝 <b>Name:</b> <code>{name}</code>\n"
            f"🔗 <b>URL:</b> <code>{url}</code>\n\n"
            f"You now have {len(custom_buttons)}/5 custom buttons configured.",
            quote=True
        )
        
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Invalid format. Please use:\n"
            "<code>/addcustombutton Name | URL</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["removecustombutton", "rcb"]) & filters.private)
async def remove_custom_button_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    page_settings = await u_db.get_page_settings(user_id)
    custom_buttons = page_settings.get('custom_buttons', [])
    
    if not custom_buttons:
        await message.reply_text(
            "❌ <b>NO CUSTOM BUTTONS</b>\n\n"
            "You don't have any custom buttons configured.\n"
            "Add one using <code>/addcustombutton Name | URL</code>",
            quote=True
        )
        return
    
    if len(message.text.split()) < 2:
        # Show list of buttons
        text = "📝 <b>YOUR CUSTOM BUTTONS</b>\n\n"
        for i, btn in enumerate(custom_buttons, 1):
            text += f"<b>{i}.</b> {btn['name']} → <code>{btn['url']}</code>\n"
        
        text += f"\n<b>Usage:</b> <code>/removecustombutton number</code>\n"
        text += f"<b>Example:</b> <code>/removecustombutton 1</code>"
        
        await message.reply_text(text, quote=True)
        return
    
    try:
        button_num = int(message.text.split()[1])
        if button_num < 1 or button_num > len(custom_buttons):
            raise ValueError("Invalid number")
        
        removed_button = custom_buttons.pop(button_num - 1)
        page_settings['custom_buttons'] = custom_buttons
        await u_db.update_page_settings(user_id, page_settings)
        
        await message.reply_text(
            "✅ <b>CUSTOM BUTTON REMOVED</b>\n\n"
            f"📝 <b>Removed:</b> <code>{removed_button['name']}</code>\n\n"
            f"You now have {len(custom_buttons)}/5 custom buttons configured.",
            quote=True
        )
        
    except (ValueError, IndexError):
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Invalid button number. Please specify a valid number.\n"
            "Use <code>/removecustombutton</code> to see the list first.",
            quote=True
        )

@StreamBot.on_message(filters.command(["listcustombuttons", "lcb"]) & filters.private)
async def list_custom_buttons_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    page_settings = await u_db.get_page_settings(user_id)
    custom_buttons = page_settings.get('custom_buttons', [])
    
    if not custom_buttons:
        await message.reply_text(
            "❌ <b>NO CUSTOM BUTTONS</b>\n\n"
            "You don't have any custom buttons configured.\n\n"
            "<b>Add one using:</b>\n"
            "<code>/addcustombutton Name | URL</code>",
            quote=True
        )
        return
    
    text = "📝 <b>YOUR CUSTOM BUTTONS</b>\n\n"
    for i, btn in enumerate(custom_buttons, 1):
        text += f"<b>{i}.</b> {btn['name']}\n"
        text += f"   🔗 <code>{btn['url']}</code>\n\n"
    
    text += f"<b>Total:</b> {len(custom_buttons)}/5 buttons\n\n"
    text += "<b>Commands:</b>\n"
    text += "• <code>/addcustombutton Name | URL</code>\n"
    text += "• <code>/removecustombutton number</code>"
    
    await message.reply_text(text, quote=True)

# TUTORIAL SETTINGS COMMANDS

@StreamBot.on_message(filters.command(["tutorial1", "t1"]) & filters.private)
async def tutorial1_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2 or '|' not in message.text:
        current_tutorial = (await u_db.get_page_settings(user_id))['shortlink_tutorials'].get('shortlink1', {})
        await message.reply_text(
            "📝 <b>CONFIGURE TUTORIAL 1</b>\n\n"
            "<b>Usage:</b> <code>/tutorial1 URL | Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/tutorial1 https://youtube.com/watch?v=abc | How to Download</code>\n"
            "• <code>/tutorial1 https://t.me/tutorial_channel/123 | Watch Tutorial</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• Status: {'✅ Enabled' if current_tutorial.get('enabled', False) else '❌ Disabled'}\n"
            f"• URL: <code>{current_tutorial.get('url', 'Not set')}</code>\n"
            f"• Text: <code>{current_tutorial.get('text', 'Tutorial 1')}</code>",
            quote=True
        )
        return
    
    try:
        tutorial_data = message.text.split(None, 1)[1]
        if '|' not in tutorial_data:
            raise ValueError("Invalid format")
        
        url, text = [x.strip() for x in tutorial_data.split('|', 1)]
        
        if not url or not text:
            raise ValueError("URL and text required")
        
        if not url.startswith(('http://', 'https://', 'tg://', 't.me')):
            await message.reply_text(
                "❌ <b>ERROR</b>\n\n"
                "Invalid URL format. Please use a valid URL.",
                quote=True
            )
            return
        
        page_settings = await u_db.get_page_settings(user_id)
        page_settings['shortlink_tutorials']['shortlink1'] = {
            'enabled': True,
            'url': url,
            'text': text
        }
        await u_db.update_page_settings(user_id, page_settings)
        
        await message.reply_text(
            "✅ <b>TUTORIAL 1 CONFIGURED</b>\n\n"
            f"🔗 <b>URL:</b> <code>{url}</code>\n"
            f"📝 <b>Button Text:</b> <code>{text}</code>\n\n"
            "Tutorial is now enabled for shortlink 1!",
            quote=True
        )
        
    except Exception as e:
        await message.reply_text(
            "❌ <b>ERROR</b>\n\n"
            "Invalid format. Please use:\n"
            "<code>/tutorial1 URL | Button Text</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["tutorial2", "t2"]) & filters.private)
async def tutorial2_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2 or '|' not in message.text:
        current_tutorial = (await u_db.get_page_settings(user_id))['shortlink_tutorials'].get('shortlink2', {})
        await message.reply_text(
            "📝 <b>CONFIGURE TUTORIAL 2</b>\n\n"
            "<b>Usage:</b> <code>/tutorial2 URL | Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/tutorial2 https://youtube.com/watch?v=def | Step by Step Guide</code>\n"
            "• <code>/tutorial2 https://t.me/tutorial_channel/456 | Learn More</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• Status: {'✅ Enabled' if current_tutorial.get('enabled', False) else '❌ Disabled'}\n"
            f"• URL: <code>{current_tutorial.get('url', 'Not set')}</code>\n"
            f"• Text: <code>{current_tutorial.get('text', 'Tutorial 2')}</code>",
            quote=True
        )
        return
    
    try:
        tutorial_data = message.text.split(None, 1)[1]
        url, text = [x.strip() for x in tutorial_data.split('|', 1)]
        
        if not url.startswith(('http://', 'https://', 'tg://', 't.me')):
            await message.reply_text("❌ Invalid URL format.", quote=True)
            return
        
        page_settings = await u_db.get_page_settings(user_id)
        page_settings['shortlink_tutorials']['shortlink2'] = {
            'enabled': True,
            'url': url,
            'text': text
        }
        await u_db.update_page_settings(user_id, page_settings)
        
        await message.reply_text(
            "✅ <b>TUTORIAL 2 CONFIGURED</b>\n\n"
            f"🔗 <b>URL:</b> <code>{url}</code>\n"
            f"📝 <b>Button Text:</b> <code>{text}</code>\n\n"
            "Tutorial is now enabled for shortlink 2!",
            quote=True
        )
        
    except Exception as e:
        await message.reply_text(
            "❌ Invalid format. Use: <code>/tutorial2 URL | Button Text</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["tutorial3", "t3"]) & filters.private)
async def tutorial3_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    
    if len(message.text.split(None, 1)) < 2 or '|' not in message.text:
        current_tutorial = (await u_db.get_page_settings(user_id))['shortlink_tutorials'].get('shortlink3', {})
        await message.reply_text(
            "📝 <b>CONFIGURE TUTORIAL 3</b>\n\n"
            "<b>Usage:</b> <code>/tutorial3 URL | Button Text</code>\n\n"
            "<b>Examples:</b>\n"
            "• <code>/tutorial3 https://youtube.com/watch?v=ghi | Final Step Tutorial</code>\n"
            "• <code>/tutorial3 https://t.me/tutorial_channel/789 | Complete Guide</code>\n\n"
            "<b>Current Settings:</b>\n"
            f"• Status: {'✅ Enabled' if current_tutorial.get('enabled', False) else '❌ Disabled'}\n"
            f"• URL: <code>{current_tutorial.get('url', 'Not set')}</code>\n"
            f"• Text: <code>{current_tutorial.get('text', 'Tutorial 3')}</code>",
            quote=True
        )
        return
    
    try:
        tutorial_data = message.text.split(None, 1)[1]
        url, text = [x.strip() for x in tutorial_data.split('|', 1)]
        
        if not url.startswith(('http://', 'https://', 'tg://', 't.me')):
            await message.reply_text("❌ Invalid URL format.", quote=True)
            return
        
        page_settings = await u_db.get_page_settings(user_id)
        page_settings['shortlink_tutorials']['shortlink3'] = {
            'enabled': True,
            'url': url,
            'text': text
        }
        await u_db.update_page_settings(user_id, page_settings)
        
        await message.reply_text(
            "✅ <b>TUTORIAL 3 CONFIGURED</b>\n\n"
            f"🔗 <b>URL:</b> <code>{url}</code>\n"
            f"📝 <b>Button Text:</b> <code>{text}</code>\n\n"
            "Tutorial is now enabled for shortlink 3!",
            quote=True
        )
        
    except Exception as e:
        await message.reply_text(
            "❌ Invalid format. Use: <code>/tutorial3 URL | Button Text</code>",
            quote=True
        )

@StreamBot.on_message(filters.command(["disabletutorial1", "dt1"]) & filters.private)
async def disable_tutorial1_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['shortlink_tutorials']['shortlink1'] = {'enabled': False}
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>TUTORIAL 1 DISABLED</b>\n\n"
        "Tutorial button will no longer appear for shortlink 1.",
        quote=True
    )

@StreamBot.on_message(filters.command(["disabletutorial2", "dt2"]) & filters.private)
async def disable_tutorial2_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['shortlink_tutorials']['shortlink2'] = {'enabled': False}
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>TUTORIAL 2 DISABLED</b>\n\n"
        "Tutorial button will no longer appear for shortlink 2.",
        quote=True
    )

@StreamBot.on_message(filters.command(["disabletutorial3", "dt3"]) & filters.private)
async def disable_tutorial3_cmd(bot, message):
    if not await verify_user(bot, message):
        return
    
    user_id = message.from_user.id
    page_settings = await u_db.get_page_settings(user_id)
    page_settings['shortlink_tutorials']['shortlink3'] = {'enabled': False}
    await u_db.update_page_settings(user_id, page_settings)
    
    await message.reply_text(
        "✅ <b>TUTORIAL 3 DISABLED</b>\n\n"
        "Tutorial button will no longer appear for shortlink 3.",
        quote=True
    )
