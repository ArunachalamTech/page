# Copyright 2021 To 2024-present, Author: MrAKTech

import jinja2
import urllib.parse
import logging
import aiohttp
import random

from MrAKTech.config import Telegram, Domain
from MrAKTech import StreamBot
from MrAKTech.tools.human_readable import humanbytes
from MrAKTech.tools.file_properties import get_file_ids
from MrAKTech.server.exceptions import InvalidHash


async def render_page(id, secure_hash, src=None):
    file_data = await get_file_ids(StreamBot, int(Telegram.FLOG_CHANNEL), int(id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"link hash: {secure_hash} - {file_data.unique_id[:6]}")
        logging.debug(f"Invalid hash for message with - ID {id}")
        raise InvalidHash

    file_name = file_data.file_name.replace("_", " ")
    src = urllib.parse.urljoin(random.choice(Domain.CLOUDFLARE_URLS), f"dl/{id}/files.mkv?hash={secure_hash}")
    mra = urllib.parse.urljoin(random.choice(Domain.MRAKFAST_URLS), f"dl/{id}/files.mkv?hash={secure_hash}")

    tag = file_data.mime_type.split("/")[0].strip()
    file_size = humanbytes(file_data.file_size)
    if tag in ["video", "audio"]:
        template_file = "MrAKTech/server/template/play.html"
    else:
        template_file = "MrAKTech/server/template/dl.html"
        async with aiohttp.ClientSession() as s:
            async with s.get(src) as u:
                file_size = humanbytes(int(u.headers.get("Content-Length")))

    with open(template_file) as f:
        template = jinja2.Template(f.read())

    file_store_link = (
        f"https://telegram.me/{Telegram.FILE_STORE_BOT_USERNAME}?start=download_{id}"
    )
    ads_link = f"https://mraklinkzz.infinityfreeapp.com/post.php?link={secure_hash}{id}"
    return template.render(
        file_name=file_name,
        file_url=src,
        mra_url=mra,
        file_size=file_size,
        mime_type=file_data.mime_type,
        file_unique_id=file_data.unique_id,
        file_id=id,
        ads_link=src,
        file_store_link=file_store_link,
    )
