import os
import asyncio
from telethon import TelegramClient
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yaml
import re
from sqlite3 import OperationalError

HOME = os.path.dirname(__file__)
api_hash_file = os.path.join(HOME, 'secrets', 'api_hash')
api_id_file = os.path.join(HOME, 'secrets', 'api_id')
config_file = os.path.join(HOME, 'pyCRONos.yml')
log_file = os.path.join(HOME, 'pyCRONos.log')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(log_file),
              logging.StreamHandler()]
)
logger = logging.getLogger('pyCRONos')


def get_tg_client():
    with open(api_hash_file) as apiF, open(api_id_file) as idF:
        api_hash = apiF.read().strip()
        api_id = int(idF.read().strip())
    try:
        if os.path.exists(os.path.join(HOME, 'pyCRONos.session')):
            client = TelegramClient(session=os.path.join(HOME, 'pyCRONos.session'),
                                    api_id=api_id, api_hash=api_hash,
                                    auto_reconnect=True,
                                    connection_retries=5)
        else:
            client = TelegramClient('pyCRONos', api_id=api_id, api_hash=api_hash, sequential_updates=True)
    except OperationalError:
        logger.error(f'Telegram Client is already connected to telegram API')
        exit(1)
    return client


def cron_to_apsched(cron):
    cron = re.sub(' +', ' ', cron).split(' ')
    cron_syntax = ['minute', 'hour', 'day', 'month', 'day_of_week']
    return {cron_arg: cron[i] for i, cron_arg in enumerate(cron_syntax)}


if __name__ == '__main__':
    with get_tg_client() as client, open(config_file) as conf:
        logger.info('Read pyCRONos.yml')
        config = yaml.safe_load(conf.read())


        def send_message(user, message):
            logger.info(f'Add action for subscriber "{user}": send "{message}"')
            try:
                user = int(user)  # group id presented as integers
            except ValueError:
                pass

            async def action():
                logger.info(f'Action for subscriber "{user}": send "{message}"')
                await client.send_message(user, message)

            return action


        scheduler = AsyncIOScheduler()
        subs = config['telegram']['subscribers']
        for (user, params) in subs.items():
            action = send_message(user, params.get('message'))
            scheduler.add_job(action, 'cron', **cron_to_apsched(params.get('cron')))
        logger.info(f'pyCRONos.pid = {os.getpid()}')
        scheduler.start()
        while True:
            try:
                asyncio.get_event_loop().run_forever()
            except Exception as e:
                logger.error(str(e))
