#!/usr/bin/env python3
from argparse import ArgumentParser
import shutil

from cfg import CONFIG
from lib import downloadPath, updateVersionMap, versionToInt


if __name__ == '__main__':
    cli = ArgumentParser()
    cli.add_argument('ipa', nargs='+')
    cli.add_argument('-m', '--move', action='store_true')
    args = cli.parse_args()
    max_os = versionToInt(CONFIG.max_os)

    for fname in args.ipa:
        info = updateVersionMap(fname)
        if args.move and versionToInt(info.osVer) <= max_os:
            download_path = downloadPath(info.appId, info.verId)
            shutil.move(fname, download_path)
