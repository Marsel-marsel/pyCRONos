import os
from telethon.sync import TelegramClient
import argparse
from pprint import pprint
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
import yaml
import re
from sqlite3 import OperationalError

HOME = os.path.dirname(__file__)
api_hash_file = os.path.join(HOME, 'secrets', 'api_hash')
api_id_file = os.path.join(HOME, 'secrets', 'api_id')
config_file = os.path.join(HOME, 'pyCRONos.yml')
pid_file = os.path.join(HOME, 'pyCRONos.pid')
log_file = os.path.join(HOME, 'pyCRONos.log')

parser = argparse.ArgumentParser()
parser.add_argument("--list", help='list dialogs and ids', action="store_true")
parser.add_argument("--keepwatch", help='read pyCRONos.yml and start', action="store_true")
args = parser.parse_args()

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
            client = TelegramClient(session=os.path.join(HOME, 'pyCRONos.session'), api_id=api_id, api_hash=api_hash)
        else:
            client = TelegramClient('pyCRONos', api_id=api_id, api_hash=api_hash, sequential_updates=True)
    except OperationalError:
        with open(pid_file) as pid:
            logger.error(f'Telegram Client is running, please execute: kill {pid.read()}')
            exit(1)
    return client


def cron_to_apsched(cron):
    cron = re.sub(' +', ' ', cron).split(' ')
    dict = {}
    for i, option in enumerate(['minute', 'hour', 'day', 'month', 'day_of_week']):
        dict[option] = cron[i]
    logger.info(f'{cron} converted to {dict}')
    return dict


if __name__ == '__main__':
    with get_tg_client() as client:
        if args.list:
            logger.info('Get list of contacts')
            pprint([(d.name, d.id) for d in client.get_dialogs()])
        elif args.keepwatch:
            dialogs = client.get_dialogs()
            logger.info('Read pyCRONos.yml')
            with open(config_file) as f:
                config = yaml.safe_load(f.read())


            def send_message(id, message, **kwargs):
                global dialogs
                dialog = [d for d in dialogs if d.id == id][0]

                def action():
                    logger.info(f'Action for subscriber "{dialog.name}" with id {id}: send "{message}"')
                    dialog.send_message(f'{message}')

                return action


            scheduler = BlockingScheduler()
            scheduler.add_executor('processpool')
            for id, args in config['telegram']['subscribers'].items():
                logger.info(f'Add job {id}: {args}')
                action = send_message(id, **args)
                scheduler.add_job(f'{__name__}:{action.__name__}', 'cron', **cron_to_apsched(args['cron']))
            with open(pid_file, 'w') as pidfile:
                pidfile.write(str(os.getpid()))
                logger.info(f'pyCRONos.pid = {os.getpid()}')
            scheduler.start()
