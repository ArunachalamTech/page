from pyrogram import filters
from pyrogram.errors import MessageTooLong
import sys
import traceback
from MrAKTech.config import Telegram
from MrAKTech import StreamBot
from io import StringIO


@StreamBot.on_message(filters.command("eval") & filters.user(list(Telegram.OWNER_ID)))
async def executor(client, message):
    try:
        code = message.text.split(" ", 1)[1]
    except:
        return await message.reply("Command Incomplete!\nUsage: /eval your_python_code")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await aexec(code, client, message)
    except:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success!"
    final_output = f"Output:\n\n<code>{evaluation}</code>"
    try:
        await message.reply(final_output)
    except MessageTooLong:
        with open("eval.txt", "w+") as outfile:
            outfile.write(final_output)
        await message.reply_document("eval.txt")


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)
