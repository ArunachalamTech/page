# Copyright 2021 To 2024-present, Author: MrAKTech
import time  # noqa: F401
from pyrogram import Client
import pyromod  # Enable listen functionality for interactive input
from MrAKTech.config import Telegram

# **COMPREHENSIVE PYROMOD FIX**: Monkey patch Client class to auto-initialize listening
original_client_init = Client.__init__

def patched_client_init(self, *args, **kwargs):
    """Patched Client.__init__ to ensure listening attribute is always present"""
    original_client_init(self, *args, **kwargs)
    
    # Direct attribute assignment to avoid recursion issues
    self.listening = getattr(self, 'listening', {})
    self.listeners = getattr(self, 'listeners', {})
    
    # Initialize basic listener types if not present
    basic_types = ['message', 'callback_query', 'inline_query']
    for listener_type in basic_types:
        if listener_type not in self.listeners:
            self.listeners[listener_type] = []
    
    print(f"🔧 Auto-initialized pyromod attributes for client: {getattr(self, 'name', 'unnamed')}")

# Apply the monkey patch
Client.__init__ = patched_client_init

StreamBot = Client(
    name="Web Streamer",
    api_id=Telegram.API_ID,
    api_hash=Telegram.API_HASH,
    bot_token=Telegram.BOT_TOKEN,
    sleep_threshold=Telegram.SLEEP_THRESHOLD,
    workers=Telegram.WORKERS,
    plugins={"root": "MrAKTech/plugins"},
)

# Ensure StreamBot has all required pyromod attributes
StreamBot.listening = getattr(StreamBot, 'listening', {})
StreamBot.listeners = getattr(StreamBot, 'listeners', {})

# Initialize basic listener types
basic_types = ['message', 'callback_query', 'inline_query']
for listener_type in basic_types:
    if listener_type not in StreamBot.listeners:
        StreamBot.listeners[listener_type] = []

print("✅ StreamBot pyromod attributes initialized")

multi_clients = {}
work_loads = {}
cdn_count = {}
