#!/usr/bin/env python3
from pathlib import Path
from subprocess import run
from typing import Dict, NamedTuple
from zipfile import ZipFile
import json
import os
import plistlib
import shutil

from cfg import CONFIG, Log


# ------------------------------
# Types
# ------------------------------


VersionMap = Dict[int, str]


class FlatVersion(NamedTuple):
    verId: int
    verOs: int


class InfoPlist(NamedTuple):
    appId: int
    verId: int
    allVersions: 'list[int]'
    bundleId: str
    osVer: str


class LocalIpaFile(NamedTuple):
    cracked: bool
    path: Path


# ------------------------------
# IPA tool
# ------------------------------

def ipaTool(*args: 'str|Path') -> None:
    # '--json'
    run(['python3', Path(__file__).parent/'ipatool-py'/'main.py'] + list(args))


def ipaToolHistory(appId: int):
    Log.info('history for appid=%d', appId)
    ipaTool('historyver', '-s', CONFIG.itunes_server,
            '-o', CONFIG.download_tmp, '-i', str(appId))


def ipaToolDownload(appId: int, verId: int):
    Log.info('download appid=%d verid=%d', appId, verId)
    ipaTool('download', '-s', CONFIG.itunes_server, '-o', CONFIG.download_tmp,
            '-i', str(appId), '--appVerId', str(verId))


# ------------------------------
# Path handling
# ------------------------------

def pathForApp(appId: int) -> 'Path|None':
    return next(CONFIG.completed.glob(f'* - {appId}/'), None)


def pathForIpa(appId: int, appVerId: int) -> 'Path|None':
    app_path = pathForApp(appId)
    if not app_path:
        return None
    return next(app_path.glob(f'* - {appVerId}.ipa'), None)


# ------------------------------
# IPA content reading
# ------------------------------

def ipaReadInfoPlist(fname: Path) -> InfoPlist:
    with ZipFile(fname) as zip:
        itunesPlist = plistlib.loads(zip.read('iTunesMetadata.plist'))
        for entry in zip.filelist:
            p = entry.filename.split('/')
            if len(p) == 3 and p[0] == 'Payload' and p[2] == 'Info.plist':
                infoPlist = plistlib.loads(zip.read(entry))
                break
    return InfoPlist(
        itunesPlist['itemId'],
        itunesPlist['softwareVersionExternalIdentifier'],
        itunesPlist['softwareVersionExternalIdentifiers'],
        # itunesPlist['softwareVersionBundleId']
        infoPlist['CFBundleIdentifier'],
        infoPlist.get('MinimumOSVersion', '1.0'),
    )


# ------------------------------
# Version Map
# ------------------------------

def readVersionMap(appId: int) -> 'VersionMap|None':
    app_dir = pathForApp(appId)
    if app_dir:
        ver_map_json = app_dir / '_versions.json'
        if ver_map_json.exists():
            with open(ver_map_json, 'rb') as fp:
                data: dict[str, str] = json.load(fp)
                return {int(k): v for k, v in data.items()}
    return None


def readVersionMapFromTemp(appId: int) -> 'VersionMap|None':
    hist_json = CONFIG.download_tmp / f'historyver_{appId}.json'
    if hist_json.exists():
        with open(hist_json, 'rb') as fp:
            allVerIds: list[int] = json.load(fp)['appVerIds']
        return {x: '' for x in allVerIds}
    return None


def writeVersionMap(appId: int, data: VersionMap):
    app_dir = pathForApp(appId)
    assert app_dir, f'app dir must exist for {appId} before calling this.'

    with open(app_dir / '_versions.json', 'w') as fp:
        json.dump(data, fp, indent=2, sort_keys=True)

    hist_json = CONFIG.download_tmp / f'historyver_{appId}.json'
    if hist_json.exists():
        os.remove(hist_json)


def updateVersionMap(fname: Path) -> InfoPlist:
    ''' Returns iOS version string '''
    info = ipaReadInfoPlist(fname)
    if not pathForApp(info.appId):
        app_dir = CONFIG.completed / f'{info.bundleId} - {info.appId}'
        app_dir.mkdir(parents=True, exist_ok=True)
    data = readVersionMap(info.appId)
    if not data:
        data = readVersionMapFromTemp(info.appId)
    if not data:
        data: 'VersionMap|None' = {x: '' for x in info.allVersions}

    assert data, f'by now, history json for {info.appId} should exist!'

    if data.get(info.verId) != info.osVer:
        for x in info.allVersions:
            if x not in data:
                data[x] = ''
        data[info.verId] = info.osVer
        Log.info('update version for %s (%s)', info.appId, info.bundleId)
        writeVersionMap(info.appId, data)
    return info


def flattenVersionMap(data: VersionMap) -> 'list[FlatVersion]':
    return sorted(FlatVersion(k, versionToInt(v)) for k, v in data.items())


def loadFlatVersionMap(appId: int) -> 'list[FlatVersion]':
    data = readVersionMap(appId)
    if not data:
        data = readVersionMapFromTemp(appId)
    if not data:  # needs download
        ipaToolHistory(appId)
        data = readVersionMapFromTemp(appId)
    if not data:
        raise RuntimeError(f'could not download version history for {appId}')
    return flattenVersionMap(data)


# ------------------------------
# Helper
# ------------------------------

def versionToInt(ver: str) -> int:
    if not ver:
        return 0
    major, minor, patch, *_ = ver.split('.') + [0, 0, 0]
    return int(major) * 1_00_00 + int(minor) * 1_00 + int(patch)


def enumAppIds():
    return sorted([int(x.parent.name.split(' ')[-1])
                   for x in CONFIG.completed.glob('*/_versions.json')])


def downloadPath(appId: int, verId: int):
    return CONFIG.download_fix / f'{appId}.{verId}.ipa'


# ------------------------------
# Actual logic
# ------------------------------

def downloadSpecificVersion(appId: int, verId: int) -> LocalIpaFile:
    ipa_path = pathForIpa(appId, verId)
    if ipa_path:
        return LocalIpaFile(True, ipa_path)  # already cracked

    download_path = downloadPath(appId, verId)
    if download_path.exists():
        return LocalIpaFile(False, download_path)  # needs cracking

    ipaToolDownload(appId, verId)
    tmp_file = next(CONFIG.download_tmp.glob(f'*-{appId}-{verId}.ipa'), None)
    if not tmp_file:
        raise RuntimeError(f'Could not download ipa {appId} {verId}')

    shutil.move(tmp_file.as_posix(), download_path)
    updateVersionMap(download_path)
    return LocalIpaFile(False, download_path)


def findLatestVersion(
    appId: int, maxOS: str, *, rmIncompatible: bool
) -> 'int|None':
    ver_map = loadFlatVersionMap(appId)
    _maxOS = versionToInt(maxOS)

    def proc_index(i: int) -> bool:
        verId, osVer = ver_map[i]
        if not osVer:
            ipa_file = downloadSpecificVersion(appId, verId)
            info = ipaReadInfoPlist(ipa_file.path)
            osVer = versionToInt(info.osVer)
            if rmIncompatible and osVer > _maxOS and not ipa_file.cracked:
                os.remove(ipa_file.path)
        Log.debug('app: %d ver: %d iOS: %s ...', appId, verId, osVer)
        return osVer <= _maxOS

    if not proc_index(0):
        Log.warning(f'No compatible version for {appId}')
        return None

    imin, imax = 1, len(ver_map) - 1
    best_i = 0
    while imin <= imax:
        i = imin + (imax - imin) // 2
        if proc_index(i):
            best_i = i
            imin = i + 1
        else:
            best_i = i - 1
            imax = i - 1
    return ver_map[best_i].verId


def downloadAllUntil(
    idx: int, appId: int, maxOS: str, *, rmIncompatible: bool
) -> 'Path|None':
    ver_map = loadFlatVersionMap(appId)
    _maxOS = versionToInt(maxOS)
    if idx >= len(ver_map):
        return None
    if any(x.verOs > _maxOS for x in ver_map[:idx + 1]):
        return None
    verId = ver_map[idx].verId
    ipa_file = downloadSpecificVersion(appId, verId)
    if ipa_file.cracked:
        return None
    info = ipaReadInfoPlist(ipa_file.path)
    osVer = versionToInt(info.osVer)
    if osVer <= _maxOS:
        return ipa_file.path
    elif rmIncompatible:
        os.remove(ipa_file.path)
