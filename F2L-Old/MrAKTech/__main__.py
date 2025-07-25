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

from MrAKTech import StreamBot, multi_clients
from MrAKTech.server import web_server
from MrAKTech.clients import initialize_clients, restart_bot
from MrAKTech.tools.utils_bot import temp
from MrAKTech.tools.performance_monitor import start_performance_monitoring
from MrAKTech.tools.advanced_cache import start_cache_cleanup
from pyrogram import Client

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
    
    # **CRITICAL FIX**: Initialize pyromod listeners BEFORE starting the bot
    print("🔧 Initializing pyromod listeners...")
    try:
        # Ensure listeners dictionary exists
        StreamBot.listeners = getattr(StreamBot, 'listeners', {})
        StreamBot.listening = getattr(StreamBot, 'listening', {})
        
        # Initialize all required listener types (string fallback)
        listener_types_str = ['message', 'callback_query', 'inline_query']
        
        # Try to get ListenerTypes enum from different possible locations
        ListenerTypes = None
        try:
            from pyromod.listen.listener_types import ListenerTypes
        except ImportError:
            try:
                from pyromod.listen import ListenerTypes
            except ImportError:
                try:
                    # For pyromod 1.5.0 and similar versions
                    import pyromod.listen
                    if hasattr(pyromod.listen, 'ListenerTypes'):
                        ListenerTypes = pyromod.listen.ListenerTypes
                    elif hasattr(pyromod, 'ListenerTypes'):
                        ListenerTypes = pyromod.ListenerTypes
                except:
                    pass
        
        if ListenerTypes:
            for listener_type in ListenerTypes:
                if listener_type not in StreamBot.listeners:
                    StreamBot.listeners[listener_type] = []
            print(f"✅ ListenerTypes enum found and initialized: {list(ListenerTypes)}")
        else:
            print("⚠️ ListenerTypes enum not found, using string fallback")
        
        # Ensure basic string listener types are also initialized
        for listener_type in listener_types_str:
            if listener_type not in StreamBot.listeners:
                StreamBot.listeners[listener_type] = []
        
        print(f"✅ Pyromod listeners initialized: {list(StreamBot.listeners.keys())}")
        
        # **ADDITIONAL FIX**: Monkey patch get_listener_matching_with_data to handle missing keys
        original_get_listener = getattr(StreamBot, 'get_listener_matching_with_data', None)
        if original_get_listener:
            def safe_get_listener_matching_with_data(data, listener_type):
                # Ensure the listener type exists
                if listener_type not in StreamBot.listeners:
                    print(f"🔧 Auto-initializing missing listener type: {listener_type}")
                    StreamBot.listeners[listener_type] = []
                return original_get_listener(data, listener_type)
            
            StreamBot.get_listener_matching_with_data = safe_get_listener_matching_with_data
            print("✅ Pyromod listener method patched for safety")
            
        # **RUNTIME PATCH**: Patch the client's listeners access in real-time
        original_listeners = StreamBot.listeners
        class SafeListenersDict(dict):
            def __getitem__(self, key):
                if key not in self:
                    print(f"🔧 Runtime: Auto-initializing listener type {key}")
                    self[key] = []
                return super().__getitem__(key)
            
            def get(self, key, default=None):
                if key not in self:
                    self[key] = []
                return super().get(key, default)
        
        # Replace the listeners dict with our safe version
        safe_listeners = SafeListenersDict(original_listeners)
        StreamBot.listeners = safe_listeners
        print("✅ Runtime listener dictionary patched for auto-initialization")
            
    except Exception as e:
        print(f"⚠️ Warning: Pyromod listener initialization failed: {e}")
        # Minimal fallback
        StreamBot.listeners = {'message': [], 'callback_query': [], 'inline_query': []}
        StreamBot.listening = {}
    
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    temp.ME = bot_info
    temp.BOT_ID = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name
    temp.B_LINK = f"https://t.me/{bot_info.username}"
    temp.START_TIME = time.time()
    print("------------------------------ DONE ------------------------------")
    print()
    print("---------------------- Initializing Clients ----------------------")
    await initialize_clients()
    
    # **ADDITIONAL FIX**: After multi-clients are initialized, ensure they all have pyromod attributes
    print("🔧 Verifying multi-client pyromod initialization...")
    for client_id, client in multi_clients.items():
        # Use direct attribute assignment to avoid recursion
        client.listening = getattr(client, 'listening', {})
        client.listeners = getattr(client, 'listeners', {})
        
        # Ensure basic listener types exist
        basic_types = ['message', 'callback_query', 'inline_query']
        for listener_type in basic_types:
            if listener_type not in client.listeners:
                client.listeners[listener_type] = []
        
        print(f"✅ Verified pyromod attributes for Client-{client_id}")
    
    print(f"✅ All {len(multi_clients)} clients verified for pyromod compatibility")
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
    try:
        await server.cleanup()
    except Exception as e:
        logging.warning(f"Server cleanup error: {e}")
    
    try:
        if StreamBot.is_connected:
            await StreamBot.stop()
    except Exception as e:
        logging.warning(f"Bot stop error: {e}")


if __name__ == "__main__":
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        logging.error(f"Runtime error: {err}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            loop.run_until_complete(cleanup())
        except Exception as cleanup_err:
            logging.warning(f"Cleanup error: {cleanup_err}")
        finally:
            loop.stop()
            logging.info("Stopped Services")
