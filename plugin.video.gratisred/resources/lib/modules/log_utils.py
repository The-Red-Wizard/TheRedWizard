# -*- coding: utf-8 -*-

import os
import six
import traceback

from datetime import datetime
from io import open
from kodi_six import xbmc
from resources.lib.modules import control

LOGDEBUG = xbmc.LOGDEBUG
LOGINFO = xbmc.LOGINFO
LOGNOTICE = xbmc.LOGNOTICE if control.getKodiVersion() < 19 else xbmc.LOGINFO
LOGWARNING = xbmc.LOGWARNING
LOGERROR = xbmc.LOGERROR
LOGFATAL = xbmc.LOGFATAL
LOGNONE = xbmc.LOGNONE

version = control.addonInfo('version')
ChangeLog_head = '-- Gratis Red Changelog --' #% version
Scrubsv2Log_head = '-- Gratis Red Current Version - v%s --' % version
DebugLog_head = '--[Gratis Red - %s - DebugLog]--' % version
DEBUGPREFIX = '[Gratis Red - %s - DEBUG]' % version

LOGPATH = control.transPath('special://logpath/')
log_file = os.path.join(LOGPATH, 'changelog.log')
changelogfile = os.path.join(control.addonPath, 'resources', 'changelog.txt')

LOGPATH = control.transPath('special://logpath/')
log_file = os.path.join(LOGPATH, 'scrubsv2.log')
scrubsv2_changelogfile = os.path.join(control.addonPath, 'resources', 'scrubsv2-changelog.txt')

debug_enabled = control.setting('addon.debug')
debugtime_enabled = control.setting('addon.debugtime')
debugspacer_enabled = control.setting('addon.debugspacer')


def log(msg, trace=0, level=LOGDEBUG):
    if not debug_enabled == 'true':
        return
    try:
        if trace == 1:
            failure = six.ensure_str(traceback.format_exc())
            _msg = '%s: %s' % (six.ensure_text(msg), failure)
        else:
            _msg = '%s' % six.ensure_text(msg)
        if not os.path.exists(log_file):
            f = open(log_file, 'w')
            f.close()
        with open(log_file, 'a', encoding='utf-8') as f:
            if not debugtime_enabled == 'true':
                line = '%s: %s' % (DEBUGPREFIX, _msg)
            else:
                line = '[%s %s] %s: %s' % (datetime.now().date(), str(datetime.now().time())[:8], DEBUGPREFIX, _msg)
            if not debugspacer_enabled == 'true':
                f.write(line.rstrip('\r\n') + '\n')
            else:
                f.write('' + '\n')
                f.write(line.rstrip('\r\n') + '\n')
                f.write('' + '\n')
    except Exception as e:
        xbmc.log('%s Logging Failure: %s' % (DEBUGPREFIX, e), level)
        pass


def changelog():
    try:
        control.textViewer(changelogfile, ChangeLog_head)
    except:
        log('changelog', 1)
        control.infoDialog('Error opening Changelog')
        pass


def scrubsv2_changelog():
    try:
        control.textViewer(scrubsv2_changelogfile, Scrubsv2Log_head)
    except:
        log('changelog', 1)
        control.infoDialog('Error opening Scrubs v2 Changelog')
        pass


def view_log():
    try:
        control.textViewer(log_file, DebugLog_head)
    except:
        log('view_log', 1)
        control.infoDialog('Error opening log file')
        pass


def empty_log():
    try:
        open(log_file, 'w').close()
    except:
        log('empty_log', 1)
        control.infoDialog('Error emptying log file')
        pass


