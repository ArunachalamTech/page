#Copyright 2021 To 2024-present, Author: MrAKTech

import time
import asyncio

from MrAKTech import StreamBot
from MrAKTech.config import Telegram
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.txt import tamilxd, BUTTON
from MrAKTech.tools.utils_bot import temp, get_time, broadcast_messages

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

lock = asyncio.Lock()

@StreamBot.on_message(filters.command('invite_link') & filters.user(list(Telegram.OWNER_ID)))
async def gen_invite_link(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat ID')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give me a valid chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite link generation failed, I'am not having sufficient rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your invite link: {link.invite_link}')

@StreamBot.on_message(filters.command('leave') & filters.user(list(Telegram.OWNER_ID)))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat ID')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:  # noqa: E722
        chat = chat
    try:
        buttons = [[
            InlineKeyboardButton('Support Group', url=Telegram.SUPPORT),
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text='Hello Friends,\nMy owner has told me to leave from group so i go! If you need add me again contact my support group.',
            reply_markup=reply_markup,
        )

        await bot.leave_chat(chat)
        await message.reply(f"Left the chat `{chat}`")
    except Exception as e:
        await message.reply(f'Error - {e}')

@StreamBot.on_message(filters.command("admin") & filters.private & filters.user(list(Telegram.OWNER_ID)))
async def start(bot, update):
    await update.reply_text(
        text=tamilxd.ADN_COMS,
        reply_markup=BUTTON.ADN_BUTTONS
    )

########## BAN CMD STARTING #########

@StreamBot.on_message(filters.command("ban") & filters.private & filters.user(list(Telegram.OWNER_ID)))
async def sts(b, m: Message):
    usr_cmd = m.text.split()
    if len(usr_cmd) < 2:
        return await m.reply_text("Invalid Format\n/ban UserID\n`/ban UserID1 UserID2` .....")
    text="Banned Users:\n"
    for id in usr_cmd[1:]:
        if not await u_db.is_user_banned(int(id)):
            try:
                await u_db.ban_user(int(id))
                text+=f"`{id}`: Banned\n"
                await b.send_message(
                    chat_id=id,
                    text="**Your Banned to Use This Bot**",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except Exception as e:
                text+=f"`{id}`: Error `{e}`\n"
        else:
            text+=f"`{id}`: Already Banned\n"
    await m.reply_text(text)

@StreamBot.on_message(filters.command("unban") & filters.private & filters.user(list(Telegram.OWNER_ID)))
async def sts(b, m: Message):  # noqa: F811
    usr_cmd = m.text.split()
    if len(usr_cmd) < 2:
        return await m.reply_text("Invalid Format\n/unban UserID\n`/unban UserID1 UserID2` .....")
    text="Unbanned Users:\n"
    for id in usr_cmd[1:]:
        if await u_db.is_user_banned(int(id)):
            try:
                await u_db.unban_user(int(id))
                text+=f"`{id}`: Unbanned\n"
                await b.send_message(
                    chat_id=id,
                    text="**Your Unbanned now Use can use This Bot**",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except Exception as e:
                text+=f"`{id}`: Error `{e}`\n"
        else:
            text+=f"`{id}`: Not Banned\n"
    await m.reply_text(text)

# ------------------------------------[ warn CODE ]------------------------------------- #

@StreamBot.on_message(filters.command('warnz') & filters.user(list(Telegram.OWNER_ID)))
async def warnz(bot, message):
    await message.reply("Warn Commands Usage\n\n /warns [Chat ID] [Message] \n /warn [Chat ID] [Message] \n /unwarn [Chat ID] [Message] \n /delwarn [Chat ID] [Message]")

@StreamBot.on_message(filters.command('warns') & filters.user(list(Telegram.OWNER_ID)))
async def warns(bot, message):
    if len(message.command) <= 1:
        return await message.reply("Invalid Command Usage\n/warns [Chat ID] [Message]")
    try:
        chat_id = int(message.command[1])
        warns = await u_db.wget_user(int(chat_id))
        if warns:
            msg = f"""**__User Warns__**\n\n**Chat ID:** `{chat_id}`\n**Warns:** {warns['warn_count']}/3\n**Reason:** {warns['warn_msg']}"""
        else:
            msg = f"**__User Warns__**\n\n**Chat ID:** `{chat_id}`\n**Warns:** 0/3\n**Reason:** No Warns"
        await message.reply_text(msg)
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@StreamBot.on_message(filters.command('warn') & filters.user(list(Telegram.OWNER_ID)))
async def warn(bot, message):
    if len(message.command) <= 1:
        return await message.reply("Invalid Command Usage\n/warn [Chat ID] [Message]")
    try:
        if len(message.text.split(None)) > 2:
            reason = message.text.split(None, 2)[2]
            chat_id = message.text.split(None, 2)[1]
        else:
            chat_id = message.command[1]
            reason = "No reason provided."
        #
        if await u_db.is_wuser_exist(int(chat_id)):
            warns = await u_db.wget_user(int(chat_id))
            if warns['warn_count'] >= 3:
                if not await u_db.is_user_banned(int(chat_id)):
                    try:
                        await u_db.ban_user(int(chat_id))
                        msg =f"`{chat_id}`: Banned\n"
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"**Your Banned to Use This Bot**, Reason : {reason}",
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                    except Exception as e:
                        msg =f"`{id}`: Error `{e}`\n"
                else:
                    msg =f"`{id}`: Already Banned\n"
            else:
                msg = f"""**Reason:** {reason}\n**Warns:** {warns['warn_count'] + 1}/3"""
                await u_db.wupdate_user(int(chat_id), str(reason), int(warns['warn_count']+1))
                await bot.send_message(int(chat_id), str(msg))
            await message.reply_text("Message sent successfully! \n\n", msg)
        else:
            await u_db.wadd_user(int(chat_id), str(reason))
            msg = f"""**__You are Warned__**\n\n **Reason:** {reason}\n**Warns:** 1/3"""
            await bot.send_message(int(chat_id), msg)
            await message.reply_text("Message sent successfully! \n\n", msg)
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@StreamBot.on_message(filters.command('unwarn') & filters.user(list(Telegram.OWNER_ID)))
async def unwarn(bot, message):
    if len(message.command) <= 1:
        return await message.reply("Invalid Command Usage\n/unwarn [Chat ID] [Message]")
    try:
        if len(message.text.split(None)) > 2:
            reason = message.text.split(None, 2)[2]
            chat_id = message.text.split(None, 2)[1]
        else:
            chat_id = message.command[1]
            reason = "No reason provided."
        if await u_db.is_wuser_exist(int(chat_id)):
            warns = await u_db.wget_user(int(chat_id))
            msg = f"""**__You are Unwarned__**\n\n **Reason:** {reason}\n**Warns:** {warns['warn_count'] - 1}/3"""
            await u_db.wupdate_user(int(chat_id), str(reason), int(warns['warn_count']-1))
            await bot.send_message(int(chat_id), msg)
            await message.reply_text(f"Successfully warned the user.\n\n{msg}")
        else:
            await message.reply_text("This user has not been warned. Please check again.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@StreamBot.on_message(filters.command('delwarn') & filters.user(list(Telegram.OWNER_ID)))
async def delwarn(bot, message):
    if len(message.command) <= 1:
        return await message.reply("Invalid Command Usage\n/delwarn [Chat ID] [Message]")
    try:
        if len(message.text.split(None)) > 2:
            reason = message.text.split(None, 2)[2]
            chat_id = message.text.split(None, 2)[1]
        else:
            chat_id = message.command[1]
            reason = "No reason provided."
        if await u_db.is_wuser_exist(int(chat_id)):
            msg = f"You have been deleted from the warning system. \n\n **Reason:** {reason}"
            await u_db.wdelete_user(int(chat_id))
            await bot.send_message(chat_id, msg)
            await message.reply_text(f"Successfully warned the user.\n\n{msg}")
        else:
            await message.reply_text("This user has not been warned. Please check again.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# ------------------------------------[ LOG TXT ]------------------------------------- #   

@StreamBot.on_message(filters.command('log') & filters.user(list(Telegram.OWNER_ID)))
async def log(bot, msg):
    await msg.reply("📜 ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʙᴏᴛ ʟᴏɢ ꜰɪʟᴇ all cmds \n\n /logs \n /clear_logs", quote=True)

@StreamBot.on_message(filters.command('logs') & filters.user(list(Telegram.OWNER_ID)))
async def log_file(bot, msg):
    try: 
        await msg.reply_document('BotLog.txt', caption="📜 ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʙᴏᴛ ʟᴏɢ ꜰɪʟᴇ...", quote=True)
    except Exception as e:
        await msg.reply(str(e))

@StreamBot.on_message(filters.command("clear_logs") & filters.user(list(Telegram.OWNER_ID)))
async def Clear_logs(client, message):
    with open("BotLog.txt", "w") as f:
        f.truncate(0)
    await message.reply_text("Logs Cleared Successfully!", quote=True)


# ------------------------[ BROADCAST ]--------------------------- #

@StreamBot.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    await query.message.edit("Trying to cancel broadcasting...")
    temp.BROADCAST_CANCEL = True

@StreamBot.on_message(filters.command(["broadcast", "bcast", "pin_broadcast", "pin_bcast"]) & filters.private & filters.user(list(Telegram.OWNER_ID)) & filters.reply)
async def broadcast_to_users(bot, message):
    if lock.locked():
        return await message.reply('Currently broadcast processing, Wait for complete.')
    #
    if message.command[0] in ['pin_broadcast', 'pin_bcast']:
        pin = True
    else:
        pin = False
    msg = await message.reply_text('Broadcasting your message...')
    broadcast_msg = message.reply_to_message
    total_users = await u_db.total_users_count()
    done = 0
    blocked = 0
    failed = 0
    success = 0
    start_time = time.time()
    temp.BROADCAST_CANCEL = False

    async with lock:
        async for user in await u_db.get_all_users():
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

