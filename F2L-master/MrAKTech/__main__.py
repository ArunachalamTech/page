# Copyright 2021 To 2024-present, Author: MrAKTech

import sys
import time
import asyncio
import logging
import logging.handlers as handlers
import platform
from MrAKTech.config import Server
from aiohttp import web
from pyrogram import idle, utils as pyroutils

from MrAKTech import StreamBot
from MrAKTech.server import web_server
from MrAKTech.clients import initialize_clients, restart_bot
from MrAKTech.tools.utils_bot import temp
from MrAKTech.tools.performance_monitor import start_performance_monitoring
from MrAKTech.tools.advanced_cache import start_cache_cleanup

logging.basicConfig(
    level=logging.INFO,
    datefmt="%d/%m/%Y %H:%M:%S",
    format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        handlers.RotatingFileHandler(
            "BotLog.txt", mode="a", maxBytes=104857600, backupCount=2, encoding="utf-8"
        ),
    ],
)

pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.CRITICAL -1)

server = web.AppRunner(web_server())
loop = asyncio.get_event_loop()



async def start_services():
    print()
    print("-------------------- Initializing Telegram Bot --------------------")
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    temp.ME = bot_info
    temp.BOT_ID = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name
    temp.START_TIME = time.time()
    print("------------------------------ DONE ------------------------------")
    print()
    print("---------------------- Initializing Clients ----------------------")
    await initialize_clients()
    print("------------------------------ DONE ------------------------------")
    print()
    print("------------------ Starting Performance Monitoring ----------------")
    await start_performance_monitoring()
    await start_cache_cleanup()
    print("------------------------------ DONE ------------------------------")
    print()
    print("--------------------- Initializing High-Speed Web Server ---------------------")
    await server.setup()
    
    try:
        # Create TCP site with optimized settings for high performance
        # Check if we're on Windows to avoid reuse_port error
        tcp_site_kwargs = {
            "runner": server,
            "host": Server.BIND_ADDRESS,
            "port": Server.PORT,
            "reuse_address": True,  # Allow address reuse
            "backlog": 1024         # Increased backlog for more concurrent connections
        }
        
        # Only add reuse_port on non-Windows systems
        if platform.system() != "Windows":
            tcp_site_kwargs["reuse_port"] = True
        
        site = web.TCPSite(**tcp_site_kwargs)
        await site.start()
        print("------------------------------ DONE ------------------------------")
    except Exception as e:
        logging.error(f"reuse_port not supported by socket module: {e}")
        # Fallback to basic TCP site without reuse_port
        site = web.TCPSite(
            server, 
            Server.BIND_ADDRESS, 
            Server.PORT,
            reuse_address=True,
            backlog=1024
        )
        await site.start()
        print("------------------------------ DONE (Fallback) ------------------------------")
    print()
    print("------------------------- Service Started -------------------------")
    print("                        bot =>> {}".format(bot_info.first_name))
    if bot_info.dc_id:
        print("                        DC ID =>> {}".format(str(bot_info.dc_id)))
    print(" URL =>> {}".format(Server.URL))
    print("🚀 High-Performance Features:")
    print("   ✅ 16 Workers for maximum throughput")
    print("   ✅ Advanced caching system active")
    print("   ✅ Performance monitoring enabled")
    print("   ✅ Optimized chunk sizes (up to 2MB)")
    print("   ✅ Enhanced connection handling")
    print("------------ Storage clone bots start ------------")
    await restart_bot()
    print("------------ all clone bots started ------------")
    print("------------------------------------------------------------------")
    await idle()


async def cleanup():
    await server.cleanup()
    await StreamBot.stop()


if __name__ == "__main__":
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logging.error(err.with_traceback(None))
    finally:
        loop.run_until_complete(cleanup())
        loop.stop()
        logging.info("Stopped Services")
