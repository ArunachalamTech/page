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
# Fix for pyromod 1.5.0 compatibility
try:
    from pyromod.exceptions.listener_timeout import ListenerTimeout
except ImportError:
    try:
        from pyromod.exceptions import ListenerTimeout
    except ImportError:
        try:
            from pyromod import ListenerTimeout
        except ImportError:
            # Fallback: create a custom timeout exception
            class ListenerTimeout(Exception):
                """Custom timeout exception for pyromod compatibility"""
                pass

from MrAKTech import StreamBot, work_loads, multi_clients, cdn_count
from MrAKTech.config import Telegram
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.txt import tamilxd, BUTTON
from MrAKTech.tools.utils_bot import readable_time, get_readable_file_size, temp, is_check_admin
from MrAKTech.tools.link_formatter import validate_links_in_text, format_links_in_text


async def safe_edit_message_text(query, text, **kwargs):
    """Edit message text with retry logic for BadMsgNotification errors"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await query.message.edit_text(text, **kwargs)
        except BadMsgNotification as e:
            if attempt == max_retries - 1:
                print(f"Failed to edit message after {max_retries} attempts: {e}")
                raise
            await asyncio.sleep(2 ** attempt)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Unexpected error editing message: {e}")
            if attempt == max_retries - 1:
                raise
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

async def safe_edit_message(query, text, reply_markup=None, **kwargs):
    """Safely edit message with error handling for MessageNotModified and other errors"""
    try:
        return await query.message.edit_text(text, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        # Handle MESSAGE_NOT_MODIFIED error
        if "MESSAGE_NOT_MODIFIED" in str(e):
            # Message content is the same, just answer the callback query
            await query.answer("✅ Already up to date!", show_alert=False)
            return None
        elif "MESSAGE_TOO_LONG" in str(e):
            # Truncate message if too long
            max_length = 4096  # Telegram message limit
            truncated_text = text[:max_length-100] + "\n\n<b>... Message truncated ...</b>"
            try:
                return await query.message.edit_text(truncated_text, reply_markup=reply_markup, **kwargs)
            except Exception as inner_e:
                print(f"Failed to edit with truncated text: {inner_e}")
                await query.answer("❌ Message too long, please try again", show_alert=True)
                return None
        else:
            print(f"Unexpected error in safe_edit_message: {e}")
            await query.answer("❌ Error updating message", show_alert=True)
            raise


async def show_page_mode_settings(bot, query):
    """Helper function to show page mode settings"""
    user_id = query.from_user.id
    page_mode_status = await u_db.get_page_mode(user_id)
    verify_mode_status = await u_db.get_verify_mode(user_id)
    
    text = f"<b>📄 PAGE MODE SETTINGS</b>\n\n"
    text += f"<b>📊 Current Status:</b>\n"
    text += f"• Page Mode: {'✅ Enabled' if page_mode_status else '❌ Disabled'}\n"
    text += f"• Verify Mode: {'✅ Enabled' if verify_mode_status else '❌ Disabled'}\n\n"
    text += f"<b>⚡ Quick Setup:</b>\n"
    text += f"1. Enable Page Mode\n"
    text += f"2. Add shortlinks (optional)\n"
    text += f"3. Enable Verify Mode (optional)\n"
    text += f"4. Use {{web_link}} in captions\n\n"
    text += f"📚 Need help? Click info buttons below"
    
    buttons = []
    
    # Page Mode Toggle Button
    buttons.append([InlineKeyboardButton(f"{'❌ Disable' if page_mode_status else '✅ Enable'} Page Mode", callback_data="toggle_pagemode")])
    
    if page_mode_status:
        # Page Mode Management Buttons
        buttons.append([InlineKeyboardButton("⚙️ Manage Page Shortlinks", callback_data="pagemode_shortlinks")])
        buttons.append([InlineKeyboardButton("🎛️ Custom Buttons", callback_data="pagemode_custom_buttons")])
        
        # Verify Mode Section (always show when page mode is enabled)
        buttons.append([InlineKeyboardButton(f"{'❌ Disable' if verify_mode_status else '✅ Enable'} Verify Mode", callback_data="pagemode_toggle_verify")])
        
        if verify_mode_status:
            # Verify Management Buttons (show when verify mode is enabled)
            buttons.append([InlineKeyboardButton("🔐 Manage Verify Shortlinks", callback_data="pagemode_verify_shortlinks")])
            buttons.append([InlineKeyboardButton("⏱️ Verify Time Settings", callback_data="pagemode_verify_time")])
    else:
        # When page mode is disabled, show instruction
        buttons.append([InlineKeyboardButton("ℹ️ Page Mode Info", callback_data="pagemode_info")])
    
    # Add help buttons
    if page_mode_status and verify_mode_status:
        buttons.append([InlineKeyboardButton("📚 Verify Mode Help", callback_data="pagemode_verify_help")])
    
    buttons.append([InlineKeyboardButton("≺≺ Back to Settings", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)


async def show_pagemode_verify_shortlinks(bot, query):
    """Helper function to show verify shortlinks page"""
    user_id = query.from_user.id
    verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
    
    text = "<b>🔐 PAGE MODE VERIFY SHORTLINKS</b>\n\n"
    text += "<b>📋 Verification Logic:</b>\n"
    text += "• <b>First Visit:</b> User completes Verify Shortlink 3\n"
    text += "• <b>Second Visit:</b> User completes Verify Shortlink 2\n"
    text += "• <b>Third Visit:</b> User completes Verify Shortlink 1\n"
    text += "• <b>Fourth+ Visits:</b> Direct access to file\n"
    text += "• Verification count resets daily\n\n"
    
    for i in range(3, 0, -1):  # 3, 2, 1 order
        shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
        status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
        visit_order = ["Third", "Second", "First"][3-i]
        text += f"<b>Verify Shortlink {i}:</b> {status} ({visit_order} visit)\n"
        if shortlink_data["url"]:
            text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
            text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
        text += "\n"
    
    text += "<b>📝 Management:</b>\n"
    text += "• Configure each verify shortlink independently\n"
    text += "• Test shortlinks before saving\n"
    text += "• Remove shortlinks if not needed\n"
    text += "• Users progress through verification levels daily"
    
    buttons = []
    for i in range(3, 0, -1):  # 3, 2, 1 order for display
        shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
        status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
        visit_order = ["Third", "Second", "First"][3-i]
        buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i} ({visit_order} visit)", callback_data=f"pagemode_verify_shortlink_{i}")])
    
    buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)


@StreamBot.on_callback_query()
async def cb_handler(bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    userxdb = await u_db.get_user_details(user_id)
    # Callback started
    if data == "start":
        await query.message.edit_text(
            text=(tamilxd.START_TXT.format(query.from_user.mention)),
            disable_web_page_preview=True,
            reply_markup=BUTTON.START_BUTTONS
        )

    elif data == "help":
        await query.message.edit_text(
            text=tamilxd.HELP_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Next Page ➡️", callback_data="help_page_2")],
                [InlineKeyboardButton("≺≺ Back", callback_data="start"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "help_page_2":
        await query.message.edit_text(
            text=tamilxd.HELP_PAGE_2,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Previous Page", callback_data="help")],
                [InlineKeyboardButton("≺≺ Back", callback_data="start"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "owner":
        await query.message.edit_text(
            text=tamilxd.OWNER_INFO,
            disable_web_page_preview=True,
            reply_markup=BUTTON.OWNER_BUTTONS
        )
    elif data == "about":
        await query.message.edit_text(
            text=tamilxd.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )

    elif data == "dev":
        m=await query.message.reply_sticker("CAACAgIAAxkBAAEJ8bxk0L2LAm0P4AABCIUXG6g7V03RTTQAAoAOAALUdQlKzIMOAcx1iKkwBA")
        await asyncio.sleep(3)
        await m.delete()
        caption = tamilxd.DEV_TXT
        tamil=await query.message.reply_photo(
            photo="https://telegra.ph/file/4e48e88fe9811add5fb22.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup([[
               #InlineKeyboardButton("♙ ʜᴏᴍᴇ", callback_data = "start"),
               InlineKeyboardButton("✗ Close", callback_data = "close")
               ]]
            )
        )
        await asyncio.sleep(1600)
        await tamil.delete()
        await query.message.delete()

    elif data == "source":
        m=await query.message.reply_sticker("CAACAgUAAxkBAAEBlVBkoEL0LKGBhqNxTtVM_Ti0QHnO_AAC5wQAAo6i-VUZIF0fRfvjmx4E")
        await asyncio.sleep(2)
        await m.delete()
        tamil=await query.message.reply_photo(
            photo="https://graph.org/file/306e4f62551e994ee6792.jpg",
            caption=tamilxd.SOURCE_TXT,
            reply_markup=BUTTON.SOURCE_BUTTONS
        )
        await asyncio.sleep(10)
        await tamil.delete()
        await query.message.delete()

    elif data == "don":
        m=await query.message.reply_sticker("CAACAgUAAxkBAAEBlVBkoEL0LKGBhqNxTtVM_Ti0QHnO_AAC5wQAAo6i-VUZIF0fRfvjmx4E")
        await asyncio.sleep(3)
        await m.delete()
        tamil=await query.message.reply_photo(
            photo="https://telegra.ph/file/d6e78fb5f4288e91be748.jpg",
            caption=(tamilxd.DONATE_TXT),
            reply_markup=BUTTON.DONATE_BUTTONS,
        )
        await asyncio.sleep(1800)
        await tamil.delete()
        await query.message.delete()

    ########## USERS MAIN BOT DETAILS START ########

    elif data in ['toggle_mode', 'storage_mode']:
        mode = await u_db.get_uploadmode(user_id)
        # modex = await u_db.get_storagemode(user_id)
        if data == "toggle_mode":
            if not mode:
                mode = "links"
            elif mode == "links":
                mode = "files"
            else:
                # mode = None
                mode = "links"
            await u_db.change_uploadmode(user_id, mode)
        # if data == "storage_mode":
        #     if not modex:
        #         modex = "Off"
        #     elif modex == "Off":
        #         modex = "On"
        #     else:
        #      #mode = None
        #         modex = "Off"
        #     await u_db.change_storagemode(user_id, modex)

        # button = [[
        #     InlineKeyboardButton(
        #         "✅ Custom caption" if userxdb['caption'] is not None else "📝 Custom caption",
        #         callback_data="custom_caption"
        #     )
        #     ],[
        #     InlineKeyboardButton(
        #         "✅ Custom shortner" if userxdb['shortener_url'] and userxdb['shortener_api'] is not None else "🖼️ Custom shortner",
        #         callback_data="custom_shortner"
        #     )
        #     ],[
        #     InlineKeyboardButton('📤 Upload mode', callback_data="toggle_mode"),
        #     InlineKeyboardButton(mode if mode else "Links", callback_data="toggle_mode")
        #     ],[
        #     InlineKeyboardButton('🛠️ Reset settings', callback_data="reset_setting"),
        #     ], [
        #     InlineKeyboardButton('Close ✗', callback_data="close")
        #     ]]

        #
        buttons = []
        buttons.append([InlineKeyboardButton(
            "✅ Custom Caption" if userxdb['caption'] != tamilxd.STREAM_MSG_TXT else "📝 Custom Caption",
            callback_data="custom_caption"
        )])
        buttons.append([InlineKeyboardButton(
            "✅ Custom Shortner" if userxdb['shortener_url'] and userxdb[
                'shortener_api'] is not None else "🖼️ Custom Shortner",
            callback_data="custom_shortner"
        )])

        # Add linkmode button
        linkmode_status = userxdb.get("linkmode", False)
        buttons.append([InlineKeyboardButton(
            "✅ Link Mode" if linkmode_status else "❌ Link Mode",
            callback_data="toggle_linkmode"
        )])
        # Add page mode button (verify settings are now inside page mode)
        page_mode_status = userxdb.get("page_mode", False)
        buttons.append([InlineKeyboardButton(
            "✅ Page Mode" if page_mode_status else "❌ Page Mode",
            callback_data="toggle_pagemode"
        )])
        buttons.append([InlineKeyboardButton('📤 Upload Mode', callback_data="toggle_mode"),
                        InlineKeyboardButton(mode if mode else "Links", callback_data="toggle_mode")])
        if await u_db.is_settings(user_id):
            buttons.append([InlineKeyboardButton('🛠️ Reset Settings', callback_data="reset_setting")])
        buttons.append([InlineKeyboardButton('Close', callback_data="close")])
        await query.message.edit_text(
            text=tamilxd.SETTINGS_TXT.format(CAPTION="✅ Exists" if userxdb["caption"] is not None else "❌ Not Exists",
                                             URLX=userxdb["shortener_url"] if userxdb["shortener_url"] is not None else "❌ Not Exists",
                                             APIX=userxdb["shortener_api"] if userxdb["shortener_api"] is not None else "❌ Not Exists",
                                             STORAGEX=userxdb["storage"],
                                             METHODX=userxdb["method"],
                                             LINKMODE="✅ Enabled" if userxdb.get("linkmode", False) else "❌ Disabled",
                                             PAGEMODE="✅ Enabled" if userxdb.get("page_mode", False) else "❌ Disabled",
                                             VERIFYMODE="✅ Enabled" if userxdb.get("verify_mode", False) else "❌ Disabled"),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)

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
        buttons.append([InlineKeyboardButton("❌ Page Mode", callback_data="toggle_pagemode")])
        buttons.append([InlineKeyboardButton('📤 Upload mode', callback_data="toggle_mode"),
                        InlineKeyboardButton("Links", callback_data="toggle_mode")])
        buttons.append([InlineKeyboardButton('Close', callback_data="close")])
        await query.message.edit_text(
            text=tamilxd.SETTINGS_TXT.format(CAPTION="❌ Not Exists",
                                             URLX="❌ Not Exists",
                                             APIX="❌ Not Exists",
                                             STORAGEX="Off",
                                             METHODX="Links",
                                             LINKMODE="❌ Disabled",
                                             PAGEMODE="❌ Disabled",
                                             VERIFYMODE="❌ Disabled"),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)

    elif data == "custom_caption":
        await query.message.edit_text(
            text=tamilxd.CUSTOM_CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Caption Guide", callback_data="caption_help_1")],
                [
                    InlineKeyboardButton("➕ Add Caption", callback_data="add_caption"),
                    InlineKeyboardButton("👁 View Current", callback_data="show_caption")
                ],
                [
                    InlineKeyboardButton("🗑 Delete Caption", callback_data="delete_caption"),
                    InlineKeyboardButton("📝 Examples", callback_data="show_examples")
                ],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "caption_help_1":
        await query.message.edit_text(
            text=tamilxd.CAPTION_HELP_1,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Next Page ➡️", callback_data="caption_help_2")],
                [InlineKeyboardButton("≺≺ Back", callback_data="custom_caption"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "caption_help_2":
        await query.message.edit_text(
            text=tamilxd.CAPTION_HELP_2,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⬅️ Previous", callback_data="caption_help_1"),
                    InlineKeyboardButton("Next ➡️", callback_data="caption_help_3")
                ],
                [InlineKeyboardButton("≺≺ Back", callback_data="custom_caption"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "caption_help_3":
        await query.message.edit_text(
            text=tamilxd.CAPTION_HELP_3,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Previous Page", callback_data="caption_help_2")],
                [
                    InlineKeyboardButton("➕ Add Caption", callback_data="add_caption"),
                    InlineKeyboardButton("📝 Test Template", callback_data="show_examples")
                ],
                [InlineKeyboardButton("≺≺ Back", callback_data="custom_caption"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "custom_shortner":
        await query.message.edit_text(
            text=tamilxd.CUSTOM_SHORTNER_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 How to Setup", callback_data="shortener_setup_help")],
                [
                    InlineKeyboardButton("🔗 Add URL", callback_data="add_shortner"),
                    InlineKeyboardButton("🔑 Add API", callback_data="add_api")
                ],
                [
                    InlineKeyboardButton("👁 View Current", callback_data="show_shortner"),
                    InlineKeyboardButton("🗑 Delete", callback_data="delete_shortner")
                ],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "shortener_setup_help":
        await query.message.edit_text(
            text=tamilxd.COMMENTS_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔗 Add URL", callback_data="add_shortner"),
                    InlineKeyboardButton("🔑 Add API", callback_data="add_api")
                ],
                [InlineKeyboardButton("≺≺ Back", callback_data="custom_shortner"), InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

    elif data == "add_api":
        # Handle API setup (redirect to existing add_shortner logic but for API)
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text="<b>🔑 ADD API KEY</b>\n\n"
                 "<b>📋 Instructions:</b>\n"
                 "• Get API from your shortener dashboard\n"
                 "• Send the complete API key\n"
                 "• Keep it secure and private\n\n"
                 "<b>Example:</b> <code>abc123xyz789def456</code>\n\n"
                 "Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data="custom_shortner")]])
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if api_msg.text == "/cancel":
                await api_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]])
                )
            
            await u_db.set_shortner_api(query.from_user.id, api_msg.text.strip())
            await api_msg.delete()
            
            await tamil.edit_text(
                f"<b>✅ API KEY ADDED</b>\n\n"
                f"<b>🔑 API:</b> <code>{api_msg.text.strip()[:20]}...</code>\n\n"
                f"Now add your shortener URL with buttons below!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('🔗 Add URL', callback_data="add_shortner")],
                    [InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]])
            )

    elif data == "add_caption":
        await query.message.delete()
        try:
            instruction_text = """<b>📝 Send your custom caption</b>

<b>🔗 How to add clickable links:</b>
<code>[Link Text](https://example.com)</code>

<b>📋 Available Variables:</b>
• <code>{file_name}</code> - File name
• <code>{file_size}</code> - File size  
• <code>{download_link}</code> - Download link
• <code>{stream_link}</code> - Stream link
• <code>{quality}</code> - Video quality
• <code>{season}</code> - Season number
• <code>{episode}</code> - Episode number

<b>💡 Link Examples:</b>
• <code>[How to Open](https://t.me/shotner_solution/6)</code>
• <code>[Join Channel](https://t.me/your_channel)</code>
• <code>[Website](https://example.com)</code>

<code>/cancel</code> - Cancel this process"""

            tamil = await bot.send_message(query.message.chat.id, instruction_text)
            caption = await bot.listen(chat_id=user_id, timeout=300)
            if caption.text == "/cancel":
                await caption.delete()
                return await tamil.edit_text("<b>Your process is canceled!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]]))
            
            # Validate link formatting
            is_valid, errors = validate_links_in_text(caption.text)
            
            if not is_valid:
                await caption.delete()
                error_text = "<b>❌ Link formatting errors found:</b>\n\n" + "\n".join(f"• {error}" for error in errors)
                error_text += "\n\n<b>💡 Correct format:</b> <code>[Text](URL)</code>"
                return await tamil.edit_text(error_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]]))
            
            # Test placeholder formatting
            try:
                caption.text.format(file_name='', file_size='', caption='', download_link='', stream_link='', storage_link='', web_link='', quality='', season='', episode='')
            except KeyError as e:
                await caption.delete()
                return await tamil.edit_text(f"<b><u>Wrong placeholder:</u> <code>{e}</code></b>\n\nUsed in your caption. Please check the available placeholders above.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]]))
            
            # Format links properly for HTML parsing
            formatted_caption = format_links_in_text(caption.text, "HTML")
            
            await u_db.set_caption(user_id, formatted_caption)
            await caption.delete()
            
            # Show preview with working links
            preview_text = f"<b>✅ Successfully added your custom caption!</b>\n\n<b>📝 Preview:</b>\n{formatted_caption[:300]}{'...' if len(formatted_caption) > 300 else ''}"
            await tamil.edit_text(preview_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]]), disable_web_page_preview=True)
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text('Process has been automatically cancelled.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]]))

    elif data == "add_shortner":
        await query.message.delete()
        try:
            tamil = await bot.send_message(query.message.chat.id, "<b>Please provide your custom shortener URL\nEg: <code>dalink.in</code>\n/cancel - <code>Cancel this process</code></b>")
            url_input = await bot.listen(chat_id=user_id, timeout=300)
            if url_input.text == "/cancel":
                await url_input.delete()
                return await tamil.edit_text("<b>Your process is canceled!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]]))
            elif not domain(url_input.text):
                await url_input.delete()
                return await tamil.edit_text("<b>Invalid domain format. please provide a valid domain.</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]]))
            try:
                # await u_db.set_shortner_url(user_id, url_input.text)
                await url_input.delete()
                await tamil.delete()
                tamil1 = await bot.send_message(query.message.chat.id, f"<b> https://{url_input.text}/member/tools/quick \n\nPlease provide your custom shortener API \n Eg: <code>88f4e0fc522facab5fef40d69f4114c260facc9b</code></b>")
                api = await bot.listen(chat_id=user_id)
                try:
                    shortzy = Shortzy(api_key=api.text, base_site=url_input.text)
                    link = Telegram.MAIN
                    await shortzy.convert(link)
                except Exception as e:
                    return await tamil1.edit_text(f"Your shortener API or URL is invalid, please check again! {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]]))
                await u_db.set_shortner_url(user_id, url_input.text)
                await u_db.set_shortner_api(user_id, api.text)
                await api.delete()
                await tamil1.edit_text("<b>Successfully added your custon shortener!...</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]]))
            except Exception as e:
                print(f"Error fetching user: {e}")
            return
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text('Process has been automatically cancelled.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_shortner")]]))

    elif data =="show_caption":
        if len(userxdb['caption']) > 170:
            await query.message.edit_text(
                text=userxdb['caption'],
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="custom_caption")]])
            )
        else:
            await safe_answer_callback(query, f"Your custom caption:\n\n{userxdb['caption']}", show_alert=True)

    elif data == "delete_caption":
        if not userxdb['caption']:
            return await query.answer("Nothing will found to delete.", show_alert=True)
        await u_db.set_caption(query.from_user.id, tamilxd.STREAM_TXT)
        return await query.answer("Caption removed suppessfully!", show_alert=True)

    elif data == "delete_shortner":
        if not userxdb['shortener_url'] or not userxdb['shortener_api']:
            return await query.answer("Nothing will found to delete.", show_alert=True)
        await u_db.set_shortner_url(query.from_user.id, None)
        await u_db.set_shortner_api(query.from_user.id, None)
        return await query.answer("Shortner removed suppessfully!", show_alert=True)



    elif data == "show_examples":
        example_text = """<b><u>📝 CAPTION EXAMPLES WITH SMART AUTO EXTRACTION</u></b>

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

<b>🧠 Smart Extraction Features:</b>
• Checks both filename AND original caption
• Uses best available information from both sources
• Falls back gracefully when data is missing
• Automatically combines results for maximum accuracy

<b>💡 Note:</b> These placeholders will be automatically replaced with the best extracted information from your files!"""
        
        await query.message.edit_text(
            example_text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Configure Auto Extract", callback_data="toggle_extract"),
                InlineKeyboardButton("Close", callback_data="close")
            ]])
        )

    elif data =="show_shortner":
        if not userxdb['shortener_url'] and userxdb['shortener_api']:
            return await query.answer("Your didn't added any custom shortner URL", show_alert=True)
        await safe_answer_callback(query, f"Your custom shortner: \n\nURL - {userxdb['shortener_url']} \nAPI - {userxdb['shortener_api']}", show_alert=True)

    elif data == "custom_linkmode":
        user_id = query.from_user.id
        linkmode_status = await u_db.get_linkmode(user_id)
        
        await query.message.edit_text(
            text="<b>🔗 LINKMODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if linkmode_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Linkmode?</b>\n"
                 f"• Collect multiple files before generating links\n"
                 f"• Use custom captions with advanced placeholders\n"
                 f"• Default caption provided if no custom caption is set\n"
                 f"• Support for multiple shortener services\n"
                 f"• Batch processing with /complete command\n\n"
                 f"<b>🎯 Commands:</b>\n"
                 f"• <code>/linkmode on/off</code> - Enable/disable linkmode\n"
                 f"• <code>/setlinkmodecaption</code> - Set custom captions\n"
                 f"• <code>/shortlink1</code>, <code>/shortlink2</code>, <code>/shortlink3</code> - Set shorteners\n"
                 f"• <code>/complete</code> - Process collected files\n"
                 f"• <code>/pending</code> - View pending files\n"
                 f"• <code>/clear</code> - Clear pending files",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if linkmode_status else '✅ Enable'} Linkmode", callback_data="toggle_linkmode")],
                [InlineKeyboardButton("🎨 Linkmode Captions", callback_data="linkmode_captions_menu")],
                [InlineKeyboardButton("🔗 Shortlinks", callback_data="linkmode_shortlinks_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    # Linkmode callback handlers
    elif data == "toggle_linkmode":
        user_id = query.from_user.id
        linkmode_status = await u_db.get_linkmode(user_id)
        new_status = not linkmode_status
        await u_db.set_linkmode(user_id, new_status)
        
        if not new_status:
            # If disabling linkmode, clear pending files
            await u_db.clear_pending_files(user_id)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Link mode has been {status_text}!", show_alert=True)
        
        # Refresh the settings menu
        await query.message.edit_text(
            text="<b>🔗 LINKMODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Linkmode?</b>\n"
                 f"• Collect multiple files before generating links\n"
                 f"• Use custom captions with advanced placeholders\n"
                 f"• Default caption provided if no custom caption is set\n"
                 f"• Support for multiple shortener services\n"
                 f"• Batch processing with /complete command\n\n"
                 f"<b>🎯 Commands:</b>\n"
                 f"• <code>/linkmode on/off</code> - Enable/disable linkmode\n"
                 f"• <code>/setlinkmodecaption</code> - Set custom captions\n"
                 f"• <code>/shortlink1</code>, <code>/shortlink2</code>, <code>/shortlink3</code> - Set shorteners\n"
                 f"• <code>/complete</code> - Process collected files\n"
                 f"• <code>/pending</code> - View pending files\n"
                 f"• <code>/clear</code> - Clear pending files",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Linkmode", callback_data="toggle_linkmode")],
                [InlineKeyboardButton("🎨 Linkmode Captions", callback_data="linkmode_captions_menu")],
                [InlineKeyboardButton("🔗 Shortlinks", callback_data="linkmode_shortlinks_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "linkmode_captions_menu":
        user_id = query.from_user.id
        # Get current captions
        caption1 = await u_db.get_linkmode_caption(user_id, 1)
        caption2 = await u_db.get_linkmode_caption(user_id, 2)
        caption3 = await u_db.get_linkmode_caption(user_id, 3)
        active_caption = await u_db.get_active_linkmode_caption(user_id)
        
        text = "<b>🎨 LINKMODE CAPTION SETTINGS</b>\n\n"
        text += f"<b>Caption 1:</b> {'✅ Set' if caption1 else '❌ Not set'}\n"
        text += f"<b>Caption 2:</b> {'✅ Set' if caption2 else '❌ Not set'}\n"
        text += f"<b>Caption 3:</b> {'✅ Set' if caption3 else '❌ Not set'}\n\n"
        text += f"<b>Active Caption:</b> {active_caption or '🔄 Default (built-in)'}\n\n"
        text += "<b>💡 Note:</b> If no caption is set, the bot will use a default template.\n\n"
        text += "<b>📋 Available Placeholders:</b>\n"
        text += "• <code>{filenamefirst}</code> - First file name\n"
        text += "• <code>{filenamelast}</code> - Last file name\n"
        text += "• <code>{filecaptionfirst}</code> - First file caption\n"
        text += "• <code>{filecaptionlast}</code> - Last file caption\n"
        text += "• <code>{stream_link_1}</code>, <code>{stream_link_2}</code>, <code>{stream_link_3}</code>\n"
        text += "• <code>{download_link_1}</code>, <code>{download_link_2}</code>, <code>{download_link_3}</code>\n"
        text += "• <code>{storage_link_1}</code>, <code>{storage_link_2}</code>, <code>{storage_link_3}</code>\n"
        text += "• <code>{web_link}</code> - Shortlink web page (if page mode enabled)\n"
        text += "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>"
        
        buttons = []
        buttons.append([InlineKeyboardButton(f"📝 Caption 1 {'✅' if caption1 else '❌'}", callback_data="linkmode_caption_1")])
        buttons.append([InlineKeyboardButton(f"📝 Caption 2 {'✅' if caption2 else '❌'}", callback_data="linkmode_caption_2")])
        buttons.append([InlineKeyboardButton(f"📝 Caption 3 {'✅' if caption3 else '❌'}", callback_data="linkmode_caption_3")])
        
        buttons.append([InlineKeyboardButton("👁️ View Default Caption", callback_data="view_default_linkmode_caption")])
        
        if caption1 or caption2 or caption3:
            buttons.append([InlineKeyboardButton(f"🎯 Active: Caption {active_caption or 'None'}", callback_data="select_active_caption")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="linkmode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "linkmode_shortlinks_menu":
        user_id = query.from_user.id
        shortlinks = await u_db.get_all_shortlinks(user_id)
        
        text = "<b>🔗 LINKMODE SHORTLINKS</b>\n\n"
        
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
        text += "• <code>/list_shortlinks</code> - View all shortlinks"
        
        buttons = []
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="linkmode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("linkmode_caption_"):
        caption_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        # Get current caption
        current_caption = await u_db.get_linkmode_caption(user_id, caption_num)
        
        buttons = []
        if current_caption:
            buttons.append([InlineKeyboardButton("👁️ View Caption", callback_data=f"view_linkmode_caption_{caption_num}")])
            buttons.append([InlineKeyboardButton("✏️ Edit Caption", callback_data=f"edit_linkmode_caption_{caption_num}")])
            buttons.append([InlineKeyboardButton("🗑️ Delete Caption", callback_data=f"delete_linkmode_caption_{caption_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Add Caption", callback_data=f"add_linkmode_caption_{caption_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="linkmode_captions_menu")])
        
        await query.message.edit_text(
            f"<b>📝 LINKMODE CAPTION {caption_num}</b>\n\n"
            f"<b>Status:</b> {'✅ Set' if current_caption else '❌ Not set'}\n\n"
            f"Choose an action:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("view_linkmode_caption_"):
        caption_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        caption = await u_db.get_linkmode_caption(user_id, caption_num)
        
        if caption:
            if len(caption) > 1000:
                await query.message.edit_text(
                    f"<b>📝 LINKMODE CAPTION {caption_num}</b>\n\n{caption}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("≺≺ Back", callback_data=f"linkmode_caption_{caption_num}")]])
                )
            else:
                await safe_answer_callback(query, f"Linkmode Caption {caption_num}:\n\n{caption}", show_alert=True)
        else:
            await query.answer("Caption not found!", show_alert=True)

    elif data.startswith("add_linkmode_caption_") or data.startswith("edit_linkmode_caption_"):
        caption_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        await query.message.delete()
        try:
            instruction_text = f"""<b>📝 LINKMODE CAPTION {caption_num}</b>

Send your custom linkmode caption.

<b>🔗 How to add clickable links:</b>
<code>[Link Text](https://example.com)</code>

<b>📋 Available Placeholders:</b>
• <code>{{filenamefirst}}</code> - First file name
• <code>{{filenamelast}}</code> - Last file name
• <code>{{filecaptionfirst}}</code> - First file caption
• <code>{{filecaptionlast}}</code> - Last file caption
• <code>{{stream_link_1}}</code>, <code>{{stream_link_2}}</code>, <code>{{stream_link_3}}</code>
• <code>{{download_link_1}}</code>, <code>{{download_link_2}}</code>, <code>{{download_link_3}}</code>
• <code>{{storage_link_1}}</code>, <code>{{storage_link_2}}</code>, <code>{{storage_link_3}}</code>
• <code>{{file_size}}</code>, <code>{{quality}}</code>, <code>{{season}}</code>, <code>{{episode}}</code>

<b>💡 Link Examples:</b>
• <code>[How to Open](https://t.me/shotner_solution/6)</code>
• <code>[Join Channel](https://t.me/your_channel)</code>
• <code>[Website](https://example.com)</code>

<code>/cancel</code> - Cancel this process"""

            tamil = await bot.send_message(query.message.chat.id, instruction_text)
            caption = await bot.listen(chat_id=user_id, timeout=300)
            
            if caption.text == "/cancel":
                await caption.delete()
                return await tamil.edit_text(
                    "<b>Process cancelled!</b>", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"linkmode_caption_{caption_num}")]])
                )
            
            # Validate link formatting
            is_valid, errors = validate_links_in_text(caption.text)
            
            if not is_valid:
                await caption.delete()
                error_text = "<b>❌ Link formatting errors found:</b>\n\n" + "\n".join(f"• {error}" for error in errors)
                error_text += "\n\n<b>💡 Correct format:</b> <code>[Text](URL)</code>"
                return await tamil.edit_text(error_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"linkmode_caption_{caption_num}")]])) 
            
            # Format links properly for HTML parsing
            formatted_caption = format_links_in_text(caption.text, "HTML")
            
            # Save the caption
            await u_db.set_linkmode_caption(user_id, caption_num, formatted_caption)
            await caption.delete()
            
            # Show preview with working links
            preview_text = f"<b>✅ Successfully saved linkmode caption {caption_num}!</b>\n\n<b>📝 Preview:</b>\n{formatted_caption[:300]}{'...' if len(formatted_caption) > 300 else ''}"
            await tamil.edit_text(
                preview_text,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"linkmode_caption_{caption_num}")]]),
                disable_web_page_preview=True
            )
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text(
                'Process has been automatically cancelled.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"linkmode_caption_{caption_num}")]])
            )

    elif data.startswith("delete_linkmode_caption_"):
        caption_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        await u_db.delete_linkmode_caption(user_id, caption_num)
        await query.answer(f"Caption {caption_num} deleted successfully!", show_alert=True)
        
        # Go back to caption menu
        await query.message.edit_text(
            f"<b>📝 LINKMODE CAPTION {caption_num}</b>\n\n"
            f"<b>Status:</b> ❌ Not set\n\n"
            f"Choose an action:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Caption", callback_data=f"add_linkmode_caption_{caption_num}")],
                [InlineKeyboardButton("≺≺ Back", callback_data="linkmode_captions_menu")]
            ])
        )

    elif data == "select_active_caption":
        user_id = query.from_user.id
        
        # Get available captions
        caption1 = await u_db.get_linkmode_caption(user_id, 1)
        caption2 = await u_db.get_linkmode_caption(user_id, 2)
        caption3 = await u_db.get_linkmode_caption(user_id, 3)
        active_caption = await u_db.get_active_linkmode_caption(user_id)
        
        buttons = []
        if caption1:
            buttons.append([InlineKeyboardButton(f"📝 Caption 1 {'✅' if active_caption == 1 else ''}", callback_data="set_active_caption_1")])
        if caption2:
            buttons.append([InlineKeyboardButton(f"📝 Caption 2 {'✅' if active_caption == 2 else ''}", callback_data="set_active_caption_2")])
        if caption3:
            buttons.append([InlineKeyboardButton(f"📝 Caption 3 {'✅' if active_caption == 3 else ''}", callback_data="set_active_caption_3")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="linkmode_captions_menu")])
        
        await query.message.edit_text(
            f"<b>🎯 SELECT ACTIVE CAPTION</b>\n\n"
            f"<b>Current Active:</b> {'Caption ' + str(active_caption) if active_caption else 'None'}\n\n"
            f"Choose which caption to use for linkmode:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("set_active_caption_"):
        caption_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        await u_db.set_active_linkmode_caption(user_id, caption_num)
        await query.answer(f"Caption {caption_num} set as active!", show_alert=True)
        
        # Go back to captions menu
        await query.message.edit_text(
            "<b>✅ Active caption updated!</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("≺≺ Back", callback_data="linkmode_captions_menu")]])
        )

    elif data == "main":
        await query.message.edit_text(
            "<b>Change your settings as your wish.</b>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('Personal settings', callback_data='settings'),
                ],[
                InlineKeyboardButton('Channels settings', callback_data='channels')
                ],[
                InlineKeyboardButton('≺≺ Close', callback_data='close')
                ]]))

    elif data == "channels":
        buttons = []
        channels = await u_db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add channel ✚',
                      callback_data="addchannel")])
        buttons.append([InlineKeyboardButton('≺≺ Back',
                      callback_data="main")])
        await query.message.edit_text(
            "<b><u>My channels</b></u>\n\n<b>You can manage your target chats in here.</b>",
        reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "addchannel":
        await query.message.delete()
        try:
            tamil = await bot.send_message(chat_id=query.message.chat.id, text=tamilxd.CHL_CHANNEL_ADD_TXT)
            chat_ids = await bot.listen(chat_id=user_id, timeout=60)
            if chat_ids.text=="/cancel":
                await chat_ids.delete()
                return await tamil.edit_text("<b>Your process has been canceled.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))
            if not chat_ids.forward_date:
                await chat_ids.delete()
                return await tamil.edit_text("<b>This is not a forward message.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))
            chat_id = chat_ids.forward_from_chat.id
            if (await bot.get_chat(chat_id)).type != enums.ChatType.CHANNEL:
                await chat_ids.delete()
                return await tamil.edit_text("This is not a channel message.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))
            title = chat_ids.forward_from_chat.title

            if not await is_check_admin(bot, chat_id, query.from_user.id):
                await chat_ids.delete()
                return await tamil.edit_text('You not admin in that channel.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))
            else:
                username = chat_ids.forward_from_chat.username
                username = "@" + username if username else "private"
                chat = await u_db.add_channel(int(user_id), int(chat_id), title, username)
                await chat_ids.delete()
                await tamil.edit_text("<b>Successfully Updated.</b>" if chat else "<b>This channel already added!...</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text('Process has been automatically cancelled.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))

    elif data.startswith(("editchannels", "chlmode")):
        chat_id = data.split('_')[1]
        channel_doc = await u_db.get_channel_detail(chat_id)
        chat = channel_doc.get("settings", u_db.default_setgs) if channel_doc else u_db.default_setgs
        mode = chat['method']
        if data.startswith("chlmode"):
            if not mode:
                mode = "Button"
            elif mode == "Button":
                mode = "Caption"
            else:
                mode = "Button"
            await u_db.update_chl_settings(chat_id, 'method', mode)
        buttons = []
        buttons.append([InlineKeyboardButton(
            "✅  Custon Caption" if chat['caption'] != tamilxd.STREAM_TXT else "📝 Custon Caption",
            callback_data=f"chlcustomcaption_{chat_id}")])
        buttons.append([InlineKeyboardButton(
            "✅  Custon  Shortener" if chat['url'] and chat['api'] is not None else "🖼️ Custon  Shortener",
            callback_data=f"chlcustomshortner_{chat_id}")])
        buttons.append([InlineKeyboardButton('📤 Uploed Mode', callback_data=f"chlmode_{chat_id}"),
                        InlineKeyboardButton(mode if mode else "Button", callback_data=f"chlmode_{chat_id}")])
        
        # Page Mode settings - always show as navigation button
        buttons.append([InlineKeyboardButton('📄 Page Mode', callback_data=f"chl_pagemode_settings_{chat_id}")])
        
        if await u_db.is_chl_settings(chat_id):
            buttons.append([InlineKeyboardButton('Delete', callback_data=f"removechannelx_{chat_id}"),
                            InlineKeyboardButton('Reset', callback_data=f"resetchatsetting_{chat_id}")])
        else:
            buttons.append([InlineKeyboardButton('Delete', callback_data=f"removechannelx_{chat_id}")])
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data="channels")])
        #
        await query.message.edit_text(text=tamilxd.CHL_CHANNEL_DETAILS_TXT.format(TITLEX=channel_doc.get("title", "Unknown") if channel_doc else "Unknown",
                                                                                CHANNEL_DIX=chat_id,
                                                                                USERNAMEX=channel_doc.get("username", "private") if channel_doc else "private",
                                                                                CAPTION="✅ Exists" if chat["caption"] is not None else "❌ Not Exists",
                                                                                APIX=chat["api"] if chat["api"] is not None else "❌ Not Exists",
                                                                                URLX=chat["url"] if chat["url"] is not None else "❌ Not Exists",
                                                                                METHODX=chat["method"]),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)

    elif data.startswith("removechannelx"):
        chat_id = data.split('_')[1]
        chat = await u_db.get_channel_details(user_id, chat_id)
        await query.message.edit_text(
            f"<b>Do you confirm ??\n\n You delete your : {chat['title']} channel?</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Confirm ✅', callback_data=f"xremovechannel_{chat_id}")],[InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")]]))

    elif data.startswith("xremovechannel"):
        chat_id = data.split('_')[1]
        await u_db.remove_channel(user_id, chat_id)
        await query.answer("Successfully deleted your channel.", show_alert=True)
        buttons = []
        channels = await u_db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add channel ✚',
                      callback_data="addchannel")])
        buttons.append([InlineKeyboardButton('≺≺ Back',
                      callback_data="main")])
        await query.message.edit_text(
            "<b><u>My channels</b></u>\n\n<b>You can manage your chats in here.</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
        #

    elif data.startswith("resetchatsetting"):
        chat_id = data.split('_')[1]
        await query.message.edit_text(
            text=tamilxd.RESET_SETTINGS,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton('Yes', callback_data=f"xresetchatsettings_{chat_id}"),
                    InlineKeyboardButton('No', callback_data=f"editchannels_{chat_id}")
                ]]
            )
        ) 

    elif data.startswith("xresetchatsettings"):
        chat_id = data.split('_')[1]
        await u_db.reset_chl_settings(chat_id)
        await query.answer("Successfully resetted your channel settings.", show_alert=True)
        #
        chat = await u_db.get_chl_settings(chat_id)
        chatx = await bot.get_chat(chat_id)
        #
        return await query.message.edit_text(
            text=tamilxd.CHL_CHANNEL_DETAILS_TXT.format(
                TITLEX=chatx.title,
                CHANNEL_DIX=chat_id,
                USERNAMEX="@" + chatx.username if chatx.username else "private",
                CAPTION="❌ Not Exists",
                APIX="❌ Not Exists",
                URLX="❌ Not Exists",
                METHODX=chat["method"],
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Custon caption", callback_data=f"chlcustomcaption_{chat_id}")
                ],[InlineKeyboardButton("Custon  Shortener", callback_data=f"chlcustomshortner_{chat_id}")
                ],[InlineKeyboardButton("📤 Uploed Mode", callback_data=f"chlmode_{chat_id}"),
                   InlineKeyboardButton("Button", callback_data=f"chlmode_{chat_id}")
                ],[InlineKeyboardButton("Delete", callback_data=f"removechannelx_{chat_id}")
                ],[InlineKeyboardButton("≺≺ Back", callback_data="channels")]]
            ),
            disable_web_page_preview=True,
        )
        #

    elif data.startswith("chlcustomcaption"):
        chat_id = data.split('_')[1]
        chat = await u_db.get_chl_settings(chat_id)
        await query.message.edit_text(
            text=tamilxd.CHL_CUSTOM_CAPTION_TXT.format(CAPTIONX=chat['caption']),
            disable_web_page_preview = True,
            reply_markup=InlineKeyboardMarkup(
                [[
                InlineKeyboardButton("Show Caption", callback_data=f"chlshowcaption_{chat_id}")
                ],[
                InlineKeyboardButton('Default Caption', callback_data=f"chldelcaption_{chat_id}"),
                InlineKeyboardButton("Change Caption", callback_data=f"chladdcaption_{chat_id}")
                ],[
                InlineKeyboardButton('Close', callback_data="close"),
                InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")
                ]]
            ))

    elif data.startswith("chlcustomshortner"):
        buttons = []
        chat_id = data.split('_')[1]
        chat = await u_db.get_chl_settings(chat_id)
        if chat['api'] and chat['url'] is not None:
            buttons.append([InlineKeyboardButton('Change shortener', callback_data=f"chladdshortner_{chat_id}"),
                            InlineKeyboardButton('Delete shortener', callback_data=f"chldelshortner_{chat_id}")])
        else:
            buttons.append([InlineKeyboardButton('Set shortener', callback_data=f"chladdshortner_{chat_id}")])
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}"),
                        InlineKeyboardButton('Close', callback_data="close")])
        await query.message.edit_text(
            text=tamilxd.CHL_SHORTNER_TXT.format(
                URLX=chat["url"] if chat["url"] is not None else "❌ Not Exists",
                APIX=chat["api"] if chat["api"] is not None else "❌ Not Exists",
            ),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    elif data.startswith("chladdcaption"):
        chat_id = data.split('_')[1]
        await query.message.delete()
        try:
            instruction_text = f"""<b>📝 Send your custom caption for this channel</b>

<b>🔗 How to add clickable links:</b>
<code>[Link Text](https://example.com)</code>

<b>📋 Available Variables:</b>
• <code>{{file_name}}</code> - File name
• <code>{{file_size}}</code> - File size  
• <code>{{download_link}}</code> - Download link
• <code>{{stream_link}}</code> - Stream link
• <code>{{storage_link}}</code> - Storage link
• <code>{{quality}}</code> - Video quality
• <code>{{season}}</code> - Season number
• <code>{{episode}}</code> - Episode number

<b>💡 Link Examples:</b>
• <code>[How to Open](https://t.me/shotner_solution/6)</code>
• <code>[Join Channel](https://t.me/your_channel)</code>
• <code>[Website](https://example.com)</code>

<b>Channel ID:</b> <code>{chat_id}</code>
<code>/cancel</code> - Cancel this process"""

            tamil = await bot.send_message(query.message.chat.id, instruction_text)
            caption = await bot.listen(chat_id=user_id, timeout=120)
            if caption.text == "/cancel":
                await caption.delete()
                return await tamil.edit_text("<b>Your process is canceled!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomcaption_{chat_id}")]]))
            
            # Validate link formatting
            is_valid, errors = validate_links_in_text(caption.text)
            
            if not is_valid:
                await caption.delete()
                error_text = "<b>❌ Link formatting errors found:</b>\n\n" + "\n".join(f"• {error}" for error in errors)
                error_text += "\n\n<b>💡 Correct format:</b> <code>[Text](URL)</code>"
                return await tamil.edit_text(error_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomcaption_{chat_id}")]]))
            
            # Test placeholder formatting
            try:
                caption.text.format(file_name='', file_size='', caption='', download_link='', fast_link='', stream_link='', storage_link='', web_link='', quality='', season='', episode='')
            except KeyError as e:
                await caption.delete()
                return await tamil.edit_text(
                    f"<b><u>Wrong placeholder:</u> <code>{e}</code></b>\n\nUsed in your caption. Please check the available placeholders above.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomcaption_{chat_id}")]]))
            
            # Format links properly for HTML parsing
            formatted_caption = format_links_in_text(caption.text, "HTML")
            
            await u_db.update_chl_settings(chat_id, 'caption', formatted_caption)
            await caption.delete()
            
            # Show preview with working links
            preview_text = f"<b>✅ Successfully added your custom caption!</b>\n\n<b>📝 Preview:</b>\n{formatted_caption[:300]}{'...' if len(formatted_caption) > 300 else ''}"
            await tamil.edit_text(preview_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomcaption_{chat_id}")]]), disable_web_page_preview=True)
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text('Process has been automatically cancelled.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))

    elif data.startswith("chladdshortner"):
        await query.message.delete()
        chat_id = data.split('_')[1]
        chl = await bot.get_chat(int(chat_id))
        try:
            tamil1 = await bot.send_message(query.message.chat.id, "<b>Please provide your custom shortener URL\nEg: <code>dalink.in</code>\n/cancel - <code>Cancel this process</code></b>")
            url_input = await bot.listen(chat_id=user_id, timeout=300)
            if url_input.text == "/cancel":
                await url_input.delete()
                return await tamil1.edit_text("<b>Your process is canceled!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomshortner_{chat_id}")]]))
            elif not domain(url_input.text):
                await url_input.delete()
                return await tamil1.edit_text("<b>Invalid domain format. please provide a valid domain.</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomshortner_{chat_id}")]]))
            try:
                await url_input.delete()
                await tamil1.delete()
                tamil2 = await bot.send_message(query.message.chat.id, f"<b> https://{url_input.text}/member/tools/quick \n\nPlease provide your custom shortener API\n Eg: <code>88f4e0fc522facab5fef40d69f4114c260facc9b</code></b>")
                api_input = await bot.listen(chat_id=user_id)
                try:
                    shortzy = Shortzy(api_key=api_input.text, base_site=url_input.text)
                    link = Telegram.MAIN
                    await shortzy.convert(link)
                except Exception as e:
                    return await tamil2.edit_text(f"Your shortener API or URL is invalid, please chack again! {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomshortner_{chat_id}")]]))
                await u_db.update_chl_settings(chat_id, 'url', url_input.text)
                await u_db.update_chl_settings(chat_id, 'api', api_input.text)
                await api_input.delete()
                await tamil2.edit_text(f"<b>Successfully changed shortener for {chl.title} - {chl.id} to\n\nURL - {url_input.text}\nAPI - {api_input.text}</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomshortner_{chat_id}")]]))
            except Exception as e:
                print(f"Error fetching user: {e}")
            return
        except asyncio.exceptions.TimeoutError:
            await tamil1.edit_text('Process has been automatically cancelled.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="channels")]]))

    elif data.startswith("chlshowcaption"):
        chat_id = data.split('_')[1]
        settings = await u_db.get_chl_settings(chat_id)
        if len(settings['caption']) > 170:
            await query.message.edit_text(
                text=settings['caption'],
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"chlcustomcaption_{chat_id}")]])
            )
        else:
            await safe_answer_callback(query, f"Your custom caption:\n\n{settings['caption']}", show_alert=True)

    elif data.startswith("chldelcaption"):
        chat_id = data.split('_')[1]
        settings = await u_db.get_chl_settings(chat_id)
        if not settings['caption']:
            return await query.answer("Nothing will found to delete.", show_alert=True)
        await u_db.update_chl_settings(chat_id, 'caption', tamilxd.STREAM_TXT)
        return await query.answer("caption removed successfully!'", show_alert=True)

    elif data.startswith("chlshowshortner"):
        chat_id = data.split('_')[1]
        settings = await u_db.get_chl_settings(chat_id)
        if not settings['api'] and settings['url']:
            return await query.answer("You didn't added any custom shortener URL or API.", show_alert=True)
        await query.answer(f"Your custom Shortner: \n\nURL - {settings['url']} \nAPI - {settings['api']}", show_alert=True)

    elif data.startswith("chldelshortner"):
        chat_id = data.split('_')[1]
        settings = await u_db.get_chl_settings(chat_id)
        if not settings['api'] and settings['url']:
            return await query.answer("Nothing will found to delete.", show_alert=True)
        await u_db.update_chl_settings(chat_id, 'api', None)
        await u_db.update_chl_settings(chat_id, 'url', None)
        await query.answer("Shortener removed successfully!", show_alert=True)
        return await query.message.edit_text(
            text=tamilxd.CHL_SHORTNER_TXT.format(URLX="❌ Not Exists",APIX="❌ Not Exists"),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('Set shortener', callback_data=f"chladdshortner_{chat_id}")
                ],[
                InlineKeyboardButton('Close', callback_data="close"),
                InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")
                ]]))

    ######################## CHANNEL PAGE MODE HANDLERS ##########################

    elif data.startswith("chl_pagemode_settings"):
        # Show dedicated channel page mode settings menu
        chat_id = data.split('_')[3]
        channel_doc = await u_db.get_channel_detail(chat_id)
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        page_mode = chat_settings.get('page_mode', False)
        page_shortlinks = chat_settings.get('page_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        # Count configured shortlinks
        configured_count = sum(1 for i in range(1, 4) 
                             if page_shortlinks.get(f"shortlink{i}", {}).get('url'))
        
        buttons = []
        
        # Page Mode toggle
        page_mode_status = "✅ Enabled" if page_mode else "❌ Disabled" 
        buttons.append([InlineKeyboardButton(f'📄 Page Mode: {page_mode_status}', callback_data=f"chl_pagemode_toggle_{chat_id}")])
        
        # Page shortlinks management
        buttons.append([InlineKeyboardButton(f'⚙️ Manage Page Shortlinks ({configured_count}/3)', callback_data=f"chl_pagemode_shortlinks_{chat_id}")])
        
        # Verify settings (only if page mode is enabled)
        if page_mode:
            verify_mode = chat_settings.get('verify_mode', False)
            verify_status = "✅ Enabled" if verify_mode else "❌ Disabled"
            buttons.append([InlineKeyboardButton(f'🔐 Verify Mode: {verify_status}', callback_data=f"chl_pagemode_verify_{chat_id}")])
            
            if verify_mode:
                verify_shortlinks = chat_settings.get('verify_shortlinks', {})
                verify_configured = sum(1 for i in range(1, 4) 
                                      if verify_shortlinks.get(f"shortlink{i}", {}).get('url'))
                buttons.append([InlineKeyboardButton(f'🔐 Manage Verify Shortlinks ({verify_configured}/3)', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")])
                
                # Verify time settings
                verify_time_gap = chat_settings.get('verify_time_gap', 14400)
                hours = verify_time_gap // 3600
                buttons.append([InlineKeyboardButton(f'⏱️ Verify Time Gap: {hours}h', callback_data=f"chl_verify_time_{chat_id}")])
        else:
            buttons.append([InlineKeyboardButton('ℹ️ Enable Page Mode to access Verify Settings', callback_data=f"chl_pagemode_info_{chat_id}")])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")])
        
        channel_title = channel_doc.get('title', 'Unknown Channel') if channel_doc else 'Unknown Channel'
        
        await query.message.edit_text(
            f"<b>📄 CHANNEL PAGE MODE SETTINGS</b>\n\n"
            f"<b>📺 Channel:</b> {channel_title}\n"
            f"<b>🆔 ID:</b> <code>{chat_id}</code>\n\n"
            f"<b>📊 Current Status:</b>\n"
            f"• Page Mode: {page_mode_status}\n"
            f"• Page Shortlinks: {configured_count}/3 configured\n"
            + (f"• Verify Mode: {verify_status}\n" if page_mode else "") +
            "\n<b>🎯 Page Mode Features:</b>\n"
            "• Beautiful web pages for downloads\n"
            "• Custom shortlink integration\n"
            "• Mobile-responsive design\n"
            "• Download analytics\n\n"
            + ("<b>🔐 Verify Mode Features:</b>\n"
               "• Progressive verification system\n"
               "• Anti-spam protection\n"
               "• Time-based verification reset\n"
               "• Direct downloads after verification\n" if page_mode else 
               "<b>💡 Enable Page Mode to unlock verification features!</b>"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("chl_pagemode_toggle"):
        # Toggle channel page mode on/off
        chat_id = data.split('_')[3]
        chat_settings = await u_db.get_chl_settings(chat_id)
        current_page_mode = chat_settings.get('page_mode', False)
        new_page_mode = not current_page_mode
        
        # Update page mode setting
        await u_db.update_chl_settings(chat_id, 'page_mode', new_page_mode)
        
        # If disabling page mode, also disable verify mode
        if not new_page_mode:
            await u_db.update_chl_settings(chat_id, 'verify_mode', False)
        
        status = "enabled" if new_page_mode else "disabled"
        await query.answer(f"Page Mode {status} for this channel!", show_alert=True)
        
        # Refresh the page mode settings menu manually to avoid callback query issues
        channel_doc = await u_db.get_channel_detail(chat_id)
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        page_mode = chat_settings.get('page_mode', False)
        page_shortlinks = chat_settings.get('page_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        # Count configured shortlinks
        configured_count = sum(1 for i in range(1, 4) 
                             if page_shortlinks.get(f"shortlink{i}", {}).get('url'))
        
        buttons = []
        
        # Page Mode toggle
        page_mode_status = "✅ Enabled" if page_mode else "❌ Disabled" 
        buttons.append([InlineKeyboardButton(f'📄 Page Mode: {page_mode_status}', callback_data=f"chl_pagemode_toggle_{chat_id}")])
        
        # Page shortlinks management
        buttons.append([InlineKeyboardButton(f'⚙️ Manage Page Shortlinks ({configured_count}/3)', callback_data=f"chl_pagemode_shortlinks_{chat_id}")])
        
        # Verify settings (only if page mode is enabled)
        if page_mode:
            verify_mode = chat_settings.get('verify_mode', False)
            verify_status = "✅ Enabled" if verify_mode else "❌ Disabled"
            buttons.append([InlineKeyboardButton(f'🔐 Verify Mode: {verify_status}', callback_data=f"chl_pagemode_verify_{chat_id}")])
            
            if verify_mode:
                verify_shortlinks = chat_settings.get('verify_shortlinks', {})
                verify_configured = sum(1 for i in range(1, 4) 
                                      if verify_shortlinks.get(f"shortlink{i}", {}).get('url'))
                buttons.append([InlineKeyboardButton(f'🔐 Manage Verify Shortlinks ({verify_configured}/3)', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")])
                
                # Verify time settings
                verify_time_gap = chat_settings.get('verify_time_gap', 14400)
                hours = verify_time_gap // 3600
                buttons.append([InlineKeyboardButton(f'⏱️ Verify Time Gap: {hours}h', callback_data=f"chl_verify_time_{chat_id}")])
        else:
            buttons.append([InlineKeyboardButton('ℹ️ Enable Page Mode to access Verify Settings', callback_data=f"chl_pagemode_info_{chat_id}")])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")])
        
        channel_title = channel_doc.get('title', 'Unknown Channel') if channel_doc else 'Unknown Channel'
        
        await query.message.edit_text(
            f"<b>📄 CHANNEL PAGE MODE SETTINGS</b>\n\n"
            f"<b>📺 Channel:</b> {channel_title}\n"
            f"<b>🆔 ID:</b> <code>{chat_id}</code>\n\n"
            f"<b>📊 Current Status:</b>\n"
            f"• Page Mode: {page_mode_status}\n"
            f"• Page Shortlinks: {configured_count}/3 configured\n"
            + (f"• Verify Mode: {verify_status}\n" if page_mode else "") +
            "\n<b>🎯 Page Mode Features:</b>\n"
            "• Beautiful web pages for downloads\n"
            "• Custom shortlink integration\n"
            "• Mobile-responsive design\n"
            "• Download analytics\n\n"
            + ("<b>🔐 Verify Mode Features:</b>\n"
               "• Progressive verification system\n"
               "• Anti-spam protection\n"
               "• Time-based verification reset\n"
               "• Direct downloads after verification\n" if page_mode else 
               "<b>💡 Enable Page Mode to unlock verification features!</b>"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("chl_pagemode_info"):
        chat_id = data.split('_')[3]
        await query.answer(
            "ℹ️ Please enable Page Mode first to access Verify settings!\n\n"
            "Page Mode is required for the verification system to work properly.",
            show_alert=True
        )

    elif data == "chl_pagemode_commands_help":
        help_text = """<b>📚 CHANNEL PAGE MODE COMMANDS</b>

<b>🔗 Quick Setup Commands:</b>
• <code>/chlpagemode1 chat_id url api</code> - Set page shortlink 1
• <code>/chlpagemode2 chat_id url api</code> - Set page shortlink 2  
• <code>/chlpagemode3 chat_id url api</code> - Set page shortlink 3

<b>📋 Example Usage:</b>
<code>/chlpagemode1 -1001234567890 short.com abc123xyz</code>

<b>💡 Benefits:</b>
• Channel-specific shortlink configuration
• Automatic testing before saving
• Independent settings per channel
• Command-based quick setup

<b>🎯 Perfect for:</b>
• Different shortlinks per channel
• Quick bulk configuration
• Power user management
• Automated setup scripts"""

        await query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back to Interactive Setup", callback_data="chl_pagemode_shortlinks")]
            ])
        )

    elif data == "chl_verify_commands_help":
        help_text = """<b>📚 CHANNEL VERIFY COMMANDS</b>

<b>🔐 Quick Setup Commands:</b>
• <code>/chlverify1 chat_id url api</code> - Set verify shortlink 1 (Third)
• <code>/chlverify2 chat_id url api</code> - Set verify shortlink 2 (Second)  
• <code>/chlverify3 chat_id url api</code> - Set verify shortlink 3 (First)

<b>📋 Example Usage:</b>
<code>/chlverify3 -1001234567890 verify.com xyz789abc</code>

<b>🎯 Verification Order:</b>
• **Verify 3**: Users see this first
• **Verify 2**: Shows after completing first
• **Verify 1**: Final verification step

<b>💡 Benefits:</b>
• Channel-specific verification setup
• Progressive verification system
• Independent verify settings per channel
• Command-based quick configuration

<b>🔐 Perfect for:</b>
• Different verification per channel type
• Anti-spam protection per channel
• Monetization strategy per audience"""

        await query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back to Interactive Setup", callback_data="chl_pagemode_verify_shortlinks")]
            ])
        )

    elif data.startswith("chl_pagemode_verify_shortlinks"):
        # Navigate to verify shortlinks management (separate from verify settings)
        chat_id = data.split('_')[4]
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        verify_shortlinks = chat_settings.get('verify_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        buttons = []
        for i in range(1, 4):
            shortlink_key = f"shortlink{i}"
            shortlink_data = verify_shortlinks.get(shortlink_key, {"url": None, "api": None})
            
            verification_order = ["Third", "Second", "First"][i-1]  # 1=Third, 2=Second, 3=First
            
            if shortlink_data["url"] and shortlink_data["api"]:
                status = "✅"
            else:
                status = "❌"
                
            buttons.append([
                InlineKeyboardButton(f'🔐 Verify {i} ({verification_order}) {status}', callback_data=f"chl_verify_set_{i}_{chat_id}"),
                InlineKeyboardButton(f'🗑️ Remove {i}', callback_data=f"chl_verify_remove_{i}_{chat_id}")
            ])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_settings_{chat_id}")])
        
        await query.message.edit_text(
            "<b>🔐 CHANNEL VERIFY SHORTLINKS</b>\n\n"
            "<b>⚙️ Manage Verification Shortlinks</b>\n\n"
            "<b>🎯 Current Configuration:</b>\n"
            f"• Verify 3 (First): {'✅ Active' if verify_shortlinks.get('shortlink3', {}).get('url') else '❌ Not Set'}\n"
            f"• Verify 2 (Second): {'✅ Active' if verify_shortlinks.get('shortlink2', {}).get('url') else '❌ Not Set'}\n"
            f"• Verify 1 (Third): {'✅ Active' if verify_shortlinks.get('shortlink1', {}).get('url') else '❌ Not Set'}\n\n"
            "<b>🔗 Verification Order:</b>\n"
            "• Users see Verify 3 first\n"
            "• Then Verify 2 on second visit\n"
            "• Finally Verify 1 on third visit\n"
            "• After all: Direct downloads\n\n"
            "<b>💡 Info:</b> Configure shortlinks for the verification system.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )



    elif data.startswith("chl_pagemode_shortlinks"):
        chat_id = data.split('_')[3]
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        # Get page mode shortlinks
        page_shortlinks = chat_settings.get('page_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        buttons = []
        for i in range(1, 4):
            shortlink_key = f"shortlink{i}"
            shortlink_data = page_shortlinks.get(shortlink_key, {"url": None, "api": None})
            
            if shortlink_data["url"] and shortlink_data["api"]:
                status = "✅"
                action_text = "Configure"
            else:
                status = "❌"
                action_text = "Add"
                
            buttons.append([
                InlineKeyboardButton(f'🔗 Page Shortlink {i} {status}', callback_data=f"chl_pagemode_set_{i}_{chat_id}"),
                InlineKeyboardButton(f'🗑️ Remove {i}', callback_data=f"chl_pagemode_remove_{i}_{chat_id}")
            ])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_settings_{chat_id}")])
        
        await safe_edit_message(
            query,
            "<b>📄 CHANNEL PAGE MODE SHORTLINKS</b>\n\n"
            "<b>⚙️ Manage Shortlinks for Page Mode</b>\n\n"
            "<b>🎯 Current Configuration:</b>\n"
            f"• Shortlink 1: {'✅ Active' if page_shortlinks.get('shortlink1', {}).get('url') else '❌ Not Set'}\n"
            f"• Shortlink 2: {'✅ Active' if page_shortlinks.get('shortlink2', {}).get('url') else '❌ Not Set'}\n"
            f"• Shortlink 3: {'✅ Active' if page_shortlinks.get('shortlink3', {}).get('url') else '❌ Not Set'}\n\n"
            "<b>💡 Info:</b> Configure shortlinks that will be used when Page Mode is enabled for this channel.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("chl_pagemode_verify"):
        chat_id = data.split('_')[3]
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        verify_mode = chat_settings.get('verify_mode', False)
        verify_shortlinks = chat_settings.get('verify_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        buttons = []
        
        # Verify mode toggle
        verify_status = "✅ Enabled" if verify_mode else "❌ Disabled"
        buttons.append([InlineKeyboardButton(f'🔐 Verify Mode: {verify_status}', callback_data=f"chl_verify_toggle_{chat_id}")])
        
        if verify_mode:
            # Show verify shortlinks only if verify mode is enabled
            for i in range(1, 4):
                shortlink_key = f"shortlink{i}"
                shortlink_data = verify_shortlinks.get(shortlink_key, {"url": None, "api": None})
                
                verification_order = ["Third", "Second", "First"][i-1]  # 1=Third, 2=Second, 3=First
                
                if shortlink_data["url"] and shortlink_data["api"]:
                    status = "✅"
                else:
                    status = "❌"
                    
                buttons.append([
                    InlineKeyboardButton(f'🔐 Verify {i} ({verification_order}) {status}', callback_data=f"chl_verify_set_{i}_{chat_id}"),
                    InlineKeyboardButton(f'🗑️ Remove {i}', callback_data=f"chl_verify_remove_{i}_{chat_id}")
                ])
            
            # Verify time settings
            verify_time_gap = chat_settings.get('verify_time_gap', 14400)  # 4 hours default
            hours = verify_time_gap // 3600
            buttons.append([InlineKeyboardButton(f'⏱️ Verify Time Gap: {hours}h', callback_data=f"chl_verify_time_{chat_id}")])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")])
        
        await query.message.edit_text(
            "<b>🔐 CHANNEL VERIFY MODE SETTINGS</b>\n\n"
            f"<b>Status:</b> {verify_status}\n\n"
            "<b>🎯 How Verify Mode Works:</b>\n"
            "• Users must complete verification shortlinks\n"
            "• After verification, they get direct downloads\n"
            "• Verification resets after time gap\n\n"
            "<b>🔗 Verification Order:</b>\n"
            f"• First Visit: {'Verify 3 ✅' if verify_shortlinks.get('shortlink3', {}).get('url') else 'Verify 3 ❌'}\n"
            f"• Second Visit: {'Verify 2 ✅' if verify_shortlinks.get('shortlink2', {}).get('url') else 'Verify 2 ❌'}\n"
            f"• Third Visit: {'Verify 1 ✅' if verify_shortlinks.get('shortlink1', {}).get('url') else 'Verify 1 ❌'}\n"
            f"• After All: Direct Download\n\n"
            "<b>⏱️ Time Gap:</b> " + f"{(chat_settings.get('verify_time_gap', 14400) // 3600)}h",
                         reply_markup=InlineKeyboardMarkup(buttons)
         )

    elif data.startswith("chl_pagemode_set"):
        # Set channel page mode shortlink with interactive input
        parts = data.split('_')
        shortlink_num = int(parts[3])
        chat_id = parts[4]
        
        await query.message.delete()
        try:
            # Get channel info for display
            channel_doc = await u_db.get_channel_detail(chat_id)
            channel_title = channel_doc.get('title', 'Unknown Channel') if channel_doc else 'Unknown Channel'
            
            tamil = await bot.send_message(
                chat_id=query.message.chat.id,
                text=f"<b>⚙️ CHANNEL PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
                     f"<b>📺 Channel:</b> {channel_title}\n"
                     f"<b>🆔 ID:</b> <code>{chat_id}</code>\n\n"
                     f"<b>Step 1:</b> Send your shortener URL\n"
                     f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
                     f"<b>📝 Instructions:</b>\n"
                     f"• Enter only the domain name\n"
                     f"• Don't include http:// or https://\n"
                     f"• Make sure the service supports API\n\n"
                     f"<b>⚡ Alternative:</b> Use command <code>/chlpagemode{shortlink_num} {chat_id} url api</code>\n\n"
                     f"Send <code>/cancel</code> to cancel this process.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('❌ Cancel', callback_data=f"chl_pagemode_shortlinks_{chat_id}")],
                    [InlineKeyboardButton("📚 Use Command Instead", callback_data="chl_pagemode_commands_help")]
                ])
            )
            
            # Wait for URL input
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process canceled!</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                    ])
                )
            
            shortener_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for API
            await tamil.edit_text(
                f"<b>⚙️ CHANNEL PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
                f"<b>📺 Channel:</b> {channel_title}\n"
                f"<b>✅ URL:</b> <code>{shortener_url}</code>\n\n"
                f"<b>Step 2:</b> Send your API key\n"
                f"<b>Example:</b> <code>abc123xyz789</code>\n\n"
                f"Send <code>/cancel</code> to cancel this process.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('❌ Cancel', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                ])
            )
            
            # Wait for API input
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if api_msg.text == "/cancel":
                await api_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process canceled!</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                    ])
                )
            
            shortener_api = api_msg.text.strip()
            await api_msg.delete()
            
            # Test the shortlink
            await tamil.edit_text(
                f"<b>🔄 TESTING CHANNEL PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
                f"<b>📺 Channel:</b> {channel_title}\n"
                f"<b>🔗 URL:</b> <code>{shortener_url}</code>\n"
                f"<b>🔑 API:</b> <code>{shortener_api[:10]}...</code>\n\n"
                f"<b>Please wait while we test your shortlink...</b>",
                reply_markup=None
            )
            
            try:
                from shortzy import Shortzy
                test_url = "https://telegram.org"
                shortzy = Shortzy(api_key=shortener_api, base_site=shortener_url)
                short_url = await shortzy.convert(test_url)
                
                if not short_url or short_url == test_url:
                    raise Exception("Shortener returned original URL")
                
                # Save to channel settings
                chat_settings = await u_db.get_chl_settings(chat_id)
                page_shortlinks = chat_settings.get('page_shortlinks', {})
                page_shortlinks[f"shortlink{shortlink_num}"] = {
                    "url": shortener_url,
                    "api": shortener_api
                }
                await u_db.update_chl_settings(chat_id, 'page_shortlinks', page_shortlinks)
                
                await tamil.edit_text(
                    f"<b>✅ CHANNEL PAGE MODE SHORTLINK {shortlink_num} CONFIGURED</b>\n\n"
                    f"<b>📺 Channel:</b> {channel_title}\n"
                    f"<b>🔗 URL:</b> {shortener_url}\n"
                    f"<b>🔑 API:</b> {shortener_api[:10]}...\n"
                    f"<b>🧪 Test URL:</b> <a href='{short_url}'>Click to verify</a>\n\n"
                    f"<b>🎯 Status:</b> Ready for use in Page Mode!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back to Shortlinks', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                    ])
                )
                
            except Exception as e:
                await tamil.edit_text(
                    f"<b>❌ CHANNEL PAGE MODE SHORTLINK {shortlink_num} ERROR</b>\n\n"
                    f"<b>📺 Channel:</b> {channel_title}\n"
                    f"<b>🔗 URL:</b> {shortener_url}\n"
                    f"<b>🔑 API:</b> {shortener_api[:10]}...\n"
                    f"<b>❌ Error:</b> {str(e)}\n\n"
                    f"Please check your configuration and try again.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('🔄 Try Again', callback_data=f"chl_pagemode_set_{shortlink_num}_{chat_id}")],
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                    ])
                )
                
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text(
                "<b>⏰ Process timed out!</b>\n\nPlease try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_shortlinks_{chat_id}")]
                ])
            )

    elif data.startswith("chl_pagemode_remove"):
        # Remove channel page mode shortlink
        parts = data.split('_')
        shortlink_num = int(parts[3])
        chat_id = parts[4]
        
        # Get current settings
        chat_settings = await u_db.get_chl_settings(chat_id)
        page_shortlinks = chat_settings.get('page_shortlinks', {})
        
        # Remove the shortlink
        page_shortlinks[f"shortlink{shortlink_num}"] = {"url": None, "api": None}
        await u_db.update_chl_settings(chat_id, 'page_shortlinks', page_shortlinks)
        
        await query.answer(f"Page Mode Shortlink {shortlink_num} removed for this channel!", show_alert=True)
        
        # Refresh the shortlinks menu
        page_shortlinks = chat_settings.get('page_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        buttons = []
        for i in range(1, 4):
            shortlink_key = f"shortlink{i}"
            shortlink_data = page_shortlinks.get(shortlink_key, {"url": None, "api": None})
            
            if shortlink_data["url"] and shortlink_data["api"]:
                status = "✅"
            else:
                status = "❌"
                
            buttons.append([
                InlineKeyboardButton(f'🔗 Page Shortlink {i} {status}', callback_data=f"chl_pagemode_set_{i}_{chat_id}"),
                InlineKeyboardButton(f'🗑️ Remove {i}', callback_data=f"chl_pagemode_remove_{i}_{chat_id}")
            ])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_settings_{chat_id}")])
        
        await safe_edit_message(
            query,
            "<b>📄 CHANNEL PAGE MODE SHORTLINKS</b>\n\n"
            "<b>⚙️ Manage Shortlinks for Page Mode</b>\n\n"
            "<b>🎯 Current Configuration:</b>\n"
            f"• Shortlink 1: {'✅ Active' if page_shortlinks.get('shortlink1', {}).get('url') else '❌ Not Set'}\n"
            f"• Shortlink 2: {'✅ Active' if page_shortlinks.get('shortlink2', {}).get('url') else '❌ Not Set'}\n"
            f"• Shortlink 3: {'✅ Active' if page_shortlinks.get('shortlink3', {}).get('url') else '❌ Not Set'}\n\n"
            "<b>💡 Info:</b> Configure shortlinks that will be used when Page Mode is enabled for this channel.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("chl_verify_toggle"):
        # Toggle channel verify mode
        chat_id = data.split('_')[3]
        chat_settings = await u_db.get_chl_settings(chat_id)
        current_verify_mode = chat_settings.get('verify_mode', False)
        new_verify_mode = not current_verify_mode
        
        await u_db.update_chl_settings(chat_id, 'verify_mode', new_verify_mode)
        
        status = "enabled" if new_verify_mode else "disabled"
        await query.answer(f"Verify Mode {status} for this channel!", show_alert=True)
        
        # Refresh the verify settings menu
        verify_mode = new_verify_mode
        verify_shortlinks = chat_settings.get('verify_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        buttons = []
        
        # Verify mode toggle
        verify_status = "✅ Enabled" if verify_mode else "❌ Disabled"
        buttons.append([InlineKeyboardButton(f'🔐 Verify Mode: {verify_status}', callback_data=f"chl_verify_toggle_{chat_id}")])
        
        if verify_mode:
            # Show verify shortlinks only if verify mode is enabled
            for i in range(1, 4):
                shortlink_key = f"shortlink{i}"
                shortlink_data = verify_shortlinks.get(shortlink_key, {"url": None, "api": None})
                
                verification_order = ["Third", "Second", "First"][i-1]  # 1=Third, 2=Second, 3=First
                
                if shortlink_data["url"] and shortlink_data["api"]:
                    status = "✅"
                else:
                    status = "❌"
                    
                buttons.append([
                    InlineKeyboardButton(f'🔐 Verify {i} ({verification_order}) {status}', callback_data=f"chl_verify_set_{i}_{chat_id}"),
                    InlineKeyboardButton(f'🗑️ Remove {i}', callback_data=f"chl_verify_remove_{i}_{chat_id}")
                ])
            
            # Verify time settings
            verify_time_gap = chat_settings.get('verify_time_gap', 14400)  # 4 hours default
            hours = verify_time_gap // 3600
            buttons.append([InlineKeyboardButton(f'⏱️ Verify Time Gap: {hours}h', callback_data=f"chl_verify_time_{chat_id}")])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_settings_{chat_id}")])
        
        await query.message.edit_text(
            "<b>🔐 CHANNEL VERIFY MODE SETTINGS</b>\n\n"
            f"<b>Status:</b> {verify_status}\n\n"
            "<b>🎯 How Verify Mode Works:</b>\n"
            "• Users must complete verification shortlinks\n"
            "• After verification, they get direct downloads\n"
            "• Verification resets after time gap\n\n"
            "<b>🔗 Verification Order:</b>\n"
            f"• First Visit: {'Verify 3 ✅' if verify_shortlinks.get('shortlink3', {}).get('url') else 'Verify 3 ❌'}\n"
            f"• Second Visit: {'Verify 2 ✅' if verify_shortlinks.get('shortlink2', {}).get('url') else 'Verify 2 ❌'}\n"
            f"• Third Visit: {'Verify 1 ✅' if verify_shortlinks.get('shortlink1', {}).get('url') else 'Verify 1 ❌'}\n"
            f"• After All: Direct Download\n\n"
            "<b>⏱️ Time Gap:</b> " + f"{(chat_settings.get('verify_time_gap', 14400) // 3600)}h",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("chl_verify_set"):
        # Set channel verify shortlink with interactive input
        parts = data.split('_')
        shortlink_num = int(parts[3])
        chat_id = parts[4]
        
        verification_order = ["Third", "Second", "First"][shortlink_num-1]
        order_desc = ["First verification (users see this first)", 
                     "Second verification (users see this second)", 
                     "Third verification (users see this third)"][shortlink_num-1]
        
        await query.message.delete()
        try:
            # Get channel info for display
            channel_doc = await u_db.get_channel_detail(chat_id)
            channel_title = channel_doc.get('title', 'Unknown Channel') if channel_doc else 'Unknown Channel'
            
            tamil = await bot.send_message(
                chat_id=query.message.chat.id,
                text=f"<b>🔐 CHANNEL VERIFY SHORTLINK {shortlink_num}</b>\n\n"
                     f"<b>📺 Channel:</b> {channel_title}\n"
                     f"<b>🆔 ID:</b> <code>{chat_id}</code>\n\n"
                     f"<b>🎯 Verification Order:</b> {verification_order}\n"
                     f"<b>📝 Description:</b> {order_desc}\n\n"
                     f"<b>Step 1:</b> Send your shortener URL\n"
                     f"<b>Example:</b> <code>verify.com</code> or <code>check.short.com</code>\n\n"
                     f"<b>📝 Instructions:</b>\n"
                     f"• Enter only the domain name\n"
                     f"• Don't include http:// or https://\n"
                     f"• Make sure the service supports API\n\n"
                     f"<b>⚡ Alternative:</b> Use command <code>/chlverify{shortlink_num} {chat_id} url api</code>\n\n"
                     f"Send <code>/cancel</code> to cancel this process.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('❌ Cancel', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")],
                    [InlineKeyboardButton("📚 Use Command Instead", callback_data="chl_verify_commands_help")]
                ])
            )
            
            # Wait for URL input
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process canceled!</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                    ])
                )
            
            shortener_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for API
            await tamil.edit_text(
                f"<b>🔐 CHANNEL VERIFY SHORTLINK {shortlink_num}</b>\n\n"
                f"<b>📺 Channel:</b> {channel_title}\n"
                f"<b>🎯 Verification Order:</b> {verification_order}\n"
                f"<b>✅ URL:</b> <code>{shortener_url}</code>\n\n"
                f"<b>Step 2:</b> Send your API key\n"
                f"<b>Example:</b> <code>abc123xyz789</code>\n\n"
                f"Send <code>/cancel</code> to cancel this process.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('❌ Cancel', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                ])
            )
            
            # Wait for API input
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if api_msg.text == "/cancel":
                await api_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process canceled!</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                    ])
                )
            
            shortener_api = api_msg.text.strip()
            await api_msg.delete()
            
            # Test the shortlink
            await tamil.edit_text(
                f"<b>🔄 TESTING CHANNEL VERIFY SHORTLINK {shortlink_num}</b>\n\n"
                f"<b>📺 Channel:</b> {channel_title}\n"
                f"<b>🎯 Verification Order:</b> {verification_order}\n"
                f"<b>🔗 URL:</b> <code>{shortener_url}</code>\n"
                f"<b>🔑 API:</b> <code>{shortener_api[:10]}...</code>\n\n"
                f"<b>Please wait while we test your verification shortlink...</b>",
                reply_markup=None
            )
            
            try:
                from shortzy import Shortzy
                test_url = "https://telegram.org"
                shortzy = Shortzy(api_key=shortener_api, base_site=shortener_url)
                short_url = await shortzy.convert(test_url)
                
                if not short_url or short_url == test_url:
                    raise Exception("Shortener returned original URL")
                
                # Save to channel settings
                chat_settings = await u_db.get_chl_settings(chat_id)
                verify_shortlinks = chat_settings.get('verify_shortlinks', {})
                verify_shortlinks[f"shortlink{shortlink_num}"] = {
                    "url": shortener_url,
                    "api": shortener_api
                }
                await u_db.update_chl_settings(chat_id, 'verify_shortlinks', verify_shortlinks)
                
                await tamil.edit_text(
                    f"<b>✅ CHANNEL VERIFY SHORTLINK {shortlink_num} CONFIGURED</b>\n\n"
                    f"<b>📺 Channel:</b> {channel_title}\n"
                    f"<b>🎯 Verification Order:</b> {verification_order}\n"
                    f"<b>🔗 URL:</b> {shortener_url}\n"
                    f"<b>🔑 API:</b> {shortener_api[:10]}...\n"
                    f"<b>🧪 Test URL:</b> <a href='{short_url}'>Click to verify</a>\n\n"
                    f"<b>🎯 Status:</b> Ready for verification system!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back to Verify Shortlinks', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                    ])
                )
                
            except Exception as e:
                await tamil.edit_text(
                    f"<b>❌ CHANNEL VERIFY SHORTLINK {shortlink_num} ERROR</b>\n\n"
                    f"<b>📺 Channel:</b> {channel_title}\n"
                    f"<b>🎯 Verification Order:</b> {verification_order}\n"
                    f"<b>🔗 URL:</b> {shortener_url}\n"
                    f"<b>🔑 API:</b> {shortener_api[:10]}...\n"
                    f"<b>❌ Error:</b> {str(e)}\n\n"
                    f"Please check your configuration and try again.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('🔄 Try Again', callback_data=f"chl_verify_set_{shortlink_num}_{chat_id}")],
                        [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                    ])
                )
                
        except asyncio.exceptions.TimeoutError:
            await tamil.edit_text(
                "<b>⏰ Process timed out!</b>\n\nPlease try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")]
                ])
            )

    elif data.startswith("chl_verify_remove"):
        # Remove channel verify shortlink
        parts = data.split('_')
        shortlink_num = int(parts[3])
        chat_id = parts[4]
        
        # Get current settings
        chat_settings = await u_db.get_chl_settings(chat_id)
        verify_shortlinks = chat_settings.get('verify_shortlinks', {})
        
        # Remove the verify shortlink
        verify_shortlinks[f"shortlink{shortlink_num}"] = {"url": None, "api": None}
        await u_db.update_chl_settings(chat_id, 'verify_shortlinks', verify_shortlinks)
        
        await query.answer(f"Verify Shortlink {shortlink_num} removed for this channel!", show_alert=True)
        
        # Go back to page mode settings instead of refreshing verify settings
        # to avoid callback query issues
        channel_doc = await u_db.get_channel_detail(chat_id)
        chat_settings = await u_db.get_chl_settings(chat_id)
        
        page_mode = chat_settings.get('page_mode', False)
        page_shortlinks = chat_settings.get('page_shortlinks', {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        })
        
        # Count configured shortlinks
        configured_count = sum(1 for i in range(1, 4) 
                             if page_shortlinks.get(f"shortlink{i}", {}).get('url'))
        
        buttons = []
        
        # Page Mode toggle
        page_mode_status = "✅ Enabled" if page_mode else "❌ Disabled" 
        buttons.append([InlineKeyboardButton(f'📄 Page Mode: {page_mode_status}', callback_data=f"chl_pagemode_toggle_{chat_id}")])
        
        # Page shortlinks management
        buttons.append([InlineKeyboardButton(f'⚙️ Manage Page Shortlinks ({configured_count}/3)', callback_data=f"chl_pagemode_shortlinks_{chat_id}")])
        
        # Verify settings (only if page mode is enabled)
        if page_mode:
            verify_mode = chat_settings.get('verify_mode', False)
            verify_status = "✅ Enabled" if verify_mode else "❌ Disabled"
            buttons.append([InlineKeyboardButton(f'🔐 Verify Mode: {verify_status}', callback_data=f"chl_pagemode_verify_{chat_id}")])
            
            if verify_mode:
                verify_shortlinks = chat_settings.get('verify_shortlinks', {})
                verify_configured = sum(1 for i in range(1, 4) 
                                      if verify_shortlinks.get(f"shortlink{i}", {}).get('url'))
                buttons.append([InlineKeyboardButton(f'🔐 Manage Verify Shortlinks ({verify_configured}/3)', callback_data=f"chl_pagemode_verify_shortlinks_{chat_id}")])
                
                # Verify time settings
                verify_time_gap = chat_settings.get('verify_time_gap', 14400)
                hours = verify_time_gap // 3600
                buttons.append([InlineKeyboardButton(f'⏱️ Verify Time Gap: {hours}h', callback_data=f"chl_verify_time_{chat_id}")])
        else:
            buttons.append([InlineKeyboardButton('ℹ️ Enable Page Mode to access Verify Settings', callback_data=f"chl_pagemode_info_{chat_id}")])
        
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data=f"editchannels_{chat_id}")])
        
        channel_title = channel_doc.get('title', 'Unknown Channel') if channel_doc else 'Unknown Channel'
        
        await query.message.edit_text(
            f"<b>📄 CHANNEL PAGE MODE SETTINGS</b>\n\n"
            f"<b>📺 Channel:</b> {channel_title}\n"
            f"<b>🆔 ID:</b> <code>{chat_id}</code>\n\n"
            f"<b>📊 Current Status:</b>\n"
            f"• Page Mode: {page_mode_status}\n"
            f"• Page Shortlinks: {configured_count}/3 configured\n"
            + (f"• Verify Mode: {verify_status}\n" if page_mode else "") +
            "\n<b>🎯 Page Mode Features:</b>\n"
            "• Beautiful web pages for downloads\n"
            "• Custom shortlink integration\n"
            "• Mobile-responsive design\n"
            "• Download analytics\n\n"
            + ("<b>🔐 Verify Mode Features:</b>\n"
               "• Progressive verification system\n"
               "• Anti-spam protection\n"
               "• Time-based verification reset\n"
               "• Direct downloads after verification\n" if page_mode else 
               "<b>💡 Enable Page Mode to unlock verification features!</b>"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    ######################## DELETE CALLBACKS ##########################

    elif data.startswith("delete"):
        file_id = data.split('_')[1]
        try:
            await StreamBot.delete_messages(chat_id=int(Telegram.FLOG_CHANNEL), message_ids=int(file_id))
            await query.answer("File Deleted successfully!", show_alert=True)
            return await bot.edit_message_reply_markup(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Deleted ✅", callback_data = "is_deleted"),
                    InlineKeyboardButton("Close", callback_data = "close")]]
                ))
        except Exception as e:  # noqa: E722
            print(e)
            # await query.message.delete()

    elif data.startswith("verify"):
        try:
            await query.answer("Verified thiss files data!", show_alert=True)
            return await bot.edit_message_reply_markup(
                chat_id=query.message.chat.id,
                message_id=query.message.id,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Verified ✅", callback_data = "is_verified"),
                    InlineKeyboardButton("Close", callback_data = "close")]]
                ))
        except Exception as e:  # noqa: E722
            print(e)

    elif data == 'is_verified':
        await query.answer("Already this file verified ✅!", show_alert=True)

    elif data == 'is_deleted':
        await query.answer("Already this file deleted ✅!", show_alert=True)

    ######################## OTHAR CALLBACKS ##########################

    elif data== "stats":
        ax = await query.message.edit_text('Refreshing.....')
        STATUS_TXT = f"""**╭──────❪ 𝗦𝗧𝗔𝗧𝗨𝗦 ❫─────⍟
│
├👤 Active Users : {await u_db.total_users_count()}
│
├👤 InActive Users : {await u_db.itotal_users_count()}
│
├🤖 Total Bots : {await u_db.total_users_bots_count()} 
│
├🤖 Total Channel : {await u_db.total_channels_count()} 
│
├🚫 Banned Users : {await u_db.total_banned_users_count()}
│
╰───────────────────⍟**"""
        await ax.edit_text(text=STATUS_TXT,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Refresh 🔃", callback_data = "stats"),
                            InlineKeyboardButton("Close ✗", callback_data = "close")]]),
                        parse_mode=enums.ParseMode.MARKDOWN)

    elif data == "status":
        ax = await query.message.edit_text('Refreshing.......')
        india_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        total, used, free = shutil.disk_usage('.')
        bot_workloads = sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
        v2_workloads = sorted(cdn_count.items(), key=lambda x: x[1], reverse=True)
        bot_workload_dict = dict(("bot" + str(c + 1), workload)for c, (_, workload) in enumerate(bot_workloads))
        v2_workload_dict = dict(("v2" + str(c + 1), workload)for c, (_, workload) in enumerate(v2_workloads))
        await ax.edit_text(
                text=tamilxd.STATUS_TXT.format(
                    date=india_time.strftime("%d-%B-%Y"),
                    time=india_time.strftime("%I:%M:%S %p"),
                    day=india_time.strftime("%A"),
                    utc_offset=india_time.strftime("%:z"),
                    #
                    currentTime=readable_time((time.time() - temp.START_TIME)),
                    total=get_readable_file_size(total),
                    used=get_readable_file_size(used),
                    free=get_readable_file_size(free),
                    cpuUsage=psutil.cpu_percent(interval=0.5),
                    memory=psutil.virtual_memory().percent,
                    disk=psutil.disk_usage('/').percent,
                    sent=get_readable_file_size(psutil.net_io_counters().bytes_sent),
                    recv=get_readable_file_size(psutil.net_io_counters().bytes_recv),
                    v1_traffic_total=sum(workload for _, workload in bot_workloads), # for this total v1 workload
                    v2_traffic_total=sum(workload for _, workload in v2_workloads), # for this total v2 workload
                    multi_clients=len(multi_clients),
                    v1_traffic_me=bot_workload_dict.get("bot1", 0), # for this bot v1 workload
                    v2_traffic_me=v2_workload_dict.get("bot1", 0), # for this bot v1 workload
                ),
                reply_markup=InlineKeyboardMarkup(
                    [[
                    InlineKeyboardButton("Refresh 🔃", callback_data = "status"),
                    InlineKeyboardButton("Close ✗", callback_data = "close")
                   ]]
               ),
           )

    ####################### OTHAR CALLBACKS ##########################

    elif data == "settings":
        # Handle back to settings navigation
        user_id = query.from_user.id
        userxdb = await u_db.get_user_details(user_id)
        
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
            [
                InlineKeyboardButton("🔗 Link Mode", callback_data="linkmode_settings"),
                InlineKeyboardButton("📄 Page Mode", callback_data="pagemode_settings"),
            ],
            [InlineKeyboardButton("Close ✗", callback_data="close")],
        ]
        
        await query.message.edit_text(
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
                LINKMODE="✅ Enabled" if userxdb.get("linkmode", False) else "❌ Disabled",
                PAGEMODE="✅ Enabled" if userxdb.get("page_mode", False) else "❌ Disabled",
                VERIFYMODE="✅ Enabled" if userxdb.get("verify_mode", False) else "❌ Disabled",
            ),
            reply_markup=InlineKeyboardMarkup(button),
            disable_web_page_preview=True,
        )

    elif data == "linkmode_settings":
        # Go directly to linkmode settings page (no toggle)
        user_id = query.from_user.id
        linkmode_status = await u_db.get_linkmode(user_id)
        
        await query.message.edit_text(
            text="<b>🔗 LINKMODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if linkmode_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Linkmode?</b>\n"
                 f"• Collect multiple files before generating links\n"
                 f"• Use custom captions with advanced placeholders\n"
                 f"• Default caption provided if no custom caption is set\n"
                 f"• Support for multiple shortener services\n"
                 f"• Batch processing with /complete command\n\n"
                 f"<b>🎯 Commands:</b>\n"
                 f"• <code>/linkmode on/off</code> - Enable/disable linkmode\n"
                 f"• <code>/setlinkmodecaption</code> - Set custom captions\n"
                 f"• <code>/shortlink1</code>, <code>/shortlink2</code>, <code>/shortlink3</code> - Set shorteners\n"
                 f"• <code>/complete</code> - Process collected files\n"
                 f"• <code>/pending</code> - View pending files\n"
                 f"• <code>/clear</code> - Clear pending files",
                reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if linkmode_status else '✅ Enable'} Linkmode", callback_data="toggle_linkmode")],
                [InlineKeyboardButton("🎨 Linkmode Captions", callback_data="linkmode_captions_menu")],
                [InlineKeyboardButton("🔗 Shortlinks", callback_data="linkmode_shortlinks_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "pagemode_settings":
        # Go directly to page mode settings page (no toggle) 
        await show_page_mode_settings(bot, query)

    # VERIFY TUTORIAL FUNCTIONALITY
    elif data.startswith("verify_tutorial_add_"):
        shortlink_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>📺 ADD VERIFY TUTORIAL - Shortlink {shortlink_num}</b>\n\n"
                 f"<b>Step 1:</b> Send your tutorial video URL\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Use YouTube, Telegram, or any video link\n"
                 f"• Show users how to complete verification\n"
                 f"• Explain the verification process clearly\n"
                 f"• Keep video short and helpful (2-5 minutes)\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>https://youtu.be/verification_guide</code>\n"
                 f"• <code>https://t.me/your_channel/tutorial</code>\n\n"
                 f"Send <code>/cancel</code> to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            
            video_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for button text
            await tamil.edit_text(
                f"<b>📺 VERIFY TUTORIAL SETUP - Shortlink {shortlink_num}</b>\n\n"
                f"<b>✅ Video URL:</b> <code>{video_url}</code>\n\n"
                f"<b>Step 2:</b> Send button text for tutorial\n\n"
                f"<b>📝 Examples:</b>\n"
                f"• <code>📺 Verify Tutorial</code>\n"
                f"• <code>🎓 How to Verify</code>\n"
                f"• <code>📖 Verification Guide</code>\n\n"
                f"<b>Default:</b> 📺 Verify Tutorial\n\n"
                f"Send button text or <code>/skip</code> for default:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
            
            text_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if text_msg.text == "/cancel":
                await text_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            
            button_text = "📺 Verify Tutorial" if text_msg.text == "/skip" else text_msg.text.strip()
            await text_msg.delete()
            
            # Save tutorial settings
            verify_settings = await u_db.get_verify_settings(user_id)
            if "shortlink_tutorials" not in verify_settings:
                verify_settings["shortlink_tutorials"] = {}
            
            verify_settings["shortlink_tutorials"][f"shortlink{shortlink_num}"] = {
                "enabled": True,
                "video_url": video_url,
                "button_text": button_text
            }
            
            await u_db.update_verify_settings(user_id, verify_settings)
            
            await tamil.edit_text(
                f"<b>✅ VERIFY TUTORIAL ADDED</b>\n\n"
                f"<b>📺 Verify Shortlink {shortlink_num} Tutorial:</b>\n"
                f"• Video URL: <code>{video_url}</code>\n"
                f"• Button Text: <code>{button_text}</code>\n\n"
                f"<b>🎯 Users will now see a tutorial button during verification!</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back to Verify Settings', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )

    elif data.startswith("verify_time_gap_"):
        shortlink_num = int(data.split("_")[-1])
        user_id = query.from_user.id
        
        if shortlink_num not in [2, 3]:
            await query.answer("Time gap is only available for verify shortlinks 2 and 3!", show_alert=True)
            return
        
        await query.message.delete()
        verify_settings = await u_db.get_verify_settings(user_id)
        current_gap = verify_settings.get(f"shortlink{shortlink_num}_time_gap", 60)
        
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>⏱️ SET TIME GAP - Verify Shortlink {shortlink_num}</b>\n\n"
                 f"<b>📊 Current Time Gap:</b> {current_gap} minutes\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Set time gap between uses of this verify link\n"
                 f"• Users must wait before using this link again\n"
                 f"• Prevents spam and abuse\n"
                 f"• Minimum: 1 minute, Maximum: 1440 minutes (24 hours)\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>60</code> (1 hour)\n"
                 f"• <code>240</code> (4 hours)\n"
                 f"• <code>480</code> (8 hours)\n\n"
                 f"Send time gap in minutes or <code>/cancel</code> to cancel:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
        )
        
        try:
            gap_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if gap_msg.text == "/cancel":
                await gap_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            
            try:
                time_gap = int(gap_msg.text.strip())
                if time_gap < 1 or time_gap > 1440:
                    raise ValueError("Time gap must be between 1 and 1440 minutes")
                
                await gap_msg.delete()
                
                # Save time gap settings
                verify_settings[f"shortlink{shortlink_num}_time_gap"] = time_gap
                await u_db.update_verify_settings(user_id, verify_settings)
                
                hours = time_gap // 60
                minutes = time_gap % 60
                time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                
                await tamil.edit_text(
                    f"<b>✅ TIME GAP SET</b>\n\n"
                    f"<b>⏱️ Verify Shortlink {shortlink_num}:</b>\n"
                    f"• Time Gap: {time_gap} minutes ({time_str})\n\n"
                    f"<b>🎯 Users will need to wait {time_str} between uses of this verification link!</b>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('≺≺ Back to Verify Settings', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]
                    ])
                )
                
            except ValueError as e:
                await gap_msg.delete()
                await tamil.edit_text(
                    f"<b>❌ Invalid time gap!</b>\n\n"
                    f"Please enter a number between 1 and 1440 minutes.\n"
                    f"Error: {str(e)}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔄 Try Again', callback_data=f"verify_time_gap_{shortlink_num}")],
                                                      [InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )

    # CUSTOM BUTTONS FUNCTIONALITY
    elif data == "pagemode_custom_buttons":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        custom_buttons = page_settings.get("custom_buttons", [])
        
        text = "<b>🎛️ CUSTOM BUTTONS</b>\n\n"
        text += "<b>🎯 Add Your Own Custom Buttons</b>\n\n"
        text += f"<b>📊 Current Buttons:</b> {len(custom_buttons)}/5\n\n"
        
        if custom_buttons:
            for i, button in enumerate(custom_buttons, 1):
                text += f"<b>{i}.</b> {button.get('name', 'Unnamed')}\n"
                text += f"   🔗 <code>{button.get('url', 'No URL')}</code>\n"
                text += f"   🎨 Icon: {button.get('icon', '🔘')}\n\n"
        else:
            text += "<i>No custom buttons added yet.</i>\n\n"
        
        text += "<b>💡 Custom Button Features:</b>\n"
        text += "• Add up to 5 custom buttons\n"
        text += "• Link to your channels, websites, etc.\n"
        text += "• Choose custom names and icons\n"
        text += "• Show on all your shortlink pages\n"
        text += "• Great for promotion and engagement"
        
        buttons = []
        
        if len(custom_buttons) < 5:
            buttons.append([InlineKeyboardButton("➕ Add Custom Button", callback_data="custom_button_add")])
        
        if custom_buttons:
            buttons.append([InlineKeyboardButton("✏️ Manage Buttons", callback_data="custom_button_manage")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "custom_button_add":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        custom_buttons = page_settings.get("custom_buttons", [])
        
        if len(custom_buttons) >= 5:
            await query.answer("You can only add up to 5 custom buttons!", show_alert=True)
            return
        
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>➕ ADD CUSTOM BUTTON</b>\n\n"
                 f"<b>📊 Current Buttons:</b> {len(custom_buttons)}/5\n\n"
                 f"<b>Step 1:</b> Send button name\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Choose a clear, descriptive name\n"
                 f"• Keep it short (max 30 characters)\n"
                 f"• Avoid special characters\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>Join Our Channel</code>\n"
                 f"• <code>Visit Website</code>\n"
                 f"• <code>Download App</code>\n"
                 f"• <code>Follow Us</code>\n\n"
                 f"Send button name or <code>/cancel</code> to cancel:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data="pagemode_custom_buttons")]])
        )
        
        try:
            name_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if name_msg.text == "/cancel":
                await name_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="pagemode_custom_buttons")]])
                )
            
            button_name = name_msg.text.strip()[:30]  # Limit to 30 characters
            await name_msg.delete()
            
            # Ask for URL
            await tamil.edit_text(
                f"<b>➕ ADD CUSTOM BUTTON</b>\n\n"
                f"<b>✅ Button Name:</b> <code>{button_name}</code>\n\n"
                f"<b>Step 2:</b> Send button URL\n\n"
                f"<b>📋 Instructions:</b>\n"
                f"• Use complete URLs with http:// or https://\n"
                f"• Telegram links: t.me/channel\n"
                f"• Website links: https://example.com\n"
                f"• Make sure link is working\n\n"
                f"<b>💡 Examples:</b>\n"
                f"• <code>https://t.me/your_channel</code>\n"
                f"• <code>https://your-website.com</code>\n"
                f"• <code>https://play.google.com/store/apps</code>\n\n"
                f"Send button URL or <code>/cancel</code> to cancel:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data="pagemode_custom_buttons")]])
            )
            
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="pagemode_custom_buttons")]])
                )
            
            button_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for icon
            await tamil.edit_text(
                f"<b>➕ ADD CUSTOM BUTTON</b>\n\n"
                f"<b>✅ Button Name:</b> <code>{button_name}</code>\n"
                f"<b>✅ Button URL:</b> <code>{button_url}</code>\n\n"
                f"<b>Step 3:</b> Send button icon (emoji)\n\n"
                f"<b>📋 Instructions:</b>\n"
                f"• Send a single emoji to use as button icon\n"
                f"• Choose emoji that represents your button\n\n"
                f"<b>💡 Examples:</b>\n"
                f"• <code>📱</code> for apps\n"
                f"• <code>🌐</code> for websites\n"
                f"• <code>📢</code> for channels\n"
                f"• <code>💬</code> for groups\n\n"
                f"Send emoji or <code>/skip</code> for default (🔘):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data="pagemode_custom_buttons")]])
            )
            
            icon_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if icon_msg.text == "/cancel":
                await icon_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="pagemode_custom_buttons")]])
                )
            
            button_icon = "🔘" if icon_msg.text == "/skip" else icon_msg.text.strip()[:2]  # Limit to 2 characters
            await icon_msg.delete()
            
            # Save custom button
            new_button = {
                "name": button_name,
                "url": button_url,
                "icon": button_icon
            }
            
            custom_buttons.append(new_button)
            page_settings["custom_buttons"] = custom_buttons
            await u_db.update_page_settings(user_id, page_settings)
            
            await tamil.edit_text(
                f"<b>✅ CUSTOM BUTTON ADDED</b>\n\n"
                f"<b>🎛️ Button Details:</b>\n"
                f"• Name: <code>{button_name}</code>\n"
                f"• URL: <code>{button_url}</code>\n"
                f"• Icon: {button_icon}\n\n"
                f"<b>🎯 This button will now appear on all your shortlink pages!</b>\n\n"
                f"<b>📊 Total Buttons:</b> {len(custom_buttons)}/5",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('➕ Add Another Button', callback_data="custom_button_add")] if len(custom_buttons) < 5 else [],
                    [InlineKeyboardButton('≺≺ Back to Custom Buttons', callback_data="pagemode_custom_buttons")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data="pagemode_custom_buttons")]])
            )

    elif data == "custom_button_manage":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        custom_buttons = page_settings.get("custom_buttons", [])
        
        text = "<b>✏️ MANAGE CUSTOM BUTTONS</b>\n\n"
        text += f"<b>📊 Current Buttons:</b> {len(custom_buttons)}/5\n\n"
        
        buttons = []
        for i, button in enumerate(custom_buttons):
            button_text = f"{button.get('icon', '🔘')} {button.get('name', 'Unnamed')}"
            buttons.append([
                InlineKeyboardButton(button_text, callback_data=f"custom_button_edit_{i}"),
                InlineKeyboardButton("🗑️", callback_data=f"custom_button_delete_{i}")
            ])
        
        if not custom_buttons:
            text += "<i>No custom buttons to manage.</i>\n\n"
            buttons.append([InlineKeyboardButton("➕ Add Custom Button", callback_data="custom_button_add")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_custom_buttons"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("custom_button_delete_"):
        button_index = int(data.split("_")[-1])
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        custom_buttons = page_settings.get("custom_buttons", [])
        
        if 0 <= button_index < len(custom_buttons):
            deleted_button = custom_buttons.pop(button_index)
            page_settings["custom_buttons"] = custom_buttons
            await u_db.update_page_settings(user_id, page_settings)
            
            await query.answer(f"Deleted button: {deleted_button.get('name', 'Unnamed')}", show_alert=True)
            
            # Refresh the manage page
            text = "<b>✏️ MANAGE CUSTOM BUTTONS</b>\n\n"
            text += f"<b>📊 Current Buttons:</b> {len(custom_buttons)}/5\n\n"
            
            buttons = []
            for i, button in enumerate(custom_buttons):
                button_text = f"{button.get('icon', '🔘')} {button.get('name', 'Unnamed')}"
                buttons.append([
                    InlineKeyboardButton(button_text, callback_data=f"custom_button_edit_{i}"),
                    InlineKeyboardButton("🗑️", callback_data=f"custom_button_delete_{i}")
                ])
            
            if not custom_buttons:
                text += "<i>No custom buttons to manage.</i>\n\n"
                buttons.append([InlineKeyboardButton("➕ Add Custom Button", callback_data="custom_button_add")])
            
            buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_custom_buttons"), InlineKeyboardButton("Close", callback_data="close")])
            
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
        else:
            await query.answer("Button not found!", show_alert=True)

    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
        except:  # noqa: E722
            await query.message.delete()

    elif data == "toggle_pagemode":
        current_status = await u_db.get_page_mode(user_id)
        new_status = not current_status
        await u_db.set_page_mode(user_id, new_status)
        
        # If disabling page mode, also disable verify mode for consistency
        if not new_status:
            await u_db.set_verify_mode(user_id, False)
            await query.answer("Page Mode disabled! Verify Mode also disabled.", show_alert=True)
        else:
            await query.answer("Page Mode enabled!", show_alert=True)
        
        # Show page mode settings using helper function
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_shortlinks":
        user_id = query.from_user.id
        page_shortlinks = await u_db.get_page_shortlinks(user_id)
        
        text = "<b>📄 PAGE MODE SHORTLINKS</b>\n\n"
        text += "<b>⚙️ Manage Shortlinks & Customization</b>\n\n"
        text += "<b>🎯 Current Configuration:</b>\n"
        for i in range(1, 4):
            shortlink_data = page_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"• Shortlink {i}: {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Management Options:</b>\n"
        text += "• Configure shortlinks and tutorials\n"
        text += "• Customize button visibility and names\n"
        text += "• Add custom channel buttons\n"
        text += "• Test all configurations"
        
        buttons = []
        for i in range(1, 4):
            shortlink_data = page_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Shortlink {i}", callback_data=f"pagemode_shortlink_{i}")])
        
        # Add customization buttons
        buttons.append([
            InlineKeyboardButton("📺 Tutorial Settings", callback_data="pagemode_tutorials"),
            InlineKeyboardButton("🎛️ Button Settings", callback_data="pagemode_button_settings")
        ])
        buttons.append([
            InlineKeyboardButton("⭐ Custom Buttons", callback_data="pagemode_custom_buttons"),
            InlineKeyboardButton("🎨 Button Names", callback_data="pagemode_button_names")
        ])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "pagemode_tutorials":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📺 TUTORIAL SETTINGS</b>\n\n"
        text += "<b>🎯 Add Tutorial Videos for Each Shortlink</b>\n\n"
        text += "<b>📊 Current Status:</b>\n"
        
        tutorials = page_settings.get("shortlink_tutorials", {})
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status = "✅ Enabled" if tutorial_data.get("enabled", False) else "❌ Disabled"
            text += f"• Shortlink {i}: {status}\n"
            if tutorial_data.get("video_url"):
                text += f"   📺 Video: {tutorial_data['video_url'][:50]}...\n"
                text += f"   🔘 Button: {tutorial_data.get('button_text', '📺 Tutorial')}\n"
            text += "\n"
        
        text += "<b>💡 How it works:</b>\n"
        text += "• Users see tutorial button on shortlink page\n"
        text += "• Helps users understand how to use shortlinks\n"
        text += "• Reduces support queries\n"
        text += "• Improves user experience"
        
        buttons = []
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status_icon = "✅" if tutorial_data.get("enabled", False) else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Tutorial {i}", callback_data=f"pagemode_tutorial_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        tutorial_data = page_settings.get("shortlink_tutorials", {}).get(f"shortlink{shortlink_num}", {})
        
        text = f"<b>📺 TUTORIAL SETTINGS - Shortlink {shortlink_num}</b>\n\n"
        text += f"<b>📊 Current Status:</b>\n"
        text += f"• Enabled: {'✅ Yes' if tutorial_data.get('enabled', False) else '❌ No'}\n"
        text += f"• Video URL: {tutorial_data.get('video_url', 'Not set')}\n"
        text += f"• Button Text: {tutorial_data.get('button_text', '📺 Tutorial')}\n\n"
        text += f"<b>💡 Tutorial Videos Help:</b>\n"
        text += f"• Show users how to bypass ads\n"
        text += f"• Explain shortlink process\n"
        text += f"• Reduce support queries\n"
        text += f"• Improve user experience"
        
        buttons = []
        if tutorial_data.get("enabled", False):
            buttons.append([InlineKeyboardButton("❌ Disable Tutorial", callback_data=f"pagemode_tutorial_disable_{shortlink_num}")])
            buttons.append([
                InlineKeyboardButton("🔗 Change Video URL", callback_data=f"pagemode_tutorial_url_{shortlink_num}"),
                InlineKeyboardButton("📝 Change Button Text", callback_data=f"pagemode_tutorial_text_{shortlink_num}")
            ])
        else:
            buttons.append([InlineKeyboardButton("✅ Enable Tutorial", callback_data=f"pagemode_tutorial_enable_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_tutorials"), InlineKeyboardButton("Close", callback_data="close")])
        
        await safe_edit_message(query, text, InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_enable_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>📺 ENABLE TUTORIAL - Shortlink {shortlink_num}</b>\n\n"
                 f"<b>Step 1:</b> Send your tutorial video URL\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Use YouTube, Telegram, or any video link\n"
                 f"• Make sure video shows how to use shortlinks\n"
                 f"• Keep video short and clear (2-5 minutes)\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>https://youtu.be/abc123</code>\n"
                 f"• <code>https://t.me/channel/123</code>\n\n"
                 f"Send <code>/cancel</code> to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            video_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for button text
            await tamil.edit_text(
                f"<b>📺 TUTORIAL SETUP - Shortlink {shortlink_num}</b>\n\n"
                f"<b>✅ Video URL:</b> <code>{video_url}</code>\n\n"
                f"<b>Step 2:</b> Send button text for tutorial\n\n"
                f"<b>📝 Examples:</b>\n"
                f"• <code>📺 How to Use</code>\n"
                f"• <code>🎓 Tutorial Video</code>\n"
                f"• <code>📖 Guide</code>\n\n"
                f"<b>Default:</b> 📺 Tutorial\n\n"
                f"Send button text or <code>/skip</code> for default:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )
            
            text_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if text_msg.text == "/cancel":
                await text_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            button_text = "📺 Tutorial" if text_msg.text == "/skip" else text_msg.text.strip()
            await text_msg.delete()
            
            # Save tutorial settings
            page_settings = await u_db.get_page_settings(user_id)
            if "shortlink_tutorials" not in page_settings:
                page_settings["shortlink_tutorials"] = {}
            
            page_settings["shortlink_tutorials"][f"shortlink{shortlink_num}"] = {
                "enabled": True,
                "video_url": video_url,
                "button_text": button_text
            }
            
            await u_db.update_page_settings(user_id, page_settings)
            
            await tamil.edit_text(
                f"<b>✅ TUTORIAL ENABLED</b>\n\n"
                f"<b>📺 Shortlink {shortlink_num} Tutorial:</b>\n"
                f"• Video URL: <code>{video_url}</code>\n"
                f"• Button Text: <code>{button_text}</code>\n\n"
                f"<b>🎯 Users will now see a tutorial button on your shortlink page!</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back to Tutorial Settings', callback_data="pagemode_tutorials")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )

    elif data == "pagemode_button_settings":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        text = "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
        text += "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
        text += "<b>📊 Current Visibility:</b>\n"
        text += f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
        text += f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
        text += f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
        text += "<b>💡 Benefits:</b>\n"
        text += "• Hide buttons you don't need\n"
        text += "• Cleaner page appearance\n"
        text += "• Focus user attention\n"
        text += "• Better mobile experience"
        
        buttons = []
        watch_status = "👁️ Show" if not button_visibility.get('watch', True) else "🙈 Hide"
        download_status = "👁️ Show" if not button_visibility.get('download', True) else "🙈 Hide"
        telegram_status = "👁️ Show" if not button_visibility.get('telegram', True) else "🙈 Hide"
        
        buttons.append([
            InlineKeyboardButton(f"{watch_status} Watch", callback_data="pagemode_toggle_watch"),
            InlineKeyboardButton(f"{download_status} Download", callback_data="pagemode_toggle_download")
        ])
        buttons.append([InlineKeyboardButton(f"{telegram_status} Telegram", callback_data="pagemode_toggle_telegram")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_toggle_"):
        button_type = data.split("_")[-1]
        user_id = query.from_user.id
        
        page_settings = await u_db.get_page_settings(user_id)
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        # Toggle the button visibility
        current_status = button_visibility.get(button_type, True)
        button_visibility[button_type] = not current_status
        
        page_settings["button_visibility"] = button_visibility
        await u_db.update_page_settings(user_id, page_settings)
        
        new_status = "visible" if not current_status else "hidden"
        await query.answer(f"{button_type.title()} button is now {new_status}!", show_alert=True)
        
        # Refresh button settings menu
        await query.message.edit_text(
            "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
            "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
            "<b>📊 Current Visibility:</b>\n"
            f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
            f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
            f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
            "<b>💡 Benefits:</b>\n"
            "• Hide buttons you don't need\n"
            "• Cleaner page appearance\n"
            "• Focus user attention\n"
            "• Better mobile experience",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('watch', True) else '🙈 Hide'} Watch", callback_data="pagemode_toggle_watch"),
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('download', True) else '🙈 Hide'} Download", callback_data="pagemode_toggle_download")
                ],
                [InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('telegram', True) else '🙈 Hide'} Telegram", callback_data="pagemode_toggle_telegram")],
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        shortlink_data = await u_db.get_page_shortlinks(user_id)
        current_shortlink = shortlink_data.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>📄 PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Page Mode Shortlinks:</b>\n"
        text += f"• This shortlink will appear as 'Shortlink Set {shortlink_num}' on the page\n"
        text += f"• Users will see 3 buttons: Watch Online, Download, Telegram Storage\n"
        text += f"• Each button uses this shortlink service\n"
        text += f"• Test before saving to ensure it works properly\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure new shortlink URL and API\n"
        text += f"• Test current configuration\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_page_shortlink(user_id, shortlink_num)
        await query.answer(f"Page Mode Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlinks list
        await query.answer("", show_alert=False)
        # Trigger pagemode_shortlinks callback
        from pyrogram.types import CallbackQuery
        mock_query = CallbackQuery(
            id=query.id,
            from_user=query.from_user,
            chat_instance=query.chat_instance,
            data="pagemode_shortlinks",
            message=query.message
        )
        return await cb_handler(bot, mock_query)

    elif data.startswith("pagemode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pagemode{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_page_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Page Mode Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )

    elif data == "toggle_verifymode":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show verify mode settings
        text = f"<b>🔐 VERIFY MODE SETTINGS</b>\n\n"
        text += f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n\n"
        text += f"<b>📋 What is Verify Mode?</b>\n"
        text += f"• Progressive shortlink verification system\n"
        text += f"• Users must complete shortlinks before accessing files\n"
        text += f"• Support up to 3 verification shortlinks per day\n"
        text += f"• After completing all verifications, direct access is granted\n"
        text += f"• Verification count resets daily\n\n"
        text += f"<b>🎯 How it works:</b>\n"
        text += f"• User visits shortlink page\n"
        text += f"• First visit: Shortlink 3 (if configured)\n"
        text += f"• Second visit: Shortlink 2 (if configured)\n"
        text += f"• Third visit: Shortlink 1 (if configured)\n"
        text += f"• Fourth+ visits: Direct access to file\n\n"
        text += f"<b>⚙️ Configuration:</b>\n"
        text += f"• Configure verification shortlinks independently\n"
        text += f"• Set custom verification time gaps\n"
        text += f"• Monitor user verification status\n"
        text += f"• Automatic daily reset functionality"
        
        buttons = []
        if new_status:
            buttons.append([InlineKeyboardButton("⚙️ Manage Verify Shortlinks", callback_data="verifymode_shortlinks")])
            buttons.append([InlineKeyboardButton("⏱️ Time Settings", callback_data="verifymode_time_settings")])
        buttons.append([InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Verify Mode", callback_data="toggle_verifymode")])
        buttons.append([InlineKeyboardButton("≺≺ Back to Settings", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 VERIFY MODE SHORTLINKS</b>\n\n"
        
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"<b>Verify Shortlink {i}:</b> {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Verification Flow:</b>\n"
        text += "• Shortlink 3: First verification of the day\n"
        text += "• Shortlink 2: Second verification of the day\n"
        text += "• Shortlink 1: Third verification of the day\n"
        text += "• Direct Access: After 3 verifications\n\n"
        text += "<b>💡 Tips:</b>\n"
        text += "• Configure all 3 shortlinks for maximum monetization\n"
        text += "• Test shortlinks before saving\n"
        text += "• Users get direct access after completing all verifications"
        
        buttons = []
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i}", callback_data=f"verifymode_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("verifymode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"verifymode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"verifymode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_time_settings":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        verification_status = await u_db.get_verification_status(user_id)
        
        # Convert seconds to hours for display
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours ({verify_time_gap} seconds)\n\n"
        text += f"<b>📊 Today's Status:</b>\n"
        text += f"• Verifications completed: {verification_status.get('verify_count_today', 0)}\n"
        text += f"• Last reset: {verification_status.get('last_reset_date', 'Never')}\n\n"
        text += f"<b>📋 How Time Gap Works:</b>\n"
        text += f"• Controls minimum time between verification requirements\n"
        text += f"• Default: 4 hours (recommended)\n"
        text += f"• Users can access files directly within time gap after verification\n"
        text += f"• Count resets daily at midnight\n\n"
        text += f"<b>💡 Recommended Settings:</b>\n"
        text += f"• 1 hour: High monetization, frequent verification\n"
        text += f"• 4 hours: Balanced approach (recommended)\n"
        text += f"• 8 hours: User-friendly, less frequent verification\n"
        text += f"• 24 hours: One verification per day maximum"
        
        buttons = []
        time_options = [
            ("1 Hour", 3600),
            ("4 Hours", 14400),
            ("8 Hours", 28800),
            ("24 Hours", 86400)
        ]
        
        for label, seconds in time_options:
            current_marker = "✅ " if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{current_marker}{label}", callback_data=f"set_verify_time_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("set_verify_time_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Refresh the time settings page
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Settings", callback_data="verifymode_time_settings")]
        ]))

    elif data.startswith("verifymode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        # Step 2: Get API
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter your API key from the shortener service\n"
            f"• Check your shortener dashboard for API key\n"
            f"• Keep it secure and don't share publicly\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text(
            f"<b>🔍 TESTING VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>URL:</b> {shortener_url}\n"
            f"<b>API:</b> {shortener_api[:20]}...\n\n"
            f"⏳ Testing shortlink configuration...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏳ Testing...', callback_data="testing")]])
        )
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )

    elif data.startswith("verifymode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlink configuration
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> ❌ Not configured\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    # Page Mode Verify Callbacks
    elif data == "pagemode_toggle_verify":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show page mode settings directly without using mock query
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_verify_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 PAGE MODE VERIFY SHORTLINKS</b>\n\n"
        text += "<b>📋 Verification Logic:</b>\n"
        text += "• <b>First Visit:</b> User completes Verify Shortlink 3\n"
        text += "• <b>Second Visit:</b> User completes Verify Shortlink 2\n"
        text += "• <b>Third Visit:</b> User completes Verify Shortlink 1\n"
        text += "• <b>Fourth+ Visits:</b> Direct access to file\n"
        text += "• Verification count resets daily\n\n"
        
        for i in range(3, 0, -1):  # 3, 2, 1 order
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            visit_order = ["Third", "Second", "First"][3-i]
            text += f"<b>Verify Shortlink {i}:</b> {status} ({visit_order} visit)\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Management:</b>\n"
        text += "• Configure each verify shortlink independently\n"
        text += "• Test shortlinks before saving\n"
        text += "• Remove shortlinks if not needed\n"
        text += "• Users progress through verification levels daily"
        
        buttons = []
        for i in range(3, 0, -1):  # 3, 2, 1 order for display
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            visit_order = ["Third", "Second", "First"][3-i]
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i} ({visit_order} visit)", callback_data=f"pagemode_verify_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        # Determine verification order
        if shortlink_num == "3":
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used for the second verification attempt of the day"
        else:  # shortlink_num == "1"
            verification_order = "Third verification"
            description = "Used for the third verification attempt of the day"
        
        text = f"<b>🔐 PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n"
        text += f"• Integrates with page mode for seamless experience\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_verify_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_verify_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_verify_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Show verify shortlinks page directly
        await show_pagemode_verify_shortlinks(bot, query)

    elif data.startswith("pagemode_verify_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        # Determine verification order for display
        if shortlink_num == "3":
            verification_order = "first verification"
            order_desc = "Users encounter this shortlink on their first visit of the day"
        elif shortlink_num == "2":
            verification_order = "second verification"
            order_desc = "Users encounter this shortlink on their second visit of the day"
        else:  # shortlink_num == "1"
            verification_order = "third verification"
            order_desc = "Users encounter this shortlink on their third visit of the day"
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>📝 Description:</b> {order_desc}\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pageverify{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_verify_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing verify shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the verify shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Verify shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )

    elif data == "pagemode_verify_time":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ PAGE MODE VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours\n\n"
        text += f"<b>📋 What is Verify Time Gap?</b>\n"
        text += f"• Minimum time between verification requirements\n"
        text += f"• Prevents excessive verification requests\n"
        text += f"• Users can access files directly within this time\n"
        text += f"• Integrates with daily verification count reset\n\n"
        text += f"<b>🎯 How it works in Page Mode:</b>\n"
        text += f"• User completes verification shortlinks\n"
        text += f"• Time gap prevents immediate re-verification\n"
        text += f"• Balances security with user experience\n"
        text += f"• Works with progressive verification system\n\n"
        text += f"<b>⚙️ Choose your preferred time gap:</b>"
        
        buttons = []
        time_options = [
            (3600, "1 Hour"),
            (7200, "2 Hours"), 
            (14400, "4 Hours"),
            (21600, "6 Hours"),
            (28800, "8 Hours"),
            (43200, "12 Hours"),
            (86400, "24 Hours")
        ]
        
        for seconds, label in time_options:
            current_indicator = " ✅" if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{label}{current_indicator}", callback_data=f"pagemode_verify_time_set_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_time_set_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Show page mode settings directly
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_info":
        await query.answer(
            "ℹ️ Please enable Page Mode first to access Verify settings!\n\n"
            "Page Mode is required for the verification system to work properly.",
            show_alert=True
        )

    elif data == "pagemode_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE COMMANDS HELP</b>\n\n"
            f"<b>🎯 Regular Page Mode Shortlinks:</b>\n\n"
            f"<b>1️⃣ Page Mode Shortlink 1:</b>\n"
            f"<code>/pagemode1 shortener_url api_key</code>\n"
            f"• Primary shortlink for page mode\n\n"
            f"<b>2️⃣ Page Mode Shortlink 2:</b>\n"
            f"<code>/pagemode2 shortener_url api_key</code>\n"
            f"• Secondary shortlink for page mode\n\n"
            f"<b>3️⃣ Page Mode Shortlink 3:</b>\n"
            f"<code>/pagemode3 shortener_url api_key</code>\n"
            f"• Tertiary shortlink for page mode\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pagemode1 short.com abc123api</code>\n"
            f"<code>/pagemode2 tiny.url def456api</code>\n"
            f"<code>/pagemode3 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pagemode1 off</code> - Remove shortlink 1\n"
            f"<code>/pagemode2 off</code> - Remove shortlink 2\n"
            f"<code>/pagemode3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "pagemode_verify_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE VERIFY COMMANDS HELP</b>\n\n"
            f"<b>🎯 Quick Configuration Commands:</b>\n\n"
            f"<b>1️⃣ First Verification (Shortlink 3):</b>\n"
            f"<code>/pageverify3 shortener_url api_key</code>\n"
            f"• Users see this on their first visit of the day\n\n"
            f"<b>2️⃣ Second Verification (Shortlink 2):</b>\n"
            f"<code>/pageverify2 shortener_url api_key</code>\n"
            f"• Users see this on their second visit of the day\n\n"
            f"<b>3️⃣ Third Verification (Shortlink 1):</b>\n"
            f"<code>/pageverify1 shortener_url api_key</code>\n"
            f"• Users see this on their third visit of the day\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pageverify3 short.com abc123api</code>\n"
            f"<code>/pageverify2 tiny.url def456api</code>\n"
            f"<code>/pageverify1 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pageverify on/off</code> - Enable/disable verify mode\n"
            f"<code>/pageverify</code> - Show current status\n"
            f"<code>/pageverify1 off</code> - Remove shortlink 1\n"
            f"<code>/pageverify2 off</code> - Remove shortlink 2\n"
            f"<code>/pageverify3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_tutorials"):
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📺 TUTORIAL SETTINGS</b>\n\n"
        text += "<b>🎯 Add Tutorial Videos for Each Shortlink</b>\n\n"
        text += "<b>📊 Current Status:</b>\n"
        
        tutorials = page_settings.get("shortlink_tutorials", {})
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status = "✅ Enabled" if tutorial_data.get("enabled", False) else "❌ Disabled"
            text += f"• Shortlink {i}: {status}\n"
            if tutorial_data.get("video_url"):
                text += f"   📺 Video: {tutorial_data['video_url'][:50]}...\n"
                text += f"   🔘 Button: {tutorial_data.get('button_text', '📺 Tutorial')}\n"
            text += "\n"
        
        text += "<b>💡 How it works:</b>\n"
        text += "• Users see tutorial button on shortlink page\n"
        text += "• Helps users understand how to use shortlinks\n"
        text += "• Reduces support queries\n"
        text += "• Improves user experience"
        
        buttons = []
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status_icon = "✅" if tutorial_data.get("enabled", False) else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Tutorial {i}", callback_data=f"pagemode_tutorial_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        tutorial_data = page_settings.get("shortlink_tutorials", {}).get(f"shortlink{shortlink_num}", {})
        
        text = f"<b>📺 TUTORIAL SETTINGS - Shortlink {shortlink_num}</b>\n\n"
        text += f"<b>📊 Current Status:</b>\n"
        text += f"• Enabled: {'✅ Yes' if tutorial_data.get('enabled', False) else '❌ No'}\n"
        text += f"• Video URL: {tutorial_data.get('video_url', 'Not set')}\n"
        text += f"• Button Text: {tutorial_data.get('button_text', '📺 Tutorial')}\n\n"
        text += f"<b>💡 Tutorial Videos Help:</b>\n"
        text += f"• Show users how to bypass ads\n"
        text += f"• Explain shortlink process\n"
        text += f"• Reduce support queries\n"
        text += f"• Improve user experience"
        
        buttons = []
        if tutorial_data.get("enabled", False):
            buttons.append([InlineKeyboardButton("❌ Disable Tutorial", callback_data=f"pagemode_tutorial_disable_{shortlink_num}")])
            buttons.append([
                InlineKeyboardButton("🔗 Change Video URL", callback_data=f"pagemode_tutorial_url_{shortlink_num}"),
                InlineKeyboardButton("📝 Change Button Text", callback_data=f"pagemode_tutorial_text_{shortlink_num}")
            ])
        else:
            buttons.append([InlineKeyboardButton("✅ Enable Tutorial", callback_data=f"pagemode_tutorial_enable_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_tutorials"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_enable_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>📺 ENABLE TUTORIAL - Shortlink {shortlink_num}</b>\n\n"
                 f"<b>Step 1:</b> Send your tutorial video URL\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Use YouTube, Telegram, or any video link\n"
                 f"• Make sure video shows how to use shortlinks\n"
                 f"• Keep video short and clear (2-5 minutes)\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>https://youtu.be/abc123</code>\n"
                 f"• <code>https://t.me/channel/123</code>\n\n"
                 f"Send <code>/cancel</code> to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            video_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for button text
            await tamil.edit_text(
                f"<b>📺 TUTORIAL SETUP - Shortlink {shortlink_num}</b>\n\n"
                f"<b>✅ Video URL:</b> <code>{video_url}</code>\n\n"
                f"<b>Step 2:</b> Send button text for tutorial\n\n"
                f"<b>📝 Examples:</b>\n"
                f"• <code>📺 How to Use</code>\n"
                f"• <code>🎓 Tutorial Video</code>\n"
                f"• <code>📖 Guide</code>\n\n"
                f"<b>Default:</b> 📺 Tutorial\n\n"
                f"Send button text or <code>/skip</code> for default:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )
            
            text_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if text_msg.text == "/cancel":
                await text_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            button_text = "📺 Tutorial" if text_msg.text == "/skip" else text_msg.text.strip()
            await text_msg.delete()
            
            # Save tutorial settings
            page_settings = await u_db.get_page_settings(user_id)
            if "shortlink_tutorials" not in page_settings:
                page_settings["shortlink_tutorials"] = {}
            
            page_settings["shortlink_tutorials"][f"shortlink{shortlink_num}"] = {
                "enabled": True,
                "video_url": video_url,
                "button_text": button_text
            }
            
            await u_db.update_page_settings(user_id, page_settings)
            
            await tamil.edit_text(
                f"<b>✅ TUTORIAL ENABLED</b>\n\n"
                f"<b>📺 Shortlink {shortlink_num} Tutorial:</b>\n"
                f"• Video URL: <code>{video_url}</code>\n"
                f"• Button Text: <code>{button_text}</code>\n\n"
                f"<b>🎯 Users will now see a tutorial button on your shortlink page!</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back to Tutorial Settings', callback_data="pagemode_tutorials")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )

    elif data == "pagemode_button_settings":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        text = "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
        text += "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
        text += "<b>📊 Current Visibility:</b>\n"
        text += f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
        text += f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
        text += f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
        text += "<b>💡 Benefits:</b>\n"
        text += "• Hide buttons you don't need\n"
        text += "• Cleaner page appearance\n"
        text += "• Focus user attention\n"
        text += "• Better mobile experience"
        
        buttons = []
        watch_status = "👁️ Show" if not button_visibility.get('watch', True) else "🙈 Hide"
        download_status = "👁️ Show" if not button_visibility.get('download', True) else "🙈 Hide"
        telegram_status = "👁️ Show" if not button_visibility.get('telegram', True) else "🙈 Hide"
        
        buttons.append([
            InlineKeyboardButton(f"{watch_status} Watch", callback_data="pagemode_toggle_watch"),
            InlineKeyboardButton(f"{download_status} Download", callback_data="pagemode_toggle_download")
        ])
        buttons.append([InlineKeyboardButton(f"{telegram_status} Telegram", callback_data="pagemode_toggle_telegram")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_toggle_"):
        button_type = data.split("_")[-1]
        user_id = query.from_user.id
        
        page_settings = await u_db.get_page_settings(user_id)
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        # Toggle the button visibility
        current_status = button_visibility.get(button_type, True)
        button_visibility[button_type] = not current_status
        
        page_settings["button_visibility"] = button_visibility
        await u_db.update_page_settings(user_id, page_settings)
        
        new_status = "visible" if not current_status else "hidden"
        await query.answer(f"{button_type.title()} button is now {new_status}!", show_alert=True)
        
        # Refresh button settings menu
        await query.message.edit_text(
            "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
            "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
            "<b>📊 Current Visibility:</b>\n"
            f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
            f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
            f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
            "<b>💡 Benefits:</b>\n"
            "• Hide buttons you don't need\n"
            "• Cleaner page appearance\n"
            "• Focus user attention\n"
            "• Better mobile experience",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('watch', True) else '🙈 Hide'} Watch", callback_data="pagemode_toggle_watch"),
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('download', True) else '🙈 Hide'} Download", callback_data="pagemode_toggle_download")
                ],
                [InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('telegram', True) else '🙈 Hide'} Telegram", callback_data="pagemode_toggle_telegram")],
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        shortlink_data = await u_db.get_page_shortlinks(user_id)
        current_shortlink = shortlink_data.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>📄 PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Page Mode Shortlinks:</b>\n"
        text += f"• This shortlink will appear as 'Shortlink Set {shortlink_num}' on the page\n"
        text += f"• Users will see 3 buttons: Watch Online, Download, Telegram Storage\n"
        text += f"• Each button uses this shortlink service\n"
        text += f"• Test before saving to ensure it works properly\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure new shortlink URL and API\n"
        text += f"• Test current configuration\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_page_shortlink(user_id, shortlink_num)
        await query.answer(f"Page Mode Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlinks list
        await query.answer("", show_alert=False)
        # Trigger pagemode_shortlinks callback
        from pyrogram.types import CallbackQuery
        mock_query = CallbackQuery(
            id=query.id,
            from_user=query.from_user,
            chat_instance=query.chat_instance,
            data="pagemode_shortlinks",
            message=query.message
        )
        return await cb_handler(bot, mock_query)

    elif data.startswith("pagemode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pagemode{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
                )
            
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_page_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Page Mode Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )

    elif data == "toggle_verifymode":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show verify mode settings
        text = f"<b>🔐 VERIFY MODE SETTINGS</b>\n\n"
        text += f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n\n"
        text += f"<b>📋 What is Verify Mode?</b>\n"
        text += f"• Progressive shortlink verification system\n"
        text += f"• Users must complete shortlinks before accessing files\n"
        text += f"• Support up to 3 verification shortlinks per day\n"
        text += f"• After completing all verifications, direct access is granted\n"
        text += f"• Verification count resets daily\n\n"
        text += f"<b>🎯 How it works:</b>\n"
        text += f"• User visits shortlink page\n"
        text += f"• First visit: Shortlink 3 (if configured)\n"
        text += f"• Second visit: Shortlink 2 (if configured)\n"
        text += f"• Third visit: Shortlink 1 (if configured)\n"
        text += f"• Fourth+ visits: Direct access to file\n\n"
        text += f"<b>⚙️ Configuration:</b>\n"
        text += f"• Configure verification shortlinks independently\n"
        text += f"• Set custom verification time gaps\n"
        text += f"• Monitor user verification status\n"
        text += f"• Automatic daily reset functionality"
        
        buttons = []
        if new_status:
            buttons.append([InlineKeyboardButton("⚙️ Manage Verify Shortlinks", callback_data="verifymode_shortlinks")])
            buttons.append([InlineKeyboardButton("⏱️ Time Settings", callback_data="verifymode_time_settings")])
        buttons.append([InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Verify Mode", callback_data="toggle_verifymode")])
        buttons.append([InlineKeyboardButton("≺≺ Back to Settings", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 VERIFY MODE SHORTLINKS</b>\n\n"
        
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"<b>Verify Shortlink {i}:</b> {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Verification Flow:</b>\n"
        text += "• Shortlink 3: First verification of the day\n"
        text += "• Shortlink 2: Second verification of the day\n"
        text += "• Shortlink 1: Third verification of the day\n"
        text += "• Direct Access: After 3 verifications\n\n"
        text += "<b>💡 Tips:</b>\n"
        text += "• Configure all 3 shortlinks for maximum monetization\n"
        text += "• Test shortlinks before saving\n"
        text += "• Users get direct access after completing all verifications"
        
        buttons = []
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i}", callback_data=f"verifymode_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("verifymode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"verifymode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"verifymode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_time_settings":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        verification_status = await u_db.get_verification_status(user_id)
        
        # Convert seconds to hours for display
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours ({verify_time_gap} seconds)\n\n"
        text += f"<b>📊 Today's Status:</b>\n"
        text += f"• Verifications completed: {verification_status.get('verify_count_today', 0)}\n"
        text += f"• Last reset: {verification_status.get('last_reset_date', 'Never')}\n\n"
        text += f"<b>📋 How Time Gap Works:</b>\n"
        text += f"• Controls minimum time between verification requirements\n"
        text += f"• Default: 4 hours (recommended)\n"
        text += f"• Users can access files directly within time gap after verification\n"
        text += f"• Count resets daily at midnight\n\n"
        text += f"<b>💡 Recommended Settings:</b>\n"
        text += f"• 1 hour: High monetization, frequent verification\n"
        text += f"• 4 hours: Balanced approach (recommended)\n"
        text += f"• 8 hours: User-friendly, less frequent verification\n"
        text += f"• 24 hours: One verification per day maximum"
        
        buttons = []
        time_options = [
            ("1 Hour", 3600),
            ("4 Hours", 14400),
            ("8 Hours", 28800),
            ("24 Hours", 86400)
        ]
        
        for label, seconds in time_options:
            current_marker = "✅ " if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{current_marker}{label}", callback_data=f"set_verify_time_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("set_verify_time_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Refresh the time settings page
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Settings", callback_data="verifymode_time_settings")]
        ]))

    elif data.startswith("verifymode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        # Step 2: Get API
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter your API key from the shortener service\n"
            f"• Check your shortener dashboard for API key\n"
            f"• Keep it secure and don't share publicly\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text(
            f"<b>🔍 TESTING VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>URL:</b> {shortener_url}\n"
            f"<b>API:</b> {shortener_api[:20]}...\n\n"
            f"⏳ Testing shortlink configuration...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏳ Testing...', callback_data="testing")]])
        )
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )

    elif data.startswith("verifymode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlink configuration
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> ❌ Not configured\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    # Page Mode Verify Callbacks
    elif data == "pagemode_toggle_verify":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show page mode settings directly without using mock query
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_verify_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 PAGE MODE VERIFY SHORTLINKS</b>\n\n"
        text += "<b>📋 Verification Logic:</b>\n"
        text += "• <b>First Visit:</b> User completes Verify Shortlink 3\n"
        text += "• <b>Second Visit:</b> User completes Verify Shortlink 2\n"
        text += "• <b>Third Visit:</b> User completes Verify Shortlink 1\n"
        text += "• <b>Fourth+ Visits:</b> Direct access to file\n"
        text += "• Verification count resets daily\n\n"
        
        for i in range(3, 0, -1):  # 3, 2, 1 order
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            visit_order = ["Third", "Second", "First"][3-i]
            text += f"<b>Verify Shortlink {i}:</b> {status} ({visit_order} visit)\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Management:</b>\n"
        text += "• Configure each verify shortlink independently\n"
        text += "• Test shortlinks before saving\n"
        text += "• Remove shortlinks if not needed\n"
        text += "• Users progress through verification levels daily"
        
        buttons = []
        for i in range(3, 0, -1):  # 3, 2, 1 order for display
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            visit_order = ["Third", "Second", "First"][3-i]
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i} ({visit_order} visit)", callback_data=f"pagemode_verify_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        # Determine verification order
        if shortlink_num == "3":
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used for the second verification attempt of the day"
        else:  # shortlink_num == "1"
            verification_order = "Third verification"
            description = "Used for the third verification attempt of the day"
        
        text = f"<b>🔐 PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n"
        text += f"• Integrates with page mode for seamless experience\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_verify_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_verify_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_verify_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Show verify shortlinks page directly
        await show_pagemode_verify_shortlinks(bot, query)

    elif data.startswith("pagemode_verify_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        # Determine verification order for display
        if shortlink_num == "3":
            verification_order = "first verification"
            order_desc = "Users encounter this shortlink on their first visit of the day"
        elif shortlink_num == "2":
            verification_order = "second verification"
            order_desc = "Users encounter this shortlink on their second visit of the day"
        else:  # shortlink_num == "1"
            verification_order = "third verification"
            order_desc = "Users encounter this shortlink on their third visit of the day"
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>📝 Description:</b> {order_desc}\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pageverify{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_verify_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing verify shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the verify shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Verify shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )

    elif data == "pagemode_verify_time":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ PAGE MODE VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours\n\n"
        text += f"<b>📋 What is Verify Time Gap?</b>\n"
        text += f"• Minimum time between verification requirements\n"
        text += f"• Prevents excessive verification requests\n"
        text += f"• Users can access files directly within this time\n"
        text += f"• Integrates with daily verification count reset\n\n"
        text += f"<b>🎯 How it works in Page Mode:</b>\n"
        text += f"• User completes verification shortlinks\n"
        text += f"• Time gap prevents immediate re-verification\n"
        text += f"• Balances security with user experience\n"
        text += f"• Works with progressive verification system\n\n"
        text += f"<b>⚙️ Choose your preferred time gap:</b>"
        
        buttons = []
        time_options = [
            (3600, "1 Hour"),
            (7200, "2 Hours"), 
            (14400, "4 Hours"),
            (21600, "6 Hours"),
            (28800, "8 Hours"),
            (43200, "12 Hours"),
            (86400, "24 Hours")
        ]
        
        for seconds, label in time_options:
            current_indicator = " ✅" if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{label}{current_indicator}", callback_data=f"pagemode_verify_time_set_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_time_set_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Show page mode settings directly
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_info":
        await query.answer(
            "ℹ️ Please enable Page Mode first to access Verify settings!\n\n"
            "Page Mode is required for the verification system to work properly.",
            show_alert=True
        )

    elif data == "pagemode_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE COMMANDS HELP</b>\n\n"
            f"<b>🎯 Regular Page Mode Shortlinks:</b>\n\n"
            f"<b>1️⃣ Page Mode Shortlink 1:</b>\n"
            f"<code>/pagemode1 shortener_url api_key</code>\n"
            f"• Primary shortlink for page mode\n\n"
            f"<b>2️⃣ Page Mode Shortlink 2:</b>\n"
            f"<code>/pagemode2 shortener_url api_key</code>\n"
            f"• Secondary shortlink for page mode\n\n"
            f"<b>3️⃣ Page Mode Shortlink 3:</b>\n"
            f"<code>/pagemode3 shortener_url api_key</code>\n"
            f"• Tertiary shortlink for page mode\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pagemode1 short.com abc123api</code>\n"
            f"<code>/pagemode2 tiny.url def456api</code>\n"
            f"<code>/pagemode3 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pagemode1 off</code> - Remove shortlink 1\n"
            f"<code>/pagemode2 off</code> - Remove shortlink 2\n"
            f"<code>/pagemode3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "pagemode_verify_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE VERIFY COMMANDS HELP</b>\n\n"
            f"<b>🎯 Quick Configuration Commands:</b>\n\n"
            f"<b>1️⃣ First Verification (Shortlink 3):</b>\n"
            f"<code>/pageverify3 shortener_url api_key</code>\n"
            f"• Users see this on their first visit of the day\n\n"
            f"<b>2️⃣ Second Verification (Shortlink 2):</b>\n"
            f"<code>/pageverify2 shortener_url api_key</code>\n"
            f"• Users see this on their second visit of the day\n\n"
            f"<b>3️⃣ Third Verification (Shortlink 1):</b>\n"
            f"<code>/pageverify1 shortener_url api_key</code>\n"
            f"• Users see this on their third visit of the day\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pageverify3 short.com abc123api</code>\n"
            f"<code>/pageverify2 tiny.url def456api</code>\n"
            f"<code>/pageverify1 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pageverify on/off</code> - Enable/disable verify mode\n"
            f"<code>/pageverify</code> - Show current status\n"
            f"<code>/pageverify1 off</code> - Remove shortlink 1\n"
            f"<code>/pageverify2 off</code> - Remove shortlink 2\n"
            f"<code>/pageverify3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_tutorials"):
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📺 TUTORIAL SETTINGS</b>\n\n"
        text += "<b>🎯 Add Tutorial Videos for Each Shortlink</b>\n\n"
        text += "<b>📊 Current Status:</b>\n"
        
        tutorials = page_settings.get("shortlink_tutorials", {})
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status = "✅ Enabled" if tutorial_data.get("enabled", False) else "❌ Disabled"
            text += f"• Shortlink {i}: {status}\n"
            if tutorial_data.get("video_url"):
                text += f"   📺 Video: {tutorial_data['video_url'][:50]}...\n"
                text += f"   🔘 Button: {tutorial_data.get('button_text', '📺 Tutorial')}\n"
            text += "\n"
        
        text += "<b>💡 How it works:</b>\n"
        text += "• Users see tutorial button on shortlink page\n"
        text += "• Helps users understand how to use shortlinks\n"
        text += "• Reduces support queries\n"
        text += "• Improves user experience"
        
        buttons = []
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status_icon = "✅" if tutorial_data.get("enabled", False) else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Tutorial {i}", callback_data=f"pagemode_tutorial_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        tutorial_data = page_settings.get("shortlink_tutorials", {}).get(f"shortlink{shortlink_num}", {})
        
        text = f"<b>📺 TUTORIAL SETTINGS - Shortlink {shortlink_num}</b>\n\n"
        text += f"<b>📊 Current Status:</b>\n"
        text += f"• Enabled: {'✅ Yes' if tutorial_data.get('enabled', False) else '❌ No'}\n"
        text += f"• Video URL: {tutorial_data.get('video_url', 'Not set')}\n"
        text += f"• Button Text: {tutorial_data.get('button_text', '📺 Tutorial')}\n\n"
        text += f"<b>💡 Tutorial Videos Help:</b>\n"
        text += f"• Show users how to bypass ads\n"
        text += f"• Explain shortlink process\n"
        text += f"• Reduce support queries\n"
        text += f"• Improve user experience"
        
        buttons = []
        if tutorial_data.get("enabled", False):
            buttons.append([InlineKeyboardButton("❌ Disable Tutorial", callback_data=f"pagemode_tutorial_disable_{shortlink_num}")])
            buttons.append([
                InlineKeyboardButton("🔗 Change Video URL", callback_data=f"pagemode_tutorial_url_{shortlink_num}"),
                InlineKeyboardButton("📝 Change Button Text", callback_data=f"pagemode_tutorial_text_{shortlink_num}")
            ])
        else:
            buttons.append([InlineKeyboardButton("✅ Enable Tutorial", callback_data=f"pagemode_tutorial_enable_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_tutorials"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_enable_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await query.message.delete()
        tamil = await bot.send_message(
            chat_id=query.message.chat.id,
            text=f"<b>📺 ENABLE TUTORIAL - Shortlink {shortlink_num}</b>\n\n"
                 f"<b>Step 1:</b> Send your tutorial video URL\n\n"
                 f"<b>📋 Instructions:</b>\n"
                 f"• Use YouTube, Telegram, or any video link\n"
                 f"• Make sure video shows how to use shortlinks\n"
                 f"• Keep video short and clear (2-5 minutes)\n\n"
                 f"<b>💡 Examples:</b>\n"
                 f"• <code>https://youtu.be/abc123</code>\n"
                 f"• <code>https://t.me/channel/123</code>\n\n"
                 f"Send <code>/cancel</code> to cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if url_msg.text == "/cancel":
                await url_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            video_url = url_msg.text.strip()
            await url_msg.delete()
            
            # Ask for button text
            await tamil.edit_text(
                f"<b>📺 TUTORIAL SETUP - Shortlink {shortlink_num}</b>\n\n"
                f"<b>✅ Video URL:</b> <code>{video_url}</code>\n\n"
                f"<b>Step 2:</b> Send button text for tutorial\n\n"
                f"<b>📝 Examples:</b>\n"
                f"• <code>📺 How to Use</code>\n"
                f"• <code>🎓 Tutorial Video</code>\n"
                f"• <code>📖 Guide</code>\n\n"
                f"<b>Default:</b> 📺 Tutorial\n\n"
                f"Send button text or <code>/skip</code> for default:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )
            
            text_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
            if text_msg.text == "/cancel":
                await text_msg.delete()
                return await tamil.edit_text(
                    "<b>❌ Process cancelled!</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
                )
            
            button_text = "📺 Tutorial" if text_msg.text == "/skip" else text_msg.text.strip()
            await text_msg.delete()
            
            # Save tutorial settings
            page_settings = await u_db.get_page_settings(user_id)
            if "shortlink_tutorials" not in page_settings:
                page_settings["shortlink_tutorials"] = {}
            
            page_settings["shortlink_tutorials"][f"shortlink{shortlink_num}"] = {
                "enabled": True,
                "video_url": video_url,
                "button_text": button_text
            }
            
            await u_db.update_page_settings(user_id, page_settings)
            
            await tamil.edit_text(
                f"<b>✅ TUTORIAL ENABLED</b>\n\n"
                f"<b>📺 Shortlink {shortlink_num} Tutorial:</b>\n"
                f"• Video URL: <code>{video_url}</code>\n"
                f"• Button Text: <code>{button_text}</code>\n\n"
                f"<b>🎯 Users will now see a tutorial button on your shortlink page!</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('≺≺ Back to Tutorial Settings', callback_data="pagemode_tutorials")]
                ])
            )
            
        except (asyncio.exceptions.TimeoutError, ListenerTimeout):
            await tamil.edit_text(
                '<b>⏰ Timeout!</b> Process cancelled due to inactivity.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_tutorial_{shortlink_num}")]])
            )

    elif data == "pagemode_button_settings":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        text = "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
        text += "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
        text += "<b>📊 Current Visibility:</b>\n"
        text += f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
        text += f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
        text += f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
        text += "<b>💡 Benefits:</b>\n"
        text += "• Hide buttons you don't need\n"
        text += "• Cleaner page appearance\n"
        text += "• Focus user attention\n"
        text += "• Better mobile experience"
        
        buttons = []
        watch_status = "👁️ Show" if not button_visibility.get('watch', True) else "🙈 Hide"
        download_status = "👁️ Show" if not button_visibility.get('download', True) else "🙈 Hide"
        telegram_status = "👁️ Show" if not button_visibility.get('telegram', True) else "🙈 Hide"
        
        buttons.append([
            InlineKeyboardButton(f"{watch_status} Watch", callback_data="pagemode_toggle_watch"),
            InlineKeyboardButton(f"{download_status} Download", callback_data="pagemode_toggle_download")
        ])
        buttons.append([InlineKeyboardButton(f"{telegram_status} Telegram", callback_data="pagemode_toggle_telegram")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_toggle_"):
        button_type = data.split("_")[-1]
        user_id = query.from_user.id
        
        page_settings = await u_db.get_page_settings(user_id)
        button_visibility = page_settings.get("button_visibility", {"watch": True, "download": True, "telegram": True})
        
        # Toggle the button visibility
        current_status = button_visibility.get(button_type, True)
        button_visibility[button_type] = not current_status
        
        page_settings["button_visibility"] = button_visibility
        await u_db.update_page_settings(user_id, page_settings)
        
        new_status = "visible" if not current_status else "hidden"
        await query.answer(f"{button_type.title()} button is now {new_status}!", show_alert=True)
        
        # Refresh button settings menu
        await query.message.edit_text(
            "<b>🎛️ BUTTON VISIBILITY SETTINGS</b>\n\n"
            "<b>🎯 Control Which Buttons Show on Your Page</b>\n\n"
            "<b>📊 Current Visibility:</b>\n"
            f"• Watch Button: {'✅ Visible' if button_visibility.get('watch', True) else '❌ Hidden'}\n"
            f"• Download Button: {'✅ Visible' if button_visibility.get('download', True) else '❌ Hidden'}\n"
            f"• Telegram Button: {'✅ Visible' if button_visibility.get('telegram', True) else '❌ Hidden'}\n\n"
            "<b>💡 Benefits:</b>\n"
            "• Hide buttons you don't need\n"
            "• Cleaner page appearance\n"
            "• Focus user attention\n"
            "• Better mobile experience",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('watch', True) else '🙈 Hide'} Watch", callback_data="pagemode_toggle_watch"),
                    InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('download', True) else '🙈 Hide'} Download", callback_data="pagemode_toggle_download")
                ],
                [InlineKeyboardButton(f"{'👁️ Show' if not button_visibility.get('telegram', True) else '🙈 Hide'} Telegram", callback_data="pagemode_toggle_telegram")],
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        shortlink_data = await u_db.get_page_shortlinks(user_id)
        current_shortlink = shortlink_data.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>📄 PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Page Mode Shortlinks:</b>\n"
        text += f"• This shortlink will appear as 'Shortlink Set {shortlink_num}' on the page\n"
        text += f"• Users will see 3 buttons: Watch Online, Download, Telegram Storage\n"
        text += f"• Each button uses this shortlink service\n"
        text += f"• Test before saving to ensure it works properly\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure new shortlink URL and API\n"
        text += f"• Test current configuration\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_page_shortlink(user_id, shortlink_num)
        await query.answer(f"Page Mode Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlinks list
        await query.answer("", show_alert=False)
        # Trigger pagemode_shortlinks callback
        from pyrogram.types import CallbackQuery
        mock_query = CallbackQuery(
            id=query.id,
            from_user=query.from_user,
            chat_instance=query.chat_instance,
            data="pagemode_shortlinks",
            message=query.message
        )
        return await cb_handler(bot, mock_query)

    elif data.startswith("pagemode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pagemode{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )

        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_page_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Page Mode Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_shortlink_{shortlink_num}")]])
            )

    elif data == "toggle_verifymode":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show verify mode settings
        text = f"<b>🔐 VERIFY MODE SETTINGS</b>\n\n"
        text += f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n\n"
        text += f"<b>📋 What is Verify Mode?</b>\n"
        text += f"• Progressive shortlink verification system\n"
        text += f"• Users must complete shortlinks before accessing files\n"
        text += f"• Support up to 3 verification shortlinks per day\n"
        text += f"• After completing all verifications, direct access is granted\n"
        text += f"• Verification count resets daily\n\n"
        text += f"<b>🎯 How it works:</b>\n"
        text += f"• User visits shortlink page\n"
        text += f"• First visit: Shortlink 3 (if configured)\n"
        text += f"• Second visit: Shortlink 2 (if configured)\n"
        text += f"• Third visit: Shortlink 1 (if configured)\n"
        text += f"• Fourth+ visits: Direct access to file\n\n"
        text += f"<b>⚙️ Configuration:</b>\n"
        text += f"• Configure verification shortlinks independently\n"
        text += f"• Set custom verification time gaps\n"
        text += f"• Monitor user verification status\n"
        text += f"• Automatic daily reset functionality"
        
        buttons = []
        if new_status:
            buttons.append([InlineKeyboardButton("⚙️ Manage Verify Shortlinks", callback_data="verifymode_shortlinks")])
            buttons.append([InlineKeyboardButton("⏱️ Time Settings", callback_data="verifymode_time_settings")])
        buttons.append([InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Verify Mode", callback_data="toggle_verifymode")])
        buttons.append([InlineKeyboardButton("≺≺ Back to Settings", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 VERIFY MODE SHORTLINKS</b>\n\n"
        
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"<b>Verify Shortlink {i}:</b> {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Verification Flow:</b>\n"
        text += "• Shortlink 3: First verification of the day\n"
        text += "• Shortlink 2: Second verification of the day\n"
        text += "• Shortlink 1: Third verification of the day\n"
        text += "• Direct Access: After 3 verifications\n\n"
        text += "<b>💡 Tips:</b>\n"
        text += "• Configure all 3 shortlinks for maximum monetization\n"
        text += "• Test shortlinks before saving\n"
        text += "• Users get direct access after completing all verifications"
        
        buttons = []
        for i in range(1, 4):
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i}", callback_data=f"verifymode_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("verifymode_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"verifymode_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"verifymode_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data == "verifymode_time_settings":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        verification_status = await u_db.get_verification_status(user_id)
        
        # Convert seconds to hours for display
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours ({verify_time_gap} seconds)\n\n"
        text += f"<b>📊 Today's Status:</b>\n"
        text += f"• Verifications completed: {verification_status.get('verify_count_today', 0)}\n"
        text += f"• Last reset: {verification_status.get('last_reset_date', 'Never')}\n\n"
        text += f"<b>📋 How Time Gap Works:</b>\n"
        text += f"• Controls minimum time between verification requirements\n"
        text += f"• Default: 4 hours (recommended)\n"
        text += f"• Users can access files directly within time gap after verification\n"
        text += f"• Count resets daily at midnight\n\n"
        text += f"<b>💡 Recommended Settings:</b>\n"
        text += f"• 1 hour: High monetization, frequent verification\n"
        text += f"• 4 hours: Balanced approach (recommended)\n"
        text += f"• 8 hours: User-friendly, less frequent verification\n"
        text += f"• 24 hours: One verification per day maximum"
        
        buttons = []
        time_options = [
            ("1 Hour", 3600),
            ("4 Hours", 14400),
            ("8 Hours", 28800),
            ("24 Hours", 86400)
        ]
        
        for label, seconds in time_options:
            current_marker = "✅ " if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{current_marker}{label}", callback_data=f"set_verify_time_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_verifymode"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("set_verify_time_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Refresh the time settings page
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh Settings", callback_data="verifymode_time_settings")]
        ]))

    elif data.startswith("verifymode_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        # Step 2: Get API
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter your API key from the shortener service\n"
            f"• Check your shortener dashboard for API key\n"
            f"• Keep it secure and don't share publicly\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text(
            f"<b>🔍 TESTING VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>URL:</b> {shortener_url}\n"
            f"<b>API:</b> {shortener_api[:20]}...\n\n"
            f"⏳ Testing shortlink configuration...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⏳ Testing...', callback_data="testing")]])
        )
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"verifymode_shortlink_{shortlink_num}")]])
            )

    elif data.startswith("verifymode_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Redirect back to shortlink configuration
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        text = f"<b>🔐 VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> ❌ Not configured\n\n"
        
        # Explain the verification order
        if shortlink_num == "1":
            verification_order = "Third verification"
            description = "Used when user has already completed 2 verifications today"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used when user has already completed 1 verification today"
        else:  # shortlink_num == "3"
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"verifymode_set_{shortlink_num}")])
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verifymode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    # Page Mode Verify Callbacks
    elif data == "pagemode_toggle_verify":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Show page mode settings directly without using mock query
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_verify_shortlinks":
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔐 PAGE MODE VERIFY SHORTLINKS</b>\n\n"
        text += "<b>📋 Verification Logic:</b>\n"
        text += "• <b>First Visit:</b> User completes Verify Shortlink 3\n"
        text += "• <b>Second Visit:</b> User completes Verify Shortlink 2\n"
        text += "• <b>Third Visit:</b> User completes Verify Shortlink 1\n"
        text += "• <b>Fourth+ Visits:</b> Direct access to file\n"
        text += "• Verification count resets daily\n\n"
        
        for i in range(3, 0, -1):  # 3, 2, 1 order
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            visit_order = ["Third", "Second", "First"][3-i]
            text += f"<b>Verify Shortlink {i}:</b> {status} ({visit_order} visit)\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api'][:20]}...</code>\n"
            text += "\n"
        
        text += "<b>📝 Management:</b>\n"
        text += "• Configure each verify shortlink independently\n"
        text += "• Test shortlinks before saving\n"
        text += "• Remove shortlinks if not needed\n"
        text += "• Users progress through verification levels daily"
        
        buttons = []
        for i in range(3, 0, -1):  # 3, 2, 1 order for display
            shortlink_data = verify_shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status_icon = "✅" if shortlink_data["url"] and shortlink_data["api"] else "➕"
            visit_order = ["Third", "Second", "First"][3-i]
            buttons.append([InlineKeyboardButton(f"{status_icon} Verify Shortlink {i} ({visit_order} visit)", callback_data=f"pagemode_verify_shortlink_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_shortlink_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        verify_shortlinks = await u_db.get_verify_shortlinks(user_id)
        current_shortlink = verify_shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})
        
        # Determine verification order
        if shortlink_num == "3":
            verification_order = "First verification"
            description = "Used for the first verification attempt of the day"
        elif shortlink_num == "2":
            verification_order = "Second verification"
            description = "Used for the second verification attempt of the day"
        else:  # shortlink_num == "1"
            verification_order = "Third verification"
            description = "Used for the third verification attempt of the day"
        
        text = f"<b>🔐 PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
        text += f"<b>Current Status:</b> {'✅ Active' if current_shortlink['url'] and current_shortlink['api'] else '❌ Not configured'}\n\n"
        
        if current_shortlink["url"] and current_shortlink["api"]:
            text += f"<b>URL:</b> <code>{current_shortlink['url']}</code>\n"
            text += f"<b>API:</b> <code>{current_shortlink['api'][:20]}...</code>\n\n"
        
        text += f"<b>📋 About Verify Shortlink {shortlink_num}:</b>\n"
        text += f"• {verification_order} of the day\n"
        text += f"• {description}\n"
        text += f"• Users must complete this shortlink to proceed\n"
        text += f"• After completion, moves to next verification level\n"
        text += f"• Integrates with page mode for seamless experience\n\n"
        text += f"<b>⚙️ Management Options:</b>\n"
        text += f"• Configure shortlink URL and API\n"
        text += f"• Test shortlink before saving\n"
        text += f"• Remove shortlink if not needed"
        
        buttons = []
        if current_shortlink["url"] and current_shortlink["api"]:
            buttons.append([InlineKeyboardButton("🔄 Reconfigure", callback_data=f"pagemode_verify_set_{shortlink_num}"), 
                           InlineKeyboardButton("🗑️ Remove", callback_data=f"pagemode_verify_remove_{shortlink_num}")])
        else:
            buttons.append([InlineKeyboardButton("➕ Configure Shortlink", callback_data=f"pagemode_verify_set_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_remove_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        await u_db.remove_verify_shortlink(user_id, shortlink_num)
        await query.answer(f"Verify Shortlink {shortlink_num} removed successfully!", show_alert=True)
        
        # Show verify shortlinks page directly
        await show_pagemode_verify_shortlinks(bot, query)

    elif data.startswith("pagemode_verify_set_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        
        # Determine verification order for display
        if shortlink_num == "3":
            verification_order = "first verification"
            order_desc = "Users encounter this shortlink on their first visit of the day"
        elif shortlink_num == "2":
            verification_order = "second verification"
            order_desc = "Users encounter this shortlink on their second visit of the day"
        else:  # shortlink_num == "1"
            verification_order = "third verification"
            order_desc = "Users encounter this shortlink on their third visit of the day"
        
        tamil = await query.message.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>📝 Description:</b> {order_desc}\n\n"
            f"<b>Step 1:</b> Send your shortener URL\n"
            f"<b>Example:</b> <code>short.com</code> or <code>url.short.com</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Enter only the domain name\n"
            f"• Don't include http:// or https://\n"
            f"• Make sure the service supports API\n\n"
            f"<b>⚡ Alternative:</b> Use command <code>/pageverify{shortlink_num} url api</code>\n\n"
            f"Send <code>/cancel</code> to cancel this process.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('❌ Cancel', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")],
                [InlineKeyboardButton("📚 Use Command Instead", callback_data="pagemode_verify_commands_help")]
            ])
        )
        
        try:
            url_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if url_msg.text == "/cancel":
            await url_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_url = url_msg.text.strip()
        await url_msg.delete()
        
        await tamil.edit_text(
            f"<b>⚙️ CONFIGURE PAGE MODE VERIFY SHORTLINK {shortlink_num}</b>\n\n"
            f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
            f"<b>Step 2:</b> Send your API key\n"
            f"<b>URL:</b> <code>{shortener_url}</code>\n\n"
            f"<b>📝 Instructions:</b>\n"
            f"• Get your API key from {shortener_url}\n"
            f"• Copy and paste the complete API key\n"
            f"• Don't share your API key with others\n\n"
            f"Send <code>/cancel</code> to cancel this process."
        )
        
        try:
            api_msg = await bot.listen(chat_id=query.from_user.id, timeout=60)
        except (asyncio.TimeoutError, ListenerTimeout):
            return await tamil.edit_text(
                "<b>⏰ Timeout!</b> Process cancelled due to inactivity.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        if api_msg.text == "/cancel":
            await api_msg.delete()
            return await tamil.edit_text(
                "<b>❌ Process cancelled!</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )
        
        shortener_api = api_msg.text.strip()
        await api_msg.delete()
        
        # Test the shortlink
        await tamil.edit_text("<b>🔄 Testing verify shortlink configuration...</b>")
        
        try:
            from shortzy import Shortzy
            shortzy = Shortzy(shortener_api, shortener_url)
            test_link = await shortzy.convert("https://telegram.me/MrAK_LinkZzz")
            
            if test_link:
                # Save the verify shortlink
                await u_db.set_verify_shortlink(user_id, shortlink_num, shortener_url, shortener_api)
                await tamil.edit_text(
                    f"<b>✅ Verify Shortlink {shortlink_num} configured successfully!</b>\n\n"
                    f"<b>🔐 Verification Order:</b> {verification_order.title()}\n"
                    f"<b>URL:</b> {shortener_url}\n"
                    f"<b>API:</b> {shortener_api[:20]}...\n\n"
                    f"<b>Test Result:</b> {test_link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
                )
            else:
                raise Exception("Failed to generate test link")
                
        except Exception as e:
            await tamil.edit_text(
                f"<b>❌ Verify shortlink test failed!</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"Please check your URL and API key.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('≺≺ Back', callback_data=f"pagemode_verify_shortlink_{shortlink_num}")]])
            )

    elif data == "pagemode_verify_time":
        user_id = query.from_user.id
        verify_time_gap = await u_db.get_verify_time_gap(user_id)
        hours = verify_time_gap // 3600
        
        text = f"<b>⏱️ PAGE MODE VERIFY TIME SETTINGS</b>\n\n"
        text += f"<b>Current Time Gap:</b> {hours} hours\n\n"
        text += f"<b>📋 What is Verify Time Gap?</b>\n"
        text += f"• Minimum time between verification requirements\n"
        text += f"• Prevents excessive verification requests\n"
        text += f"• Users can access files directly within this time\n"
        text += f"• Integrates with daily verification count reset\n\n"
        text += f"<b>🎯 How it works in Page Mode:</b>\n"
        text += f"• User completes verification shortlinks\n"
        text += f"• Time gap prevents immediate re-verification\n"
        text += f"• Balances security with user experience\n"
        text += f"• Works with progressive verification system\n\n"
        text += f"<b>⚙️ Choose your preferred time gap:</b>"
        
        buttons = []
        time_options = [
            (3600, "1 Hour"),
            (7200, "2 Hours"), 
            (14400, "4 Hours"),
            (21600, "6 Hours"),
            (28800, "8 Hours"),
            (43200, "12 Hours"),
            (86400, "24 Hours")
        ]
        
        for seconds, label in time_options:
            current_indicator = " ✅" if seconds == verify_time_gap else ""
            buttons.append([InlineKeyboardButton(f"{label}{current_indicator}", callback_data=f"pagemode_verify_time_set_{seconds}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_verify_time_set_"):
        time_gap = int(data.split("_")[-1])
        user_id = query.from_user.id
        await u_db.set_verify_time_gap(user_id, time_gap)
        
        hours = time_gap // 3600
        await query.answer(f"Verify time gap set to {hours} hours!", show_alert=True)
        
        # Show page mode settings directly
        await show_page_mode_settings(bot, query)

    elif data == "pagemode_info":
        await query.answer(
            "ℹ️ Please enable Page Mode first to access Verify settings!\n\n"
            "Page Mode is required for the verification system to work properly.",
            show_alert=True
        )

    elif data == "pagemode_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE COMMANDS HELP</b>\n\n"
            f"<b>🎯 Regular Page Mode Shortlinks:</b>\n\n"
            f"<b>1️⃣ Page Mode Shortlink 1:</b>\n"
            f"<code>/pagemode1 shortener_url api_key</code>\n"
            f"• Primary shortlink for page mode\n\n"
            f"<b>2️⃣ Page Mode Shortlink 2:</b>\n"
            f"<code>/pagemode2 shortener_url api_key</code>\n"
            f"• Secondary shortlink for page mode\n\n"
            f"<b>3️⃣ Page Mode Shortlink 3:</b>\n"
            f"<code>/pagemode3 shortener_url api_key</code>\n"
            f"• Tertiary shortlink for page mode\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pagemode1 short.com abc123api</code>\n"
            f"<code>/pagemode2 tiny.url def456api</code>\n"
            f"<code>/pagemode3 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pagemode1 off</code> - Remove shortlink 1\n"
            f"<code>/pagemode2 off</code> - Remove shortlink 2\n"
            f"<code>/pagemode3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "pagemode_verify_commands_help":
        await query.message.edit_text(
            f"<b>📚 PAGE MODE VERIFY COMMANDS HELP</b>\n\n"
            f"<b>🎯 Quick Configuration Commands:</b>\n\n"
            f"<b>1️⃣ First Verification (Shortlink 3):</b>\n"
            f"<code>/pageverify3 shortener_url api_key</code>\n"
            f"• Users see this on their first visit of the day\n\n"
            f"<b>2️⃣ Second Verification (Shortlink 2):</b>\n"
            f"<code>/pageverify2 shortener_url api_key</code>\n"
            f"• Users see this on their second visit of the day\n\n"
            f"<b>3️⃣ Third Verification (Shortlink 1):</b>\n"
            f"<code>/pageverify1 shortener_url api_key</code>\n"
            f"• Users see this on their third visit of the day\n\n"
            f"<b>📋 Example Setup:</b>\n"
            f"<code>/pageverify3 short.com abc123api</code>\n"
            f"<code>/pageverify2 tiny.url def456api</code>\n"
            f"<code>/pageverify1 link.short ghi789api</code>\n\n"
            f"<b>🔧 Management Commands:</b>\n"
            f"<code>/pageverify on/off</code> - Enable/disable verify mode\n"
            f"<code>/pageverify</code> - Show current status\n"
            f"<code>/pageverify1 off</code> - Remove shortlink 1\n"
            f"<code>/pageverify2 off</code> - Remove shortlink 2\n"
            f"<code>/pageverify3 off</code> - Remove shortlink 3\n\n"
            f"<b>✅ Benefits:</b>\n"
            f"• Instant configuration with automatic testing\n"
            f"• Clear success/error feedback\n"
            f"• Built-in validation and error handling\n"
            f"• No timeout issues or interactive prompts",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("≺≺ Back", callback_data="pagemode_verify_shortlinks"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data.startswith("pagemode_tutorials"):
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📺 TUTORIAL SETTINGS</b>\n\n"
        text += "<b>🎯 Add Tutorial Videos for Each Shortlink</b>\n\n"
        text += "<b>📊 Current Status:</b>\n"
        
        tutorials = page_settings.get("shortlink_tutorials", {})
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status = "✅ Enabled" if tutorial_data.get("enabled", False) else "❌ Disabled"
            text += f"• Shortlink {i}: {status}\n"
            if tutorial_data.get("video_url"):
                text += f"   📺 Video: {tutorial_data['video_url'][:50]}...\n"
                text += f"   🔘 Button: {tutorial_data.get('button_text', '📺 Tutorial')}\n"
            text += "\n"
        
        text += "<b>💡 How it works:</b>\n"
        text += "• Users see tutorial button on shortlink page\n"
        text += "• Helps users understand how to use shortlinks\n"
        text += "• Reduces support queries\n"
        text += "• Improves user experience"
        
        buttons = []
        for i in range(1, 4):
            tutorial_data = tutorials.get(f"shortlink{i}", {})
            status_icon = "✅" if tutorial_data.get("enabled", False) else "➕"
            buttons.append([InlineKeyboardButton(f"{status_icon} Tutorial {i}", callback_data=f"pagemode_tutorial_{i}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_shortlinks"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

    elif data.startswith("pagemode_tutorial_"):
        shortlink_num = data.split("_")[-1]
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        tutorial_data = page_settings.get("shortlink_tutorials", {}).get(f"shortlink{shortlink_num}", {})
        
        text = f"<b>📺 TUTORIAL SETTINGS - Shortlink {shortlink_num}</b>\n\n"
        text += f"<b>📊 Current Status:</b>\n"
        text += f"• Enabled: {'✅ Yes' if tutorial_data.get('enabled', False) else '❌ No'}\n"
        text += f"• Video URL: {tutorial_data.get('video_url', 'Not set')}\n"
        text += f"• Button Text: {tutorial_data.get('button_text', '📺 Tutorial')}\n\n"
        text += f"<b>💡 Tutorial Videos Help:</b>\n"
        text += f"• Show users how to bypass ads\n"
        text += f"• Explain shortlink process\n"
        text += f"• Reduce support queries\n"
        text += f"• Improve user experience"
        
        buttons = []
        if tutorial_data.get("enabled", False):
            buttons.append([InlineKeyboardButton("❌ Disable Tutorial", callback_data=f"pagemode_tutorial_disable_{shortlink_num}")])
            buttons.append([
                InlineKeyboardButton("🔗 Change Video URL", callback_data=f"pagemode_tutorial_url_{shortlink_num}"),
                InlineKeyboardButton("📝 Change Button Text", callback_data=f"pagemode_tutorial_text_{shortlink_num}")
            ])
        else:
            buttons.append([InlineKeyboardButton("✅ Enable Tutorial", callback_data=f"pagemode_tutorial_enable_{shortlink_num}")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="pagemode_tutorials"), InlineKeyboardButton("Close", callback_data="close")])
        
        await safe_edit_message(query, text, InlineKeyboardMarkup(buttons), disable_web_page_preview=True)