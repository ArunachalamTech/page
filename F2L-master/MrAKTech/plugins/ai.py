# Description: AI Chatbot Plugin for MrAKTech Userbot

import random
import requests

from pyrogram import filters
from MrAKTech import StreamBot
from pyrogram.types import Message
from pyrogram.enums.parse_mode import ParseMode

USERBOT_PREFIX = [".", "!", "/", "@"]


@StreamBot.on_message(filters.command(["askai", "ai"], prefixes=USERBOT_PREFIX))
async def gpt(app, message: Message):
    text = "".join(message.text.split(" ")[1:])
    if len(text) == 0:
        return await message.reply_text(
            f"""Cannot reply to empty message. \n\nPreFix : {USERBOT_PREFIX} \n\nLike : @Ai Or !Ai [Question]""",
            parse_mode=ParseMode.MARKDOWN,
        )
    m = await message.reply_text(
        "Getting Request....", parse_mode=ParseMode.MARKDOWN, quote=True
    )
    url = "https://wewordle.org/gptapi/v1/web/turbo"
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
        "content-type": "application/json",
        "X-Forwarded-For": ip,
        "origin": "https://chatg.org",
        "referer": "https://chatg.org/",
    }

    conv = [
        {"content": "Hello! How can I help you?", "role": "assistant"},
        {"content": text, "role": "user"},
    ]

    resp = requests.post(url, headers=headers, json={"messages": conv})

    try:
        # if resp.status_code == 200:
        await m.edit_text(f"{resp.json()['message']['content']}")
        # await m.edit_text(f"Error :-\n{resp.json()}")
    except Exception as e:
        await m.edit_text(f"Error :-\n{e}")
