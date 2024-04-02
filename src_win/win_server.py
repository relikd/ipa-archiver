#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
import socket
import subprocess

os.chdir(Path(__file__).parent)
INSTALLER = Path('libimobiledevice', 'ideviceinstaller.exe')
PATH_IN = Path('queued')


class IpaServer(BaseHTTPRequestHandler):
    def reply(self, status: int, data: str):
        self.send_response(status)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(data.encode('utf8'))

    def do_POST(self):
        length = self.headers.get('Content-Length', 1)
        data = self.rfile.read(int(length)).decode('utf8')
        if self.path == '/up':
            return self.reply(200, 'YES')
        elif self.path == '/install':
            fname = PATH_IN / data
            if not fname.exists():
                return self.reply(404, f'File not found "{fname}"')
            subprocess.run([INSTALLER, '-i', fname])
        elif self.path == '/uninstall':
            bundleId = data
            subprocess.run([INSTALLER, '-U', bundleId], timeout=60)
        else:
            raise ValueError('unsuppoted API path')
        return self.reply(200, 'OK')


def getLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('10.255.255.255', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


if __name__ == '__main__':
    webServer = HTTPServer(('0.0.0.0', 8117), IpaServer)
    print('Server started http://%s:%s' % (getLocalIp(), 8117))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
