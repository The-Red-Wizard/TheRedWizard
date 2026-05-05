# -*- coding: utf-8 -*-
"""
Changelog Notice
----------------
On addon startup (service.py) we compare the stored 'addon.lastversion' with
the current addon version. When they differ, we display a blocking textviewer
containing resources/changelog.txt. The user MUST click OK to dismiss.

Two dismissal mechanisms are provided so the user can't miss it:
  1. A modal textviewer dialog on first launch after an update.
  2. A persistent 'What's New' entry prepended to the addon root menu, which
     stays visible until the user opens it (same dialog) or clicks "Dismiss".

After the user dismisses, 'addon.lastversion' is written so we don't prompt
again until the next version bump.
"""

import os

from kodi_six import xbmcgui, xbmcaddon

from resources.lib.modules import control
from resources.lib.modules import log_utils


def _current_version():
    try:
        return xbmcaddon.Addon().getAddonInfo('version') or ''
    except Exception:
        return ''


def _stored_version():
    try:
        return control.setting('addon.lastversion') or ''
    except Exception:
        return ''


def _write_stored_version(ver):
    try:
        control.setSetting('addon.lastversion', ver)
        control.setSetting('addon.changelog.dismissed', 'true')
    except Exception:
        log_utils.log('changelog_notice: failed to persist lastversion', 1)


def _read_changelog():
    path = os.path.join(control.addonPath, 'resources', 'changelog.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception:
            return ''


def has_pending_notice():
    """True if current version != stored version OR user hasn't dismissed yet."""
    cur = _current_version()
    stored = _stored_version()
    dismissed = (control.setting('addon.changelog.dismissed') == 'true')
    if cur and cur != stored:
        return True
    if not dismissed:
        return True
    return False


def show(force=False, auto_dismiss=True):
    """Show the changelog dialog. If force=True, ignore the 'same version' check."""
    if not force and not has_pending_notice():
        return
    body = _read_changelog() or 'No changelog found.'
    heading = '[COLOR red]-- Gratis Red - What\'s New (v%s) --[/COLOR]' % _current_version()
    try:
        xbmcgui.Dialog().textviewer(heading, body)
    except Exception:
        control.okDialog(body[:4000], heading)

    if auto_dismiss:
        _write_stored_version(_current_version())


def dismiss_only():
    """Silently dismiss without showing (used from the menu entry 'Dismiss')."""
    _write_stored_version(_current_version())


def service_check():
    """Called from service.py. Non-blocking trigger via RunPlugin if needed."""
    try:
        if has_pending_notice():
            # Use RunPlugin so the dialog renders in the GUI thread after startup.
            control.execute('RunPlugin(plugin://%s/?action=show_changelog)' % 'plugin.video.gratisred')
            log_utils.log('changelog_notice: scheduled new-version notice')
    except Exception:
        log_utils.log('changelog_notice: service_check failed', 1)
