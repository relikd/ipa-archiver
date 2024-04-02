#!/usr/bin/env python3
from configparser import ConfigParser
from pathlib import Path
import logging
import os

os.chdir(Path(__file__).parent.parent)

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    level=logging.INFO)
Log = logging.getLogger('main')


class Cfg():
    def __init__(self) -> None:
        cfg = ConfigParser()
        cfg.read('config.ini')
        # [main]
        self.itunes_server = cfg.get('main', 'itunes_server')
        self.win_server = cfg.get('main', 'win_server')
        self.ssh_cmd_crack = cfg.get('main', 'ssh_cmd_crack')
        self.ssh_cmd_sync = cfg.get('main', 'ssh_cmd_sync')
        self.max_os = cfg.get('main', 'max_os')
        # [zip]
        self.convert_plist = cfg.getboolean('zip', 'convert_binary_plist')
        # [paths]
        self.sync_in = Path(cfg.get('paths', 'sync_in'))
        self.sync_out = Path(cfg.get('paths', 'sync_out'))
        self.completed = Path(cfg.get('paths', 'complete'))
        self.download_fix = Path(cfg.get('paths', 'download_fix'))
        self.download_tmp = Path(cfg.get('paths', 'download_tmp'))
        # config validation
        for path in [self.sync_in, self.sync_out, self.completed]:
            if not path.exists():
                raise FileNotFoundError(f'Directory "{path}" does not exist.')
        # create dirs
        self.download_fix.mkdir(parents=True, exist_ok=True)
        self.download_tmp.mkdir(parents=True, exist_ok=True)

    def __str__(self):
        return str(self.__dict__)


CONFIG = Cfg()
# print(CONFIG)
