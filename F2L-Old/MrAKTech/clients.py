#Copyright 2021 To 2024-present, Author: MrAKTech

import asyncio
import logging
from os import environ
from pyrogram import Client
from MrAKTech.config import Telegram
from MrAKTech import multi_clients, work_loads, StreamBot

logger = logging.getLogger("multi_client")

# This DC5 Bots
environ['MULTI_TOKEN1'] = '7486925095:AAEdZ1YaArIUk18Ujp5ATTnkJAaB15qgdO0' # @MrAKF2lClient1bot
environ['MULTI_TOKEN2'] = '7225388262:AAFNdXrz_Q-Ad5mRatSoDPyGIcxQVn_VVv4' # @MrAKF2lClient2bot
environ['MULTI_TOKEN3'] = '7413985195:AAH4EuredrYaFe2DYA-0sFGr2La-l4t1Z8A' # @MrAKF2lClient3bot
environ['MULTI_TOKEN4'] = '7015679204:AAFPTrKt7B1pG1fyGFtw6A5Ziza5B6gcIUM' # @MrAKF2lClient4bot
environ['MULTI_TOKEN5'] = '7030641843:AAE3w4EIpIde4rEuPAAOFcDAZaVBP4zRxqY' # @MrAKF2lClient5bot
environ['MULTI_TOKEN6'] = '7327176150:AAEAi0sEiD_JxCNUhaNRHOL0fPKaoEha6TM' # @MrAKF2lClient6bot

environ['MULTI_TOKEN7'] = '7460051597:AAGurpCLV9WLVBrJx2fFRiaByPjmBg4siEA' # @MrAKF2LClient7bot
environ['MULTI_TOKEN8'] = '7593296957:AAGJoapvfM09kBwCTeS0DDv_zpeOxyVkZck' # @MrAKF2LClient8bot
environ['MULTI_TOKEN9'] = '8171535139:AAE9402XecWL8ayZVam31rYNb6ph6Tssf4M' # @MrAKF2LClient9bot
environ['MULTI_TOKEN10'] = '7995500623:AAHwsuAah5Rv7Ir_NHY-wD26OyxrAnf4TWc' # @MrAKF2LClient10bot
environ['MULTI_TOKEN11'] = '7887383001:AAGcx-j8FV6hEiV2HU3JEzK5Ne9-rEMoXfU' # @MrAKF2LClient11bot

async def restart_bot():
    logger.info("Restarting all bots........")
    try:
        ai = Client(
            f"{Telegram.FILE_STORE_BOT_TOKEN}", Telegram.API_ID, Telegram.API_HASH,
            bot_token=Telegram.FILE_STORE_BOT_TOKEN,
            plugins={"root": "Storage"},
            workers=300, in_memory=True
        )
        await ai.start()
    except Exception as e:
        logger.exception(f"Error while restarting bot with token {Telegram.FILE_STORE_BOT_TOKEN}: {e}")
    logger.info("All bots restarted.") 

async def initialize_clients():
    multi_clients[0] = StreamBot
    work_loads[0] = 0
    all_tokens = dict(
        (c + 1, t)
        for c, (_, t) in enumerate(
            filter(
                lambda n: n[0].startswith("MULTI_TOKEN"), sorted(environ.items())
            )
        )
    )
    if not all_tokens:
        logger.info("No additional clients found, using default client")
        return
    
    async def start_client(client_id, token):
        try:
            if len(token) >= 100:
                session_string=token
                bot_token=None
                logger.info(f'Starting Client - {client_id} Using Session String')
            else:
                session_string=None
                bot_token=token
                logger.info(f'Starting Client - {client_id} Using Bot Token')
            if client_id == len(all_tokens):
                await asyncio.sleep(2)
                logger.info("This will take some time, please wait...")
            client = await Client(
                name=str(client_id),
                api_id=Telegram.API_ID,
                api_hash=Telegram.API_HASH,
                bot_token=bot_token,
                sleep_threshold=Telegram.SLEEP_THRESHOLD,
                no_updates=True,
                session_string=session_string,
                in_memory=True,
            ).start()
            client.id = (await client.get_me()).id
            work_loads[client_id] = 0
            
            # **CRITICAL FIX**: Ensure pyromod attributes are initialized for each multi-client
            client.listening = getattr(client, 'listening', {})
            client.listeners = getattr(client, 'listeners', {})
            
            # Initialize basic listener types
            basic_types = ['message', 'callback_query', 'inline_query']
            for listener_type in basic_types:
                if listener_type not in client.listeners:
                    client.listeners[listener_type] = []
            
            logger.info(f"✅ Client-{client_id} pyromod setup complete")
            
            return client_id, client
        except Exception:
            logger.error(f"Failed starting Client - {client_id} Error:", exc_info=True)
    
    clients = await asyncio.gather(*[start_client(i, token) for i, token in all_tokens.items()])
    multi_clients.update(dict(clients))
    if len(multi_clients) != 1:
        Telegram.MULTI_CLIENT = True
        logger.info("Multi-Client Mode Enabled")
    else:
        logger.info("No additional clients were initialized, using default client")
