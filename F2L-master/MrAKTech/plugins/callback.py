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
            reply_markup=BUTTON.HELP_BUTTONS
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

    elif data in ['settings', 'toggle_mode', 'storage_mode']:
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
        auto_extract = userxdb.get('auto_extract', True)
        buttons.append([InlineKeyboardButton(
            "✅ Auto Extract" if auto_extract else "❌ Auto Extract",
            callback_data="toggle_extract"
        )])
        # Add linkmode button
        linkmode_status = userxdb.get("linkmode", False)
        buttons.append([InlineKeyboardButton(
            "✅ Link Mode" if linkmode_status else "❌ Link Mode",
            callback_data="toggle_linkmode"
        )])
        
        # Add page mode button
        page_mode_status = userxdb.get("page_mode", False)
        buttons.append([InlineKeyboardButton(
            "✅ Page Mode" if page_mode_status else "❌ Page Mode",
            callback_data="page_mode_settings"
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
                                             AUTO_EXTRACT="✅ Enabled" if userxdb.get("auto_extract", True) else "❌ Disabled",
                                             LINKMODE="✅ Enabled" if userxdb.get("linkmode", False) else "❌ Disabled",
                                             PAGEMODE="✅ Enabled" if userxdb.get("page_mode", False) else "❌ Disabled"),
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
        buttons.append([InlineKeyboardButton('📤 Upload mode', callback_data="toggle_mode"),
                        InlineKeyboardButton("Links", callback_data="toggle_mode")])
        buttons.append([InlineKeyboardButton('Close', callback_data="close")])
        await query.message.edit_text(
            text=tamilxd.SETTINGS_TXT.format(CAPTION="❌ Not Exists",
                                             URLX="❌ Not Exists",
                                             APIX="❌ Not Exists",
                                             METHODX="Links",
                                             AUTO_EXTRACT="✅ Enabled",
                                             LINKMODE="❌ Disabled"),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)

    elif data == "custom_caption":
        buttons = []
        if userxdb['caption'] is not None:
            buttons.append([InlineKeyboardButton('Show caption', callback_data="show_caption")])
            buttons.append([InlineKeyboardButton('Default caption', callback_data="delete_caption"),
                            InlineKeyboardButton('Change caption', callback_data="add_caption")])
        else:
            buttons.append([InlineKeyboardButton('Set caption', callback_data="add_caption")])
        buttons.append([InlineKeyboardButton('≺≺ Back', callback_data="settings"),
                        InlineKeyboardButton('Close', callback_data="close")])
        await query.message.edit_text(
            text=tamilxd.CUSTOM_CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "custom_shortner":
        buttons = []
        if userxdb['shortener_url'] and userxdb['shortener_api'] is not None:
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
            reply_markup=InlineKeyboardMarkup(buttons))

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
• <code>{web_link}</code> - Page mode web link
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
                caption.text.format(file_name='', file_size='', caption='', download_link='', stream_link='', storage_link='', quality='', season='', episode='', web_link='')
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
        except asyncio.exceptions.TimeoutError:
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

    elif data == "toggle_extract":
        user_id = query.from_user.id
        auto_extract = await u_db.get_auto_extract(user_id)
        new_status = not auto_extract
        await u_db.set_auto_extract(user_id, new_status)
        
        buttons = []
        buttons.append([
            InlineKeyboardButton(
                "✅ Enable Auto Extract" if not new_status else "❌ Disable Auto Extract",
                callback_data="toggle_extract"
            )
        ])
        buttons.append([InlineKeyboardButton("Close", callback_data="close")])
        
        status = "Enabled" if new_status else "Disabled"
        await query.message.edit_text(
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
            reply_markup=InlineKeyboardMarkup(buttons),
        )

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
        text += "• <code>{file_size}</code>, <code>{quality}</code>, <code>{season}</code>, <code>{episode}</code>"
        
        buttons = []
        buttons.append([InlineKeyboardButton(f"📝 Caption 1 {'✅' if caption1 else '❌'}", callback_data="linkmode_caption_1")])
        buttons.append([InlineKeyboardButton(f"📝 Caption 2 {'✅' if caption2 else '❌'}", callback_data="linkmode_caption_2")])
        buttons.append([InlineKeyboardButton(f"📝 Caption 3 {'✅' if caption3 else '❌'}", callback_data="linkmode_caption_3")])
        
        buttons.append([InlineKeyboardButton("👁️ View Default Caption", callback_data="view_default_linkmode_caption")])
        
        if caption1 or caption2 or caption3:
            buttons.append([InlineKeyboardButton(f"🎯 Active: Caption {active_caption or 'None'}", callback_data="select_active_caption")])
        
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_linkmode"), InlineKeyboardButton("Close", callback_data="close")])
        
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
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="toggle_linkmode"), InlineKeyboardButton("Close", callback_data="close")])
        
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

    # Page Mode Settings Handlers
    elif data == "page_mode_settings":
        user_id = query.from_user.id
        page_mode_status = await u_db.get_page_mode(user_id)
        verify_mode_status = await u_db.get_verify_mode(user_id)
        
        await query.message.edit_text(
            text="<b>📄 PAGE MODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if page_mode_status else '❌ Disabled'}\n"
                 f"<b>Verify Mode:</b> {'✅ Enabled' if verify_mode_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Page Mode?</b>\n"
                 f"• Create custom web pages for file downloads\n"
                 f"• Add multiple shortlinks with custom buttons\n"
                 f"• Support for tutorial videos and custom buttons\n"
                 f"• Use {{web_link}} in captions to link to the page\n"
                 f"• Verify mode for step-by-step user verification\n\n"
                 f"<b>🎯 Features:</b>\n"
                 f"• Dynamic button visibility controls\n"
                 f"• Custom button names and icons\n"
                 f"• Up to 3 shortlinks per mode\n"
                 f"• Tutorial video integration\n"
                 f"• Custom button support (up to 5)\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if page_mode_status else '✅ Enable'} Page Mode", callback_data="toggle_page_mode")],
                [InlineKeyboardButton("🔗 Page Shortlinks", callback_data="page_shortlinks_menu")],
                [InlineKeyboardButton("⚙️ Page Settings", callback_data="page_settings_menu")],
                [InlineKeyboardButton("🔐 Verify Mode", callback_data="verify_mode_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "toggle_page_mode":
        user_id = query.from_user.id
        page_mode_status = await u_db.get_page_mode(user_id)
        new_status = not page_mode_status
        await u_db.set_page_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Page mode has been {status_text}!", show_alert=True)
        
        # Refresh the page mode menu
        verify_mode_status = await u_db.get_verify_mode(user_id)
        await query.message.edit_text(
            text="<b>📄 PAGE MODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n"
                 f"<b>Verify Mode:</b> {'✅ Enabled' if verify_mode_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Page Mode?</b>\n"
                 f"• Create custom web pages for file downloads\n"
                 f"• Add multiple shortlinks with custom buttons\n"
                 f"• Support for tutorial videos and custom buttons\n"
                 f"• Use {{web_link}} in captions to link to the page\n"
                 f"• Verify mode for step-by-step user verification\n\n"
                 f"<b>🎯 Features:</b>\n"
                 f"• Dynamic button visibility controls\n"
                 f"• Custom button names and icons\n"
                 f"• Up to 3 shortlinks per mode\n"
                 f"• Tutorial video integration\n"
                 f"• Custom button support (up to 5)\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Page Mode", callback_data="toggle_page_mode")],
                [InlineKeyboardButton("🔗 Page Shortlinks", callback_data="page_shortlinks_menu")],
                [InlineKeyboardButton("⚙️ Page Settings", callback_data="page_settings_menu")],
                [InlineKeyboardButton("🔐 Verify Mode", callback_data="verify_mode_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "page_shortlinks_menu":
        user_id = query.from_user.id
        shortlinks = await u_db.get_page_shortlinks(user_id)
        
        text = "<b>🔗 PAGE MODE SHORTLINKS</b>\n\n"
        
        for i in range(1, 4):
            shortlink_data = shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"<b>Shortlink {i}:</b> {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api']}</code>\n"
            text += "\n"
        
        text += "<b>📝 Commands:</b>\n"
        text += "• <code>/pageshortlink1 {url} {api}</code>\n"
        text += "• <code>/pageshortlink2 {url} {api}</code>\n"
        text += "• <code>/pageshortlink3 {url} {api}</code>\n"
        text += "• <code>/pageshortlink1 off</code> (to disable)\n"
        
        buttons = []
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="page_mode_settings"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "verify_mode_menu":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        
        await query.message.edit_text(
            text="<b>🔐 VERIFY MODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if verify_mode_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Verify Mode?</b>\n"
                 f"• Step-by-step verification process\n"
                 f"• Users complete shortlinks in sequence\n"
                 f"• 24-hour reset cycle for verifications\n"
                 f"• Customizable time gaps between steps\n"
                 f"• Tutorial support for each verification\n\n"
                 f"<b>🎯 Process:</b>\n"
                 f"• Step 1: Complete shortlink 3\n"
                 f"• Step 2: Complete shortlink 2\n"
                 f"• Step 3: Complete shortlink 1\n"
                 f"• Final: Direct access to files\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if verify_mode_status else '✅ Enable'} Verify Mode", callback_data="toggle_verify_mode")],
                [InlineKeyboardButton("🔗 Verify Shortlinks", callback_data="verify_shortlinks_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="page_mode_settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "toggle_verify_mode":
        user_id = query.from_user.id
        verify_mode_status = await u_db.get_verify_mode(user_id)
        new_status = not verify_mode_status
        await u_db.set_verify_mode(user_id, new_status)
        
        status_text = "enabled" if new_status else "disabled"
        await query.answer(f"Verify mode has been {status_text}!", show_alert=True)
        
        # Refresh the verify mode menu
        await query.message.edit_text(
            text="<b>🔐 VERIFY MODE SETTINGS</b>\n\n"
                 f"<b>Status:</b> {'✅ Enabled' if new_status else '❌ Disabled'}\n\n"
                 f"<b>📋 What is Verify Mode?</b>\n"
                 f"• Step-by-step verification process\n"
                 f"• Users complete shortlinks in sequence\n"
                 f"• 24-hour reset cycle for verifications\n"
                 f"• Customizable time gaps between steps\n"
                 f"• Tutorial support for each verification\n\n"
                 f"<b>🎯 Process:</b>\n"
                 f"• Step 1: Complete shortlink 3\n"
                 f"• Step 2: Complete shortlink 2\n"
                 f"• Step 3: Complete shortlink 1\n"
                 f"• Final: Direct access to files\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{'❌ Disable' if new_status else '✅ Enable'} Verify Mode", callback_data="toggle_verify_mode")],
                [InlineKeyboardButton("🔗 Verify Shortlinks", callback_data="verify_shortlinks_menu")],
                [InlineKeyboardButton("≺≺ Back", callback_data="page_mode_settings"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            disable_web_page_preview=True
        )

    elif data == "verify_shortlinks_menu":
        user_id = query.from_user.id
        shortlinks = await u_db.get_verify_shortlinks(user_id)
        
        text = "<b>🔗 VERIFY MODE SHORTLINKS</b>\n\n"
        
        for i in range(1, 4):
            shortlink_data = shortlinks.get(f"shortlink{i}", {"url": None, "api": None})
            status = "✅ Active" if shortlink_data["url"] and shortlink_data["api"] else "❌ Not set"
            text += f"<b>Verify Shortlink {i}:</b> {status}\n"
            if shortlink_data["url"]:
                text += f"   • URL: <code>{shortlink_data['url']}</code>\n"
                text += f"   • API: <code>{shortlink_data['api']}</code>\n"
            text += "\n"
        
        text += "<b>📝 Commands:</b>\n"
        text += "• <code>/verifyshortlink1 {url} {api}</code>\n"
        text += "• <code>/verifyshortlink2 {url} {api}</code>\n"
        text += "• <code>/verifyshortlink3 {url} {api}</code>\n"
        text += "• <code>/verifyshortlink1 off</code> (to disable)\n"
        
        buttons = []
        buttons.append([InlineKeyboardButton("≺≺ Back", callback_data="verify_mode_menu"), InlineKeyboardButton("Close", callback_data="close")])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "page_settings_menu":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>⚙️ PAGE SETTINGS</b>\n\n"
        text += "<b>🔘 Button Visibility:</b>\n"
        text += f"• Watch: {'✅ Visible' if page_settings['button_visibility']['watch'] else '❌ Hidden'}\n"
        text += f"• Download: {'✅ Visible' if page_settings['button_visibility']['download'] else '❌ Hidden'}\n"
        text += f"• Telegram: {'✅ Visible' if page_settings['button_visibility']['telegram'] else '❌ Hidden'}\n\n"
        
        text += "<b>📝 Button Names:</b>\n"
        text += f"• Watch: <code>{page_settings['button_names']['watch']}</code>\n"
        text += f"• Download: <code>{page_settings['button_names']['download']}</code>\n"
        text += f"• Telegram: <code>{page_settings['button_names']['telegram']}</code>\n\n"
        
        custom_buttons_count = len(page_settings.get('custom_buttons', []))
        text += f"<b>⭐ Custom Buttons:</b> {custom_buttons_count}/5\n\n"
        
        text += "<b>📺 Tutorial Settings:</b>\n"
        for i in range(1, 4):
            tutorial = page_settings['shortlink_tutorials'].get(f'shortlink{i}', {})
            enabled = tutorial.get('enabled', False)
            text += f"• Shortlink {i}: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
        
        buttons = [
            [InlineKeyboardButton("🔘 Button Visibility", callback_data="button_visibility_menu")],
            [InlineKeyboardButton("📝 Button Names", callback_data="button_names_menu")],
            [InlineKeyboardButton("⭐ Custom Buttons", callback_data="custom_buttons_menu")],
            [InlineKeyboardButton("📺 Tutorial Settings", callback_data="tutorial_settings_menu")],
            [InlineKeyboardButton("≺≺ Back", callback_data="page_mode_settings"), InlineKeyboardButton("Close", callback_data="close")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "button_visibility_menu":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        watch_visible = page_settings['button_visibility']['watch']
        download_visible = page_settings['button_visibility']['download']
        telegram_visible = page_settings['button_visibility']['telegram']
        
        buttons = [
            [InlineKeyboardButton(f"🎮 Watch: {'✅ Show' if watch_visible else '❌ Hide'}", callback_data="toggle_watch_visibility")],
            [InlineKeyboardButton(f"📥 Download: {'✅ Show' if download_visible else '❌ Hide'}", callback_data="toggle_download_visibility")],
            [InlineKeyboardButton(f"📱 Telegram: {'✅ Show' if telegram_visible else '❌ Hide'}", callback_data="toggle_telegram_visibility")],
            [InlineKeyboardButton("≺≺ Back", callback_data="page_settings_menu")]
        ]
        
        await query.message.edit_text(
            "<b>🔘 BUTTON VISIBILITY SETTINGS</b>\n\n"
            "Toggle which buttons appear on your shortlink pages:\n\n"
            f"🎮 <b>Watch Button:</b> {'✅ Visible' if watch_visible else '❌ Hidden'}\n"
            f"📥 <b>Download Button:</b> {'✅ Visible' if download_visible else '❌ Hidden'}\n"
            f"📱 <b>Telegram Button:</b> {'✅ Visible' if telegram_visible else '❌ Hidden'}\n",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("toggle_") and data.endswith("_visibility"):
        user_id = query.from_user.id
        button_type = data.replace("toggle_", "").replace("_visibility", "")
        
        page_settings = await u_db.get_page_settings(user_id)
        current_value = page_settings['button_visibility'][button_type]
        new_value = not current_value
        
        page_settings['button_visibility'][button_type] = new_value
        await u_db.update_page_settings(user_id, page_settings)
        
        await query.answer(f"{button_type.title()} button {'shown' if new_value else 'hidden'}!", show_alert=True)
        
        # Refresh the visibility menu
        watch_visible = page_settings['button_visibility']['watch']
        download_visible = page_settings['button_visibility']['download']
        telegram_visible = page_settings['button_visibility']['telegram']
        
        buttons = [
            [InlineKeyboardButton(f"🎮 Watch: {'✅ Show' if watch_visible else '❌ Hide'}", callback_data="toggle_watch_visibility")],
            [InlineKeyboardButton(f"📥 Download: {'✅ Show' if download_visible else '❌ Hide'}", callback_data="toggle_download_visibility")],
            [InlineKeyboardButton(f"📱 Telegram: {'✅ Show' if telegram_visible else '❌ Hide'}", callback_data="toggle_telegram_visibility")],
            [InlineKeyboardButton("≺≺ Back", callback_data="page_settings_menu")]
        ]
        
        await query.message.edit_text(
            "<b>🔘 BUTTON VISIBILITY SETTINGS</b>\n\n"
            "Toggle which buttons appear on your shortlink pages:\n\n"
            f"🎮 <b>Watch Button:</b> {'✅ Visible' if watch_visible else '❌ Hidden'}\n"
            f"📥 <b>Download Button:</b> {'✅ Visible' if download_visible else '❌ Hidden'}\n"
            f"📱 <b>Telegram Button:</b> {'✅ Visible' if telegram_visible else '❌ Hidden'}\n",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "button_names_menu":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📝 BUTTON NAMES SETTINGS</b>\n\n"
        text += "Customize the text that appears on your shortlink page buttons:\n\n"
        text += f"🎮 <b>Watch Button:</b> <code>{page_settings['button_names']['watch']}</code>\n"
        text += f"📥 <b>Download Button:</b> <code>{page_settings['button_names']['download']}</code>\n"
        text += f"📱 <b>Telegram Button:</b> <code>{page_settings['button_names']['telegram']}</code>\n\n"
        text += "<b>💡 To change button names, use these commands:</b>\n"
        text += "• <code>/watchbuttonname Your Text</code>\n"
        text += "• <code>/downloadbuttonname Your Text</code>\n"
        text += "• <code>/telegrambuttonname Your Text</code>"
        
        buttons = [
            [InlineKeyboardButton("≺≺ Back", callback_data="page_settings_menu"), InlineKeyboardButton("Close", callback_data="close")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "custom_buttons_menu":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        custom_buttons = page_settings.get('custom_buttons', [])
        
        text = "<b>⭐ CUSTOM BUTTONS SETTINGS</b>\n\n"
        text += f"You can add up to 5 custom buttons to your shortlink pages.\n"
        text += f"<b>Current buttons:</b> {len(custom_buttons)}/5\n\n"
        
        if custom_buttons:
            for i, btn in enumerate(custom_buttons, 1):
                text += f"<b>{i}.</b> {btn['name']} → <code>{btn['url']}</code>\n"
        else:
            text += "<i>No custom buttons configured yet.</i>\n"
        
        text += "\n<b>💡 To manage custom buttons, use these commands:</b>\n"
        text += "• <code>/addcustombutton Name | URL</code>\n"
        text += "• <code>/removecustombutton Number</code>\n"
        text += "• <code>/listcustombuttons</code>\n\n"
        text += "<b>Example:</b> <code>/addcustombutton Join Channel | https://t.me/your_channel</code>"
        
        buttons = [
            [InlineKeyboardButton("≺≺ Back", callback_data="page_settings_menu"), InlineKeyboardButton("Close", callback_data="close")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    elif data == "tutorial_settings_menu":
        user_id = query.from_user.id
        page_settings = await u_db.get_page_settings(user_id)
        
        text = "<b>📺 TUTORIAL SETTINGS</b>\n\n"
        text += "Configure tutorial videos for each shortlink. These help users understand how to navigate the shortlink process.\n\n"
        
        for i in range(1, 4):
            tutorial = page_settings['shortlink_tutorials'].get(f'shortlink{i}', {})
            enabled = tutorial.get('enabled', False)
            url = tutorial.get('url', 'Not set')
            text_label = tutorial.get('text', f'Tutorial {i}')
            
            text += f"<b>Shortlink {i}:</b> {'✅ Enabled' if enabled else '❌ Disabled'}\n"
            if enabled:
                text += f"  • URL: <code>{url}</code>\n"
                text += f"  • Text: <code>{text_label}</code>\n"
            text += "\n"
        
        text += "<b>💡 To configure tutorials, use these commands:</b>\n"
        text += "• <code>/tutorial1 URL | Button Text</code>\n"
        text += "• <code>/tutorial2 URL | Button Text</code>\n"
        text += "• <code>/tutorial3 URL | Button Text</code>\n"
        text += "• <code>/disabletutorial1</code> (or 2, 3)\n\n"
        text += "<b>Example:</b> <code>/tutorial1 https://youtube.com/watch?v=abc | How to Download</code>"
        
        buttons = [
            [InlineKeyboardButton("≺≺ Back", callback_data="page_settings_menu"), InlineKeyboardButton("Close", callback_data="close")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

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
• <code>{{web_link}}</code> - Page mode web link
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
                caption.text.format(file_name='', file_size='', caption='', download_link='', fast_link='', stream_link='', storage_link='', quality='', season='', episode='', web_link='')
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

    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
        except:  # noqa: E722
            await query.message.delete()
