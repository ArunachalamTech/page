# Copyright 2021 To 2024-present, Author: MrAKTech
import time  # noqa: F401
from pyrogram import Client
from MrAKTech.config import Telegram

StreamBot = Client(
    name="Web Streamer",
    api_id=Telegram.API_ID,
    api_hash=Telegram.API_HASH,
    bot_token=Telegram.BOT_TOKEN,
    sleep_threshold=Telegram.SLEEP_THRESHOLD,
    workers=Telegram.WORKERS,
    plugins={"root": "MrAKTech/plugins"},
)

multi_clients = {}
work_loads = {}
cdn_count = {}
