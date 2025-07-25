import asyncio
import time
import datetime
import shutil
import psutil
from shortzy import Shortzy
from validators import domain

from pyrogram import enums
from pyrogram.errors import BadMsgNotification, FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from MrAKTech import StreamBot, work_loads, multi_clients, cdn_count
from MrAKTech.config import Telegram
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.txt import tamilxd, BUTTON
from MrAKTech.tools.utils_bot import readable_time, get_readable_file_size, temp, is_check_admin
from MrAKTech.tools.link_formatter import validate_links_in_text, format_links_in_text


def truncate_text(text, max_length=4000):
    """Truncate text to avoid MEDIA_CAPTION_TOO_LONG errors"""
    if len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # If we can find a space in the last 20%
        truncated = truncated[:last_space]
    
    return truncated + "\n\n<i>... (message truncated due to length)</i>"


async def safe_edit_message_text(query, text, **kwargs):
    """Edit message text with retry logic for BadMsgNotification errors"""
    max_retries = 3
    # Truncate text to prevent MEDIA_CAPTION_TOO_LONG errors
    text = truncate_text(text)
    
    for attempt in range(max_retries):
        try:
            return await query.message.edit_text(text, **kwargs)
        except Exception as e:
            if "MEDIA_CAPTION_TOO_LONG" in str(e) or "MESSAGE_TOO_LONG" in str(e):
                # Try with shorter text
                shorter_text = truncate_text(text, 2000)
                try:
                    return await query.message.edit_text(shorter_text, **kwargs)
                except:
                    await query.answer("⚠️ Message too long. Please try a shorter message.", show_alert=True)
                    return
            elif "BadMsgNotification" in str(e):
                if attempt == max_retries - 1:
                    print(f"Failed to edit message after {max_retries} attempts: {e}")
                    raise
                await asyncio.sleep(2 ** attempt)
            elif "FloodWait" in str(e):
                wait_time = int(str(e).split('of ')[1].split(' ')[0]) if 'of ' in str(e) else 5
                await asyncio.sleep(wait_time)
            else:
                print(f"Unexpected error editing message: {e}")
                if attempt == max_retries - 1:
                    await query.answer("❌ An error occurred. Please try again.", show_alert=True)
                    return
                await asyncio.sleep(1)


async def safe_answer_callback(query, text, **kwargs):
    """Answer callback query with retry logic for BadMsgNotification errors and message length limits"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await query.answer(text, **kwargs)
        except BadMsgNotification as e:
            if attempt == max_retries - 1:
                print(f"Failed to answer callback after {max_retries} attempts: {e}")
                raise
            await asyncio.sleep(2 ** attempt)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            # Handle MESSAGE_TOO_LONG error
            if "MESSAGE_TOO_LONG" in str(e):
                # Truncate the message to fit within Telegram's limits
                max_length = 200  # Telegram callback answer limit
                truncated_text = text[:max_length-3] + "..." if len(text) > max_length else text
                try:
                    return await query.answer(truncated_text, **kwargs)
                except Exception as truncate_error:
                    print(f"Failed to answer callback even with truncated message: {truncate_error}")
                    # Try with a generic message
                    return await query.answer("Caption too long to display in popup. Check your settings.", show_alert=True)
            
            print(f"Unexpected error answering callback: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)


@StreamBot.on_callback_query()
async def cb_handler(bot, query: CallbackQuery):
    try:
        data = query.data
        user_id = query.from_user.id
        userxdb = await u_db.get_user_details(user_id)
        
        # Callback started
        if data == "start":
            await safe_edit_message_text(
                query,
                text=(tamilxd.START_TXT.format(query.from_user.mention)),
                disable_web_page_preview=True,
                reply_markup=BUTTON.START_BUTTONS
            )

        elif data == "help":
            await safe_edit_message_text(
                query,
                text=tamilxd.HELP_TXT,
                disable_web_page_preview=True,
                reply_markup=BUTTON.HELP_BUTTONS
            )

        elif data == "owner":
            await safe_edit_message_text(
                query,
                text=tamilxd.OWNER_INFO,
                disable_web_page_preview=True,
                reply_markup=BUTTON.OWNER_BUTTONS
            )
            
        elif data == "about":
            await safe_edit_message_text(
                query,
                text=tamilxd.ABOUT_TXT,
                disable_web_page_preview=True,
                reply_markup=BUTTON.ABOUT_BUTTONS
            )

        elif data == "dev":
            m = await query.message.reply_sticker("CAACAgIAAxkBAAEJ8bxk0L2LAm0P4AABCIUXG6g7V03RTTQAAoAOAALUdQlKzIMOAcx1iKkwBA")
            await asyncio.sleep(3)
            await m.delete()
            caption = tamilxd.DEV_TXT
            tamil = await query.message.reply_photo(
                photo="https://telegra.ph/file/4e48e88fe9811add5fb22.jpg",
                caption=caption,
                reply_markup=InlineKeyboardMarkup([[
                   InlineKeyboardButton("✗ Close", callback_data="close")
                ]])
            )
            await asyncio.sleep(1600)
            await tamil.delete()
            await query.message.delete()

        elif data == "source":
            m = await query.message.reply_sticker("CAACAgUAAxkBAAEBlVBkoEL0LKGBhqNxTtVM_Ti0QHnO_AAC5wQAAo6i-VUZIF0fRfvjmx4E")
            await asyncio.sleep(2)
            await m.delete()
            tamil = await query.message.reply_photo(
                photo="https://graph.org/file/306e4f62551e994ee6792.jpg",
                caption=tamilxd.SOURCE_TXT,
                reply_markup=BUTTON.SOURCE_BUTTONS
            )
            await asyncio.sleep(10)
            await tamil.delete()
            await query.message.delete()

        elif data == "don":
            m = await query.message.reply_sticker("CAACAgUAAxkBAAEBlVBkoEL0LKGBhqNxTtVM_Ti0QHnO_AAC5wQAAo6i-VUZIF0fRfvjmx4E")
            await asyncio.sleep(3)
            await m.delete()
            tamil = await query.message.reply_photo(
                photo="https://telegra.ph/file/d6e78fb5f4288e91be748.jpg",
                caption=(tamilxd.DONATE_TXT),
                reply_markup=BUTTON.DONATE_BUTTONS,
            )
            await asyncio.sleep(1800)
            await tamil.delete()
            await query.message.delete()

        # Settings and user management
        elif data in ['settings', 'toggle_mode', 'storage_mode']:
            mode = await u_db.get_uploadmode(user_id)
            if data == "toggle_mode":
                if not mode:
                    mode = "links"
                elif mode == "links":
                    mode = "files"
                else:
                    mode = "links"
                await u_db.change_uploadmode(user_id, mode)

            buttons = []
            buttons.append([InlineKeyboardButton(
                "✅ Custom Caption" if userxdb.get('caption') and userxdb['caption'] != tamilxd.STREAM_TXT else "📝 Custom Caption",
                callback_data="custom_caption"
            )])
            buttons.append([InlineKeyboardButton(
                "✅ Custom Shortner" if userxdb.get('shortener_url') and userxdb.get('shortener_api') else "🖼️ Custom Shortner",
                callback_data="custom_shortner"
            )])

            linkmode_status = userxdb.get("linkmode", False)
            buttons.append([InlineKeyboardButton(
                "✅ Link Mode" if linkmode_status else "❌ Link Mode",
                callback_data="toggle_linkmode"
            )])
            buttons.append([InlineKeyboardButton('📤 Upload Mode', callback_data="toggle_mode"),
                            InlineKeyboardButton(mode if mode else "Links", callback_data="toggle_mode")])
            if await u_db.is_settings(user_id):
                buttons.append([InlineKeyboardButton('🛠️ Reset Settings', callback_data="reset_setting")])
            buttons.append([InlineKeyboardButton('Close', callback_data="close")])
            
            await safe_edit_message_text(
                query,
                text=tamilxd.SETTINGS_TXT.format(
                    CAPTION="✅ Exists" if userxdb.get("caption") else "❌ Not Exists",
                    URLX=userxdb.get("shortener_url", "❌ Not Exists"),
                    APIX=userxdb.get("shortener_api", "❌ Not Exists"),
                    STORAGEX=userxdb.get("storage", ""),
                    METHODX=userxdb.get("method", mode),
                    LINKMODE="✅ Enabled" if userxdb.get("linkmode", False) else "❌ Disabled",
                    PAGEMODE="✅ Enabled" if userxdb.get("page_mode", False) else "❌ Disabled",
                    VERIFYMODE="✅ Enabled" if userxdb.get("verify_mode", False) else "❌ Disabled"
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

        elif data == "reset_setting":
            await query.message.edit_text(
                text=tamilxd.RESET_SETTINGS,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Yes', callback_data="reset_settings"),
                    InlineKeyboardButton('No', callback_data="settings"),
                ]]))

        elif data == "reset_settings":
            await u_db.reset_settings(user_id)
            await query.answer("Successfully settings resetted.", show_alert=True)
            buttons = []
            buttons.append([InlineKeyboardButton("📝 Custom caption", callback_data="custom_caption")])
            buttons.append([InlineKeyboardButton("🖼️ Custom shortner", callback_data="custom_shortner")])
            buttons.append([InlineKeyboardButton("✅ Auto Extract", callback_data="toggle_extract")])
            buttons.append([InlineKeyboardButton("❌ Link Mode", callback_data="toggle_linkmode")])
            buttons.append([InlineKeyboardButton('📤 Upload mode', callback_data="toggle_mode"),
                            InlineKeyboardButton("Links", callback_data="toggle_mode")])
            buttons.append([InlineKeyboardButton('Close', callback_data="close")])
            await safe_edit_message_text(
                query,
                text=tamilxd.SETTINGS_TXT.format(
                    CAPTION="❌ Not Exists",
                    URLX="❌ Not Exists",
                    APIX="❌ Not Exists",
                    STORAGEX="Off",
                    METHODX="Links",
                    LINKMODE="❌ Disabled",
                    PAGEMODE="❌ Disabled",
                    VERIFYMODE="❌ Disabled"
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )

        # Caption management
        elif data == "custom_caption":
            buttons = []
            if userxdb.get('caption'):
                buttons.append([InlineKeyboardButton('Show caption', callback_data="show_caption")])
                buttons.append([InlineKeyboardButton('Default caption', callback_data="delete_caption"),
                                InlineKeyboardButton('Change caption', callback_data="add_caption")])
            else:
                buttons.append([InlineKeyboardButton('Set caption', callback_data="add_caption")])
            buttons.append([InlineKeyboardButton('≺≺ Back', callback_data="settings"),
                            InlineKeyboardButton('Close', callback_data="close")])
            await safe_edit_message_text(
                query,
                text=tamilxd.CUSTOM_CAPTION_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif data == "show_caption":
            caption = userxdb.get('caption', '')
            if len(caption) > 170:
                await query.message.edit_text(
                    text=caption,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]])
                )
            else:
                await safe_answer_callback(query, f"Your custom caption:\n\n{caption}", show_alert=True)

        elif data == "delete_caption":
            if not userxdb.get('caption'):
                return await query.answer("Nothing will found to delete.", show_alert=True)
            await u_db.set_caption(query.from_user.id, tamilxd.STREAM_TXT)
            return await query.answer("Caption removed successfully!", show_alert=True)

        # Shortener management
        elif data == "custom_shortner":
            buttons = []
            if userxdb.get('shortener_url') and userxdb.get('shortener_api'):
                buttons.append([InlineKeyboardButton('Show shortner', callback_data="show_shortner")])
                buttons.append([InlineKeyboardButton('Delete shortner', callback_data="delete_shortner"),
                                InlineKeyboardButton('Change shortner', callback_data="add_shortner")])
            else:
                buttons.append([InlineKeyboardButton('Set shortner', callback_data="add_shortner")])
            buttons.append([InlineKeyboardButton('≺≺ Back', callback_data="settings"),
                            InlineKeyboardButton('Close', callback_data="close")])
            await query.message.edit_text(
                text=tamilxd.CUSTOM_SHORTNER_TXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif data == "show_shortner":
            if not userxdb.get('shortener_url') or not userxdb.get('shortener_api'):
                return await query.answer("You didn't add any custom shortener URL", show_alert=True)
            await safe_answer_callback(query, f"Your custom shortener: \n\nURL - {userxdb['shortener_url']} \nAPI - {userxdb['shortener_api']}", show_alert=True)

        elif data == "delete_shortner":
            if not userxdb.get('shortener_url') or not userxdb.get('shortener_api'):
                return await query.answer("Nothing will found to delete.", show_alert=True)
            await u_db.set_shortner_url(query.from_user.id, None)
            await u_db.set_shortner_api(query.from_user.id, None)
            return await query.answer("Shortener removed successfully!", show_alert=True)

        elif data == "close":
            await query.message.delete()
            
    except Exception as e:
        # Handle any callback errors, especially MEDIA_CAPTION_TOO_LONG
        print(f"Callback error: {e}")
        try:
            if "MEDIA_CAPTION_TOO_LONG" in str(e):
                await query.answer("⚠️ Message too long. Please try again.", show_alert=True)
            else:
                await query.answer("❌ An error occurred. Please try again.", show_alert=True)
        except:
            pass  # If even the error message fails, just ignore
