#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlopen

from cfg import CONFIG, Log


class WinApiServer():
    def __init__(self) -> None:
        self.server_url = CONFIG.win_server
        if self._post('up', '') != 'YES':
            raise RuntimeError(
                f'WinServer {self.server_url} does not seem to be running')

    def _post(self, action: str, data: str) -> str:
        ''' With 10min timeout '''
        url = f'{self.server_url}/{action}'
        Log.debug('POST %s --data %s', url, data)
        with urlopen(url, data=data.encode('utf8'), timeout=1200) as fp:
            return fp.read().decode('utf8')

    def install(self, fname: Path) -> str:
        if fname.suffix != '.ipa':
            raise ValueError(f'Not an *.ipa file: "{fname}"')
        if not fname.exists() or fname.is_dir():
            raise ValueError(f'File not found: "{fname}"')
        if fname.absolute().parent != CONFIG.sync_out.absolute():
            raise ValueError(f'Install file not in SYNC OUT dir: "{fname}"')
        return self._post('install', fname.name)

    def uninstall(self, bundleId: str) -> str:
        return self._post('uninstall', bundleId)


WinServer = WinApiServer()
