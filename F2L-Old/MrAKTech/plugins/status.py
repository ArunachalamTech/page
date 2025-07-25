import asyncio
import time
import datetime
import shutil
import psutil

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums.parse_mode import ParseMode
from pyrogram import filters

from MrAKTech import StreamBot, work_loads, multi_clients, cdn_count
from MrAKTech.database.u_db import u_db
from MrAKTech.tools.utils_bot import readable_time, get_readable_file_size, temp
from MrAKTech.tools.txt import tamilxd


IMAGE_X = "https://graph.org/file/cbcf2177d0f74475eecb7.jpg"
START_TEXT = """ Your Telegram DC Is : `{}`  """


@StreamBot.on_message(filters.command("dc") & filters.private)
async def about_handler(bot, message):
    hs = await message.reply_text(
        text=START_TEXT.format(message.from_user.dc_id),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close ✗", callback_data="close")]]
        ),
        quote=True,
    )
    await asyncio.sleep(1600)
    await hs.delete()
    await message.delete()


@StreamBot.on_message(filters.command("ping"))
async def ping(b, m):
    start_t = time.time()
    ag = await m.reply_text("....", quote=True)
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await ag.edit(f"Pong!\n{time_taken_s:.3f} ms")


@StreamBot.on_message(filters.command(["users", "stats"]) & filters.private)
async def sts(c, m):
    STATUS_TXT = f"""**╭──────❪ 𝗦𝗧𝗔𝗧𝗨𝗦 ❫─────⍟
│
├👤 Active Users : {await u_db.total_users_count()}
│
├👤 InActive Users : {await u_db.itotal_users_count()}
│
├ Storage Users : {await u_db.stotal_users_count()}
│
├🤖 Total Bots : {await u_db.total_users_bots_count()} 
│
├🤖 Total Channel : {await u_db.total_channels_count()} 
│
├🚫 Banned Users : {await u_db.total_banned_users_count()}
│
╰───────────────────⍟**"""
    await m.delete()
    await m.reply_text(
        text=STATUS_TXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Refresh 🔃", callback_data="stats"),
                    InlineKeyboardButton("Close ✗", callback_data="close"),
                ]
            ]
        ),
        parse_mode=ParseMode.MARKDOWN,
        quote=True,
    )


@StreamBot.on_message(filters.private & filters.command(["status", "tasks"]))
async def stats(bot, update):
    india_time = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    )
    total, used, free = shutil.disk_usage(".")
    bot_workloads = sorted(work_loads.items(), key=lambda x: x[1], reverse=True)
    v2_workloads = sorted(cdn_count.items(), key=lambda x: x[1], reverse=True)
    bot_workload_dict = dict(
        ("bot" + str(c + 1), workload) for c, (_, workload) in enumerate(bot_workloads)
    )
    v2_workload_dict = dict(
        ("v2" + str(c + 1), workload) for c, (_, workload) in enumerate(v2_workloads)
    )
    tamil = await update.reply_text(
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
            disk=psutil.disk_usage("/").percent,
            sent=get_readable_file_size(psutil.net_io_counters().bytes_sent),
            recv=get_readable_file_size(psutil.net_io_counters().bytes_recv),
            v1_traffic_total=sum(
                workload for _, workload in bot_workloads
            ),  # for this total v1 workload
            v2_traffic_total=sum(
                workload for _, workload in v2_workloads
            ),  # for this total v2 workload
            multi_clients=len(multi_clients),
            v1_traffic_me=bot_workload_dict.get("bot1", 0),  # for this bot v1 workload
            v2_traffic_me=v2_workload_dict.get("bot1", 0),  # for this bot v1 workload
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Refresh 🔃", callback_data="status"),
                    InlineKeyboardButton("Close ✗", callback_data="close"),
                ]
            ]
        ),
        quote=True,
    )
    # await update.delete()
    await asyncio.sleep(1600)
    await tamil.delete()
