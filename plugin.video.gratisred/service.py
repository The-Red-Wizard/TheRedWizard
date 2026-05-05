# -*- coding: utf-8 -*-

import threading

from resources.lib.modules import control
from resources.lib.modules import log_utils


def syncTraktLibrary():
    try:
        control.execute('RunPlugin(plugin://%s)' % 'plugin.video.gratisred/?action=movies_to_library_silent&url=trakt_collection')
        control.execute('RunPlugin(plugin://%s)' % 'plugin.video.gratisred/?action=tvshows_to_library_silent&url=trakt_collection')
        log_utils.log('Trakt Library Sync Successful.')
    except Exception:
        log_utils.log('syncTraktLibrary', 1)
        pass


try:
    control.execute('RunPlugin(plugin://%s)' % 'plugin.video.gratisred/?action=service')
    log_utils.log('Service Process Successful.')
except Exception:
    log_utils.log('Service Process Failed.', 1)
    pass


try:
    from resources.lib.modules import changelog_notice
    changelog_notice.service_check()
except Exception:
    log_utils.log('Changelog Notice Check Failed.', 1)
    pass


try:
    if control.setting('trakt.sync') == 'true':
        synctime = control.setting('trakt.synctime') or '0'
        if int(synctime) > 0:
            timeout = 3600 * int(synctime)
            log_utils.log('Trakt Library Sync Delayed: ' + str(synctime) + ' Hours.')
            schedTrakt = threading.Timer(timeout, syncTraktLibrary)
            schedTrakt.start()
        else:
            syncTraktLibrary()
except Exception:
    log_utils.log('Trakt Library Sync Failed.', 1)
    pass


