# -*- coding: utf-8 -*-

import os
import sys
import traceback

import six
from six.moves import urllib_parse
from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs


def six_encode(txt, char='utf-8', errors='replace'):
    if six.PY2 and isinstance(txt, six.text_type):
        txt = txt.encode(char, errors=errors)
    return txt


def six_decode(txt, char='utf-8', errors='replace'):
    if six.PY3 and isinstance(txt, six.binary_type):
        txt = txt.decode(char, errors=errors)
    return txt


def getKodiVersion():
    return int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])


addon = xbmcaddon.Addon
addonInfo = xbmcaddon.Addon().getAddonInfo

lang = xbmcaddon.Addon().getLocalizedString
lang2 = xbmc.getLocalizedString

setting = xbmcaddon.Addon().getSetting
setSetting = xbmcaddon.Addon().setSetting

addItem = xbmcplugin.addDirectoryItem
addItems = xbmcplugin.addDirectoryItems

item = xbmcgui.ListItem
directory = xbmcplugin.endOfDirectory

content = xbmcplugin.setContent
property = xbmcplugin.setProperty

infoLabel = xbmc.getInfoLabel

condVisibility = xbmc.getCondVisibility

jsonrpc = xbmc.executeJSONRPC

dialog = xbmcgui.Dialog()
progressDialog = xbmcgui.DialogProgress()
progressDialogBG = xbmcgui.DialogProgressBG()
window = xbmcgui.Window(10000)
windowDialog = xbmcgui.WindowDialog()

button = xbmcgui.ControlButton

image = xbmcgui.ControlImage

getCurrentDialogId = xbmcgui.getCurrentWindowDialogId()
getCurrentWinId = xbmcgui.getCurrentWindowId()

keyboard = xbmc.Keyboard

monitor = xbmc.Monitor()

execute = xbmc.executebuiltin

skin = xbmc.getSkinDir()

player = xbmc.Player()
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
resolve = xbmcplugin.setResolvedUrl

legalFilename = xbmc.makeLegalFilename if getKodiVersion() < 19 else xbmcvfs.makeLegalFilename

openFile = xbmcvfs.File
makeFile = xbmcvfs.mkdir
deleteFile = xbmcvfs.delete

deleteDir = xbmcvfs.rmdir
listDir = xbmcvfs.listdir

transPath = xbmc.translatePath if getKodiVersion() < 19 else xbmcvfs.translatePath
#transPath = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
addonPath = transPath(addonInfo('path'))
dataPath = transPath(addonInfo('profile'))
skinPath = transPath('special://skin/')

cacheFile = os.path.join(dataPath, 'cache.db')
viewsFile = os.path.join(dataPath, 'views.db')
metacacheFile = os.path.join(dataPath, 'meta.db')
searchFile = os.path.join(dataPath, 'search.db')
libcacheFile = os.path.join(dataPath, 'library.db')
bookmarksFile = os.path.join(dataPath, 'bookmarks.db')
favoritesFile = os.path.join(dataPath, 'favorites.db')
progressFile = os.path.join(dataPath, 'progress.db')
providercacheFile = os.path.join(dataPath, 'providers.db')

settingsPath = os.path.join(addonPath, 'resources', 'settings.xml')
settingsFile = os.path.join(dataPath, 'settings.xml')

key = "RgUkXp2s5v8x/A?D(G+KbPeShVmYq3t6"
iv = "p2s5v8y/B?E(H+Mb"
integer = 1000

notifcations_disabled = setting('addon.notifcations')


def sleep(time):
    while time > 0 and not monitor.abortRequested():
        xbmc.sleep(min(100, time))
        time = time - 100


def addonId():
    return addonInfo('id')


def addonName():
    return addonInfo('name')


def appearance():
    appearance = setting('theme.1').lower() if condVisibility('System.HasAddon(script.gratisred.artwork)') else setting('theme.alt').lower()
    return appearance


def artPath():
    theme = appearance()
    if theme in ['-', '']:
        return
    elif condVisibility('System.HasAddon(script.gratisred.artwork)'):
        return os.path.join(xbmcaddon.Addon('script.gratisred.artwork').getAddonInfo('path'), 'resources', 'media', theme)


def artwork():
    execute('RunPlugin(plugin://script.gratisred.artwork)')


def addonIcon():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'icon.png')
    return addonInfo('icon')


def addonThumb():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'poster.png')
    elif theme == '-':
        return 'DefaultFolder.png'
    return addonInfo('icon')


def addonPoster():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'poster.png')
    return 'DefaultVideo.png'


def addonBanner():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'banner.png')
    return 'DefaultVideo.png'


def addonFanart():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'fanart.jpg')
    return addonInfo('fanart')


def addonNext():
    theme = appearance()
    art = artPath()
    if not (art == None and theme in ['-', '']):
        return os.path.join(art, 'next.png')
    return 'DefaultVideo.png'


def getCurrentViewId():
    win = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return str(win.getFocusId())


def moderator():
    try:
        white_list = [urllib_parse.urlparse(sys.argv[0]).netloc, '', 'plugin.video.metalliq', 'script.extendedinfo',
            'plugin.program.super.favourites', 'plugin.video.openmeta', 'plugin.video.themoviedb.helper'
        ]
        plugin_name = infoLabel('Container.PluginName')
        if not plugin_name in white_list:
            xbmc.log('Gratis Red Moderator Blockage: %s (Contact me with this line if you feel its a error.)' % plugin_name, xbmc.LOGWARNING)
            sys.exit()
    except Exception as error:
        xbmc.log('Gratis Red Moderator Failure: %s' % error, xbmc.LOGDEBUG)


def version():
    num = ''
    try:
        version = addon('xbmc.addon').getAddonInfo('version')
    except:
        version = '999'
    for i in version:
        if i.isdigit():
            num += i
        else:
            break
    return int(num)


def idle():
    if getKodiVersion() >= 18:
        return execute('Dialog.Close(busydialognocancel)')
    else:
        return execute('Dialog.Close(busydialog)')


def busy():
    if getKodiVersion() >= 18:
        return execute('ActivateWindow(busydialognocancel)')
    else:
        return execute('ActivateWindow(busydialog)')


def refresh():
    return execute('Container.Refresh')


def queueItem():
    return execute('Action(Queue)')


def yesnoDialog(message, heading=addonInfo('name'), nolabel='', yeslabel=''):
    if getKodiVersion() < 19:
        return dialog.yesno(heading, message, '', '', nolabel, yeslabel)
    else:
        return dialog.yesno(heading, message, nolabel, yeslabel)


def okDialog(message, heading=addonInfo('name')):
    return dialog.ok(heading, message)


def selectDialog(list, heading=addonInfo('name'), useDetails=False):
    if getKodiVersion() >= 17:
        return dialog.select(heading, list, useDetails=useDetails)
    else:
        return dialog.select(heading, list)


def multiselectDialog(list, heading=addonInfo('name'), useDetails=False):
    if getKodiVersion() >= 17:
        return dialog.multiselect(heading, list, useDetails=useDetails)
    else:
        return dialog.multiselect(heading, list)


def contextmenuDialog(list):
    return dialog.contextmenu(list)


def infoDialog(message, heading=addonInfo('name'), icon='', time=3000, sound=False):
    if notifcations_disabled == 'true':
        return
    if icon == '':
        icon = addonIcon()
    elif icon == 'INFO':
        icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING':
        icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR':
        icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, icon, time, sound=sound)


def textViewer(file, heading=addonInfo('name'), monofont=True):
    sleep(200)
    if not os.path.exists(file):
        w = open(file, 'w')
        w.close()
    with open(file, 'rb') as r:
        text = r.read()
    if not text:
        text = ' '
    head = '[COLOR red][B]%s[/B][/COLOR]' % six.ensure_str(heading, errors='replace')
    if getKodiVersion() >= 18:
        return dialog.textviewer(head, text, monofont)
    else:
        return dialog.textviewer(head, text)


def textViewer2(text, heading=addonInfo('name'), monofont=True):
    sleep(200)
    if not text:
        text = 'Error, Something Went Wrong.'
    head = '[COLOR red][B]%s[/B][/COLOR]' % six.ensure_str(heading, errors='replace')
    if getKodiVersion() >= 18:
        return dialog.textviewer(head, text, monofont)
    else:
        return dialog.textviewer(head, text)


def metadataClean(metadata):
    if metadata == None:
        return metadata
    allowed = ['aired', 'album', 'artist', 'cast',
        'castandrole', 'code', 'country', 'credits', 'dateadded', 'dbid', 'director',
        'duration', 'episode', 'episodeguide', 'genre', 'imdbnumber', 'lastplayed',
        'mediatype', 'mpaa', 'originaltitle', 'overlay', 'path', 'playcount', 'plot',
        'plotoutline', 'premiered', 'rating', 'season', 'set', 'setid', 'setoverview',
        'showlink', 'sortepisode', 'sortseason', 'sorttitle', 'status', 'studio', 'tag',
        'tagline', 'title', 'top250', 'totalepisodes', 'totalteasons', 'tracknumber',
        'trailer', 'tvshowtitle', 'userrating', 'votes', 'watched', 'writer', 'year'
    ]
    return {k: v for k, v in six.iteritems(metadata) if k in allowed}


def apiLanguage(ret_name=None):
    langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs',
        'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Finnish': 'fi', 'French': 'fr',
        'German': 'de', 'Greek': 'el', 'Hebrew': 'he', 'Hungarian': 'hu', 'Italian': 'it',
        'Japanese': 'ja', 'Korean': 'ko', 'Norwegian': 'no', 'Polish': 'pl', 'Portuguese': 'pt',
        'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk', 'Slovenian': 'sl',
        'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'
    }
    trakt = ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja',
        'ko', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'sk', 'sl', 'sr', 'sv', 'th', 'tr', 'uk', 'zh'
    ]
    tvdb = ['cs', 'da', 'de', 'el', 'en', 'es', 'fi', 'fr', 'he', 'hr', 'hu', 'it', 'ja',
        'ko', 'nl', 'no', 'pl', 'pt', 'ru', 'sl', 'sv', 'tr', 'zh'
    ]
    youtube = ['aa', 'ab', 'ae', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az', 'ba',
        'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs', 'ca', 'ce', 'ch', 'co', 'cr',
        'cs', 'cu', 'cv', 'cy', 'da', 'de', 'dv', 'dz', 'ee', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv',
        'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz', 'ia', 'id', 'ie', 'ig', 'ii',
        'ik', 'io', 'is', 'it', 'iu', 'ja', 'jv', 'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km',
        'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky', 'la', 'lb', 'lg', 'li', 'ln', 'lo',
        'lt', 'lu', 'lv', 'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my', 'na',
        'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv', 'ny', 'oc', 'oj', 'om', 'or',
        'os', 'pa', 'pi', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'rw', 'sa', 'sc',
        'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su',
        'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt',
        'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'wo', 'xh', 'yi', 'yo',
        'za', 'zh', 'zu'
    ]
    tmdb = ['ar', 'be', 'bg', 'bn', 'ca', 'ch', 'cs', 'da', 'de', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi', 'hu', 'id', 'it', 'ja', 'ka', 'kk', 'kn',
        'ko', 'lt', 'lv', 'ml', 'ms', 'nb', 'nl', 'no', 'pl', 'pt', 'ro', 'ru', 'si', 'sk',
        'sl', 'sr', 'sv', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'vi', 'zh', 'zu-ZA'
    ]
    name = None
    name = setting('api.language')
    if not name:
        name = 'AUTO'
    if name[-1].isupper():
        try:
            name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
        except:
            pass
    try:
        name = langDict[name]
    except:
        name = 'en'
    lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
    lang['tvdb'] = name if name in tvdb else 'en'
    lang['youtube'] = name if name in youtube else 'en'
    lang['tmdb'] = name if name in tmdb else 'en'
    if ret_name:
        lang['trakt'] = [i[0] for i in six.iteritems(langDict)if i[1] == lang['trakt']][0]
        lang['tvdb'] = [i[0] for i in six.iteritems(langDict) if i[1] == lang['tvdb']][0]
        lang['youtube'] = [i[0] for i in six.iteritems(langDict) if i[1] == lang['youtube']][0]
        lang['tmdb'] = [i[0] for i in six.iteritems(langDict) if i[1] == lang['tmdb']][0]
    return lang


def platform():
    if xbmc.getCondVisibility('system.platform.android'):
        return 'android'
    elif xbmc.getCondVisibility('system.platform.linux'):
        return 'linux'
    elif xbmc.getCondVisibility('system.platform.windows'):
        return 'windows'
    elif xbmc.getCondVisibility('system.platform.osx'):
        return 'osx'
    elif xbmc.getCondVisibility('system.platform.atv2'):
        return 'atv2'
    elif xbmc.getCondVisibility('system.platform.ios'):
        return 'ios'


def openBrowser(link):
    myplatform = platform()
    if myplatform == 'android':
        mycommand = 'StartAndroidActivity(,android.intent.action.VIEW,,%s)'
        return xbmc.executebuiltin(mycommand % link)
    else:
        import webbrowser
        return webbrowser.open(link)


def copy2clip(txt):
    platform = sys.platform
    if platform == 'win32':
        try:
            import subprocess
            cmd = 'echo %s|clip' % txt.strip()
            return subprocess.check_call(cmd, shell=True)
        except:
            pass
    elif platform == 'linux2':
        try:
            from subprocess import PIPE, Popen
            p = Popen(['xsel', '-pi'], stdin=PIPE)
            p.communicate(input=txt)
        except:
            pass


def openSettings(query=None, id=None):
    try:
        id = addonInfo('id') if id == None else id
        idle()
        execute('Addon.OpenSettings(%s)' % id)
        if query == None:
            raise Exception()
        c, f = query.split('.')
        if getKodiVersion() >= 18:
            execute('SetFocus(%i)' % (int(c) - 100))
            execute('SetFocus(%i)' % (int(f) - 80))
        else:
            execute('SetFocus(%i)' % (int(c) + 100))
            execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return


def installAddon(id):
    try:
        addon_path = os.path.join(transPath('special://home/addons'), id)
        if not os.path.exists(addon_path) == True:
            xbmc.executebuiltin('InstallAddon(%s)' % (id))
        else:
            infoDialog('{0} is already installed'.format(id), sound=True)
    except:
        return


def checkArtwork():
    try:
        theme = appearance()
        art = artPath()
        if (art == None and theme in ['-', '']):
            if setting('show.artwork') == 'true':
                yes = yesnoDialog('Install Theme Artwork?')
                if not yes:
                    return
                installAddon('script.gratisred.artwork')
        return
    except:
        return


