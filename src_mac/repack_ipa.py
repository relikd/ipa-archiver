#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
from subprocess import run
from zipfile import ZipFile
import os
import re
import shutil

from cfg import CONFIG, Log

_rx_coh = re.compile(r'\s*<key>storeCohort<\/key>\s*<string>[^<]*<\/string>')


def cleanupZipDir(path: Path):
    if (path / 'IPAToolInfo.plist').exists():
        os.remove(path / 'IPAToolInfo.plist')
    shutil.rmtree(path / 'META-INF', ignore_errors=True)

    if CONFIG.convert_plist:
        ii = next((path / 'Payload').glob('*.app')) / 'Info.plist'
        run(f'/usr/libexec/PlistBuddy -x -c print {ii} > {ii}.tmp', shell=True)
        os.remove(ii)
        os.rename(f'{ii}.tmp', ii)

    with open(path / 'iTunesMetadata.plist', 'r') as fp:
        data = fp.read()
        start, end = _rx_coh.search(data).span()  # type: ignore assume exist
    with open(path / 'iTunesMetadata.plist', 'w') as fp:
        fp.write(data[:start])
        fp.write(data[end:])


def repackIpa(ipa_path: Path):
    is_dir = ipa_path.is_dir() and (ipa_path / 'IPAToolInfo.plist').exists()
    tmp_unzip_dir = ipa_path if is_dir else Path('tmp_unzip')

    target_path = CONFIG.sync_out / ipa_path.name
    if is_dir:  # in case of manual extraction (needed for utf8 filenames)
        just_app_ver_id = target_path.name.split(' ', 1)[0]  # " 2" or " copy"
        target_path = target_path.with_name(just_app_ver_id + '.ipa')
    if target_path.exists():
        return

    if ipa_path.is_file():
        Log.info('[unzip] %s', ipa_path)
        shutil.rmtree(tmp_unzip_dir, ignore_errors=True)
        tmp_unzip_dir.mkdir(exist_ok=True)

        with ZipFile(ipa_path) as zip:
            zip.extractall(tmp_unzip_dir)
    else:
        Log.info('[repack-dir] %s', ipa_path)

    cleanupZipDir(tmp_unzip_dir)

    Log.info('[zip] %s', target_path)
    shutil.make_archive(str(target_path), 'zip', str(tmp_unzip_dir))
    shutil.move(str(target_path) + '.zip', str(target_path))
    shutil.rmtree(tmp_unzip_dir, ignore_errors=True)


if __name__ == '__main__':
    cli = ArgumentParser()
    cli.add_argument('ipa', type=Path, nargs='+')
    args = cli.parse_args()

    for fname in args.ipa:
        repackIpa(fname)
