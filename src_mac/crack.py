#!/usr/bin/env python3
from subprocess import Popen
from time import sleep
import os

from cfg import CONFIG, Log
from move_em import moveEmAll
from server import WinServer


print('Start cracking ...')
while True:
    file = next(CONFIG.sync_out.glob('*.ipa'), None)

    if not file:
        print('Nothing to do. Retry in 10s ...')
        sleep(10)
        continue

    Log.info('[install] %s ...', file.name)
    WinServer.install(file)

    Log.info('[crack] %s ...', file.name)
    shell = Popen(CONFIG.ssh_cmd_crack, shell=True)
    if shell.wait() != 0:
        raise RuntimeError('Error during cracking command')

    Log.info('[pull] %s ...', file.name)
    shell = Popen(CONFIG.ssh_cmd_sync, shell=True)
    if shell.wait() != 0:
        raise RuntimeError('Error during sync-download')

    Log.info('[delete] %s', file.name)
    os.remove(file)  # file on sync_out dir

    moveEmAll()
