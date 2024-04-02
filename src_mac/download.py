#!/usr/bin/env python3
from cfg import CONFIG, Log
from lib import downloadAllUntil, enumAppIds
from repack_ipa import repackIpa


# findLatestVersion(000, CONFIG.max_os)
# downloadSpecificVersion(000, 000)
# exit(0)

appIds = list(enumAppIds())
# appIds = [000]

for i, appId in enumerate(appIds):
    Log.info('Checking [%d/%d] %s', i + 1, len(appIds), appId)
    for i in range(150):
        path = downloadAllUntil(i, appId, CONFIG.max_os, rmIncompatible=True)
        if path:
            repackIpa(path)

print('done.')
