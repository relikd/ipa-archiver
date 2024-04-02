#!/usr/bin/env python3
from pathlib import Path
import os
import shutil

from cfg import CONFIG, Log
from lib import ipaReadInfoPlist
from server import WinServer


def moveEmAll():
    for fname in CONFIG.sync_in.glob('*.ipa'):
        info = ipaReadInfoPlist(Path(fname))
        FROM = Path(fname)
        new_name = FROM.name[:-4] + f' - {info.verId}.ipa'
        DEST = next(CONFIG.completed.glob(f'{info.bundleId} */')) / new_name
        Log.info('[mv] -> %s', DEST.name)
        shutil.move(FROM.as_posix(), DEST)

        # cleanup download files
        orig_filename = f'{info.appId}.{info.verId}.ipa'
        download_file = CONFIG.download_fix / orig_filename
        if download_file.exists():
            Log.info('[delete] %s', download_file)
            os.remove(download_file)

        Log.info('[uninstall] %s', info.bundleId)
        WinServer.uninstall(info.bundleId)


if __name__ == '__main__':
    moveEmAll()
