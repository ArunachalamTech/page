#Copyright 2021 To 2024-present, Author: MrAKTech
from MrAKTech.config import Telegram
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class tamilxd(object):

    CUSTOM_SHORTNER_TXT = """<b>🔗 CUSTOM SHORTENER</b>

<b>Quick Setup:</b>
• <code>/api</code> - Add your API
• <code>/site</code> - Add your URL

📚 Need help? Click "How to Setup" below."""

    # Main settings text - keep it short
    SETTINGS_TXT = '''<b>⚙️ USER SETTINGS</b>

<b>📊 Current Status:</b>
• Site: <code>{URLX}</code>
• API: <code>{APIX}</code>
• Caption: <code>{CAPTION}</code>
• Link Mode: <code>{LINKMODE}</code>
• Page Mode: <code>{PAGEMODE}</code>
• Verify Mode: <code>{VERIFYMODE}</code>

<b>🎯 Quick Actions:</b> Use buttons below'''

    RESET_SETTINGS = 'Reset all settings to default?'
    
    USER_ABOUT_MESSAGE = """<b>📊 Your Current Settings</b>

🌐 Website: {shortener_url}
🔌 API: {shortener_api}
🎯 Method: {method}
💾 Storage: {storage}"""
    
    # Split long caption text into multiple pages
    CUSTOM_CAPTION_TXT = """<b>📝 CUSTOM CAPTION</b>

<b>🎯 Current Status:</b>
• Caption: Set ✅ / Not Set ❌
• Auto Extract: Enabled / Disabled

<b>⚡ Quick Actions:</b>
• Add Caption Template
• View Examples
• Format Links

📚 Click "Next Page" for detailed guide."""

    # Caption help page 1
    CAPTION_HELP_1 = """<b>📝 CAPTION GUIDE - Page 1/3</b>

<b>🔗 How to Add Links:</b>
• Markdown: <code>[Text](url)</code>
• HTML: <code>&lt;a href="url"&gt;Text&lt;/a&gt;</code>

<b>💡 Examples:</b>
• <code>[Join Channel](@MrAK_LinkZzz)</code>
• <code>[How to Open](https://t.me/guide)</code>

Both formats work perfectly!"""

    # Caption help page 2
    CAPTION_HELP_2 = """<b>📝 CAPTION GUIDE - Page 2/3</b>

<b>📋 Basic Variables:</b>
• <code>{file_name}</code> - File name
• <code>{file_size}</code> - File size
• <code>{download_link}</code> - Download
• <code>{stream_link}</code> - Stream
• <code>{web_link}</code> - Page mode link

<b>🧠 Auto Extract Variables:</b>
• <code>{quality}</code> - 1080p, 720p, 4K
• <code>{season}</code> - S01, S02
• <code>{episode}</code> - E01, E02"""

    # Caption help page 3
    CAPTION_HELP_3 = """<b>📝 CAPTION GUIDE - Page 3/3</b>

<b>📝 Example Template:</b>
<code>🎬 {file_name}
📺 {quality} | {season}{episode}
📥 {download_link}
🎮 {stream_link}
📱 [Join Channel](@MrAK_LinkZzz)</code>

<b>💡 Pro Tips:</b>
• Bot auto-extracts from filename & caption
• Test your template before saving
• Use clickable links for better UX"""

    CHL_CUSTOM_CAPTION_TXT = '''<b>📄 CHANNEL CAPTION</b>

<b>Current:</b> <code>{CAPTIONX}</code>

<b>📝 Info:</b> Bot auto-edits file names'''

    CHL_CHANNEL_DETAILS_TXT = '''<b>📺 CHANNEL DETAILS</b>
    
<b>📋 Info:</b>
• Title: <code>{TITLEX}</code>
• ID: <code>{CHANNEL_DIX}</code>
• Username: {USERNAMEX}

<b>⚙️ Settings:</b>
• Site: {URLX}
• API: {APIX}
• Caption: <code>{CAPTION}</code>'''

    CHL_SHORTNER_TXT = '''<b>🔗 CHANNEL SHORTENER</b>

<b>📊 Current:</b>
• URL: {URLX}
• API: {APIX}

<b>⚡ Actions:</b> Use buttons below'''

    CHL_CHANNEL_ADD_TXT = '''<b>📺 ADD CHANNEL</b>

<b>📋 Steps:</b>
1. Add me as admin with "Post Messages" 
2. Forward any message from channel

<b>⏱️ Timeout:</b> 60 seconds
<b>❌ Cancel:</b> Send /cancel'''

    # Optimized START text
    START_TXT = """<b>Hello {} 👋</b>

<b>🚀 File to Link Bot</b>

<b>📤 Send me:</b>
• Videos, Documents, Photos
• Get permanent download links
• Stream videos online

<b>⚡ Features:</b>
• Custom shorteners
• Page mode with verification  
• Link mode for batch files
• Never expires!

<b>🎯 Quick Start:</b> Just send a file!"""

    # Simplified ABOUT text
    ABOUT_TXT = """<b>🤖 BOT DETAILS</b>

<b>📊 Server Info:</b>
• Ping: Fast ⚡
• Uptime: 24/7 
• Storage: Unlimited

<b>💻 Developer:</b> @IamMrAK_bot
<b>📢 Updates:</b> @MrAK_LinkZzz

<b>🔥 Version:</b> 2.0 Advanced"""

    # Optimized HELP - split into pages
    HELP_TXT = """<b>📚 HOW TO USE - Page 1/2</b>

<b>🚀 Quick Start:</b>
• Send any file → Get links instantly
• Stream videos in any player
• Links never expire!

<b>📱 For Channels:</b>
• Add me as admin
• Auto-generate links for posts

<b>⚙️ Basic Commands:</b>
• <code>/settings</code> - Bot settings
• <code>/help</code> - This help menu"""

    # Help page 2
    HELP_PAGE_2 = """<b>📚 HOW TO USE - Page 2/2</b>

<b>🔗 Link Formats:</b>
• Markdown: <code>[text](url)</code>
• HTML: <code>&lt;a&gt;text&lt;/a&gt;</code>
• Both work perfectly!

<b>❗ Rules:</b>
• No adult content (ban)
• Respect copyrights

<b>💬 Support:</b> @IamMrAK_bot
<b>📢 Channel:</b> @MrAK_LinkZzz"""

    OWNER_INFO = """<b>👨‍💻 DEVELOPER</b>

<b>📛 Name:</b> 𝙼𝚁𝗔𝗞
<b>💬 Contact:</b> @IamMrAK_bot 
<b>🔗 Direct Chat:</b> <a href="https://t.me/IamMrAK_bot">Click Here</a>

<b>🛠️ Services:</b>
• Custom bot development
• Server optimization
• 24/7 support"""

    SOURCE_TXT = """<b>📝 NOTES</b>

• This bot is open source
• Built with Python & Pyrogram
• Hosted on premium servers
• Regular updates & maintenance

<b>🔧 Tech Stack:</b>
• Python 3.11+
• MongoDB Database  
• Redis Caching
• Docker Deployment"""

    DEV_TXT = """<b>🙏 SPECIAL THANKS</b>

<b>💎 Core Developers:</b>
• MrAK - Main Developer
• Community Contributors

<b>🛠️ Libraries Used:</b>
• Pyrogram - Telegram MTProto
• Motor - MongoDB Driver
• Shortzy - URL Shortening
• Aiohttp - Web Server"""

    # Simplified comments about shorteners
    COMMENTS_TXT = """<b>💰 SHORTENER SETUP</b>

<b>🔗 Popular Services:</b>
• AdFly, Short.st, LinkVertise
• Shrinkme, Gplinks, Tnlink

<b>⚡ Quick Setup:</b>
1. Register on shortener site
2. Get API key from dashboard  
3. Use <code>/api your_key</code>
4. Use <code>/site domain.com</code>

<b>💡 Pro Tip:</b> Test with small links first!"""

    DONATE_TXT = """<b>💖 SUPPORT DEVELOPMENT</b>

<b>🙏 Help keep this bot running!</b>

<b>💰 Ways to Support:</b>
• UPI: mrak@paytm
• Bitcoin: Coming soon
• Star this message ⭐
• Share with friends 📤

<b>🎁 Supporters get:</b>
• Priority support
• Beta features access
• Custom modifications"""

    # Keep existing stream texts - they're already short
    STREAM_MSG_TXT = """<b>🎉 Your Links Are Ready!</b>

<b>📥 Download:</b> {download_link}
<b>🎮 Stream:</b> {stream_link}
<b>💾 Storage:</b> {storage_link}

<b>📱 How to Stream:</b>
Copy stream link → Open in video player"""

    STREAM_TXT = """<b>{caption}

📂 <code>{file_name}</code>
📊 <code>{file_size}</code>

📥 Download: {download_link}
🎮 Stream: {stream_link}
💾 Storage: {storage_link}</b>"""

    BAN_TXT = """<b>🚫 ACCESS DENIED</b>

<b>❌ You are banned from using this bot</b>

<b>📝 Reason:</b> {ban_reason}
<b>⏰ Duration:</b> {ban_duration}

<b>💬 Appeal:</b> Contact @IamMrAK_bot"""

    SWCMD_TXT = """<b>⚠️ SOMETHING WENT WRONG</b>

<b>😔 An error occurred</b>

<b>🔧 Please try:</b>
• Restart with /start
• Check your input
• Try again later

<b>💬 Still issues?</b> Contact @IamMrAK_bot"""

    # Add new page mode texts
    PAGE_MODE_HELP_1 = """<b>📄 PAGE MODE - Page 1/2</b>

<b>🎯 What is Page Mode?</b>
• Beautiful web pages for downloads
• Multiple shortlink options
• Mobile-responsive design
• Professional presentation

<b>⚙️ Setup:</b>
1. Enable page mode
2. Add up to 3 shortlinks
3. Use {web_link} in captions"""

    PAGE_MODE_HELP_2 = """<b>📄 PAGE MODE - Page 2/2</b>

<b>🔐 Verify Mode Features:</b>
• Progressive verification system
• Anti-spam protection  
• Time-based resets
• Direct access after verification

<b>💡 Perfect for:</b>
• Movie channels
• Premium content
• Monetization strategy"""

    # Add verify mode texts  
    VERIFY_MODE_HELP_1 = """<b>🔐 VERIFY MODE - Page 1/2</b>

<b>🎯 How it Works:</b>
• Users complete 3 verifications daily
• Progressive shortlink system
• Automatic time-based reset
• Direct access after completion

<b>📊 Verification Order:</b>
• Visit 1: Verify Shortlink 3
• Visit 2: Verify Shortlink 2  
• Visit 3: Verify Shortlink 1
• Visit 4+: Direct download"""

    VERIFY_MODE_HELP_2 = """<b>🔐 VERIFY MODE - Page 2/2</b>

<b>⚙️ Configuration:</b>
• Independent verify shortlinks
• Customizable time gaps
• Per-user tracking
• Works with page mode

<b>💰 Benefits:</b>
• Anti-spam protection
• Monetization strategy
• Professional presentation
• User progress tracking"""

    # Link mode help texts
    LINK_MODE_HELP_1 = """<b>🔗 LINK MODE - Page 1/2</b>

<b>🎯 What is Link Mode?</b>
• Collect multiple files
• Batch processing
• Custom captions for each batch
• Multiple shortener support

<b>📝 How to Use:</b>
1. Enable link mode
2. Send multiple files
3. Use /complete to process
4. Get formatted output"""

    LINK_MODE_HELP_2 = """<b>🔗 LINK MODE - Page 2/2</b>

<b>⚡ Commands:</b>
• <code>/complete</code> - Process files
• <code>/pending</code> - View queue
• <code>/clear</code> - Clear queue

<b>🎨 Advanced Features:</b>
• 3 custom caption templates
• {filenamefirst}, {filenamelast}
• Batch shortlink generation
• Perfect for series/seasons"""

# ------------------------------------------------------------------------------

class BUTTON(object):
    
    OWNER_BUTTONS =  InlineKeyboardMarkup([
        InlineKeyboardButton('𝙼𝚁𝗔𝗞', url= Telegram.MAIN )
    ])

    START_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('📢 𝙼𝙰𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.MAIN),
        InlineKeyboardButton('⚡ 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.AUTH_CHANNEL3)
        ],[
        InlineKeyboardButton('📢 𝙼𝙾𝚅𝙸𝙴 𝙶𝚁𝙾𝚄𝙿', url= Telegram.AUTH_GROUP)
        ],[
        InlineKeyboardButton('⚙️ Hᴇʟᴘ', callback_data='help'),
        InlineKeyboardButton('📚 Aʙᴏᴜᴛ', callback_data='about')
        ],[
        InlineKeyboardButton('⚙️ Sᴇᴛᴛɪɴɢs ', callback_data='settings')
        ]]
    )

    HELP_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton("📊 Status", callback_data="stats")
        ],[
        InlineKeyboardButton("⛺ Home", callback_data="start"),
        InlineKeyboardButton("🗑 Close", callback_data="close")
        ]]
    )

    ABOUT_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('📢 𝙼𝙰𝙸𝙽 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.MAIN),
        InlineKeyboardButton('⚡ 𝚄𝙿𝙳𝙰𝚃𝙴𝚂 𝙲𝙷𝙰𝙽𝙽𝙴𝙻', url= Telegram.AUTH_CHANNEL3)
        ],[
        InlineKeyboardButton('📢 𝙼𝙾𝚅𝙸𝙴 𝙶𝚁𝙾𝚄𝙿', url= Telegram.AUTH_GROUP)
        ],[
        InlineKeyboardButton("🌿 sᴏᴜʀᴄᴇ", callback_data = "source"),
        InlineKeyboardButton("👨‍💻 Dᴇᴠs 🥷", callback_data = "dev")
        ],[
        InlineKeyboardButton("⛺ Hᴏᴍᴇ", callback_data = "start"),
        InlineKeyboardButton("🗑 Cʟᴏsᴇ", callback_data = "close")
        ]]
    )
    
    DONATE_BUTTONS = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton("Pᴀʏ 💰 Aᴍᴏᴜɴᴛ",
                                             url= Telegram.SUPPORT)
        ],[
        InlineKeyboardButton("⛺ Hᴏᴍᴇ", callback_data="start"),
        InlineKeyboardButton("🗑 Cʟᴏsᴇ", callback_data="close")
        ]]
    ) 

    DEV_BUTTONS = InlineKeyboardMarkup( 
        [[
        InlineKeyboardButton('𝙼𝚁𝗔𝗞', url= Telegram.SUPPORT),
        ],[
        InlineKeyboardButton("≺≺ Back", callback_data = "about"),
        InlineKeyboardButton("🗑 Close", callback_data = "close")
        ]]
    ) 

    ADN_BUTTONS = InlineKeyboardMarkup( 
        [[
        InlineKeyboardButton("🗑 Close", callback_data = "close")
        ]]
    ) 

    SOURCE_BUTTONS = InlineKeyboardMarkup( 
        [[
        InlineKeyboardButton("♙ ʜᴏᴍᴇ", callback_data = "start"),
        InlineKeyboardButton("🗑 Close", callback_data = "close")
        ]]
    )
