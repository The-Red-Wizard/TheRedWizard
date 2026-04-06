import json
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import re
import os
from itertools import count
from uservar import excludes
from .addonvar import addon_id, addon_name, addon_icon, textures_db

translatePath = xbmcvfs.translatePath
addon_id = xbmcaddon.Addon().getAddonInfo('id')
addon = xbmcaddon.Addon(addon_id)
addoninfo  = addon.getAddonInfo
addon_data  = translatePath(addon.getAddonInfo('profile'))
addons_path = translatePath(translatePath('special://home/addons'))
file_path = addon_data + 'whitelist.json'
dialog = xbmcgui.Dialog()

EXCLUDES_BASIC = excludes + [addon_id, textures_db, 'kodi.log', 'Addons33.db', 'packages', 'backups']
EXCLUDES_FRESH = [addon_id, textures_db, 'Addons33.db', 'kodi.log', 'plugin.program.theredwizard', 'repository.redwizard']

def add_whitelist():
    dirs, files = xbmcvfs.listdir(addons_path)
    dirs.sort()
    for x in ['packages', 'temp']:
        dirs.remove(x)
    current_whitelist = []
    if xbmcvfs.exists(file_path):
        with open(file_path, 'r') as wl:
            current_whitelist = json.load(wl)['whitelist']
        for x in current_whitelist:
            if dirs in current_whitelist:
                rm_names = dirs.remove(current_whitelist)
                current_whitelist.append(rm_names)
    xbmc.log('dirs = ' + str(dirs), xbmc.LOGINFO)
    names = []
    for x in current_whitelist:
        if x not in dirs:
            current_whitelist.remove(x)
        else:
            dirs.remove(x)
    for foldername in dirs:
        try :
            addon_nm = xbmcaddon.Addon(foldername).getAddonInfo('name')
            name = "".join(re.split("\[|\]", addon_nm)[::2])
        except:
            name = foldername
        names.append(name)
    if not names:
        xbmcgui.Dialog().notification(addon_name, 'No items available to add!', addon_icon, 3000)
        quit()
    else:
        ret = dialog.multiselect('Select Items to Add to Your Whitelist', names)
        xbmc.log('ret = ' + str(ret), xbmc.LOGINFO)
    if ret is None:
        return None
    whitelist = []
    for x in range(len(dirs)):
        if x in ret:
            whitelist.append(dirs[x])
    xbmc.log('whitelist = ' + str(whitelist), xbmc.LOGINFO)
    if not xbmcvfs.exists(addon_data):
        xbmcvfs.mkdir(addon_data)
    new_list = current_whitelist + whitelist
    with open(file_path, 'w') as whitelist_file:
        json.dump({'whitelist': new_list}, whitelist_file, indent = 4)
        xbmcgui.Dialog().notification(addon_name, 'Whitelist Updated!', addon_icon, 3000)

def remove_whitelist():
    dirs, files = xbmcvfs.listdir(addons_path)
    dirs.sort()
    for y in ['packages', 'temp']:
        dirs.remove(y)
    current_whitelist = []
    if xbmcvfs.exists(file_path):
        with open(file_path, 'r') as wl:
            current_whitelist = json.load(wl)['whitelist']
    names = []
    for y in current_whitelist:
        if y not in dirs:
            current_whitelist.remove(y)
        else:
            try :
                addon_nm = xbmcaddon.Addon(plugin).getAddonInfo('name')
                name = "".join(re.split("\[|\]", addon_nm)[::2])
            except:
                name = y
            names.append(name)
    if not names:
        xbmcgui.Dialog().notification(addon_name, 'No items available to remove!', addon_icon, 3000)
        try:
            os.unlink(os.path.join(file_path))
        except Exception as e:
            xbmc.log('Failed to delete %s. Reason: %s' % (os.path.join(file_path), e), xbmc.LOGINFO)
        quit()
    ret = dialog.multiselect('Select Items to Remove From Your Whitelist', names)
    xbmc.log('ret = ' + str(ret), xbmc.LOGINFO)
    if ret is None:
        return None
    whitelist = []
    for x in range(len(current_whitelist)):
        if x in ret:
            whitelist.append(current_whitelist[x])
    xbmc.log('whitelist = ' + str(whitelist), xbmc.LOGINFO)
    for x in whitelist:
        current_whitelist.remove(x)
    if not current_whitelist:
        try:
            os.unlink(os.path.join(file_path))
        except Exception as e:
            xbmc.log('Failed to delete %s. Reason: %s' % (os.path.join(file_path), e), xbmc.LOGINFO)
        xbmcgui.Dialog().notification(addon_name, 'Whitelist Updated!', addon_icon, 3000)
    else:
        with open(file_path, 'w') as whitelist_file:
            json.dump({'whitelist': current_whitelist}, whitelist_file, indent = 4)
            xbmcgui.Dialog().notification(addon_name, 'Whitelist Updated!', addon_icon, 3000)
            
'''def view_whitelist():
    if xbmcvfs.exists(file_path):
        with open(file_path, 'r') as wl:
            current_whitelist = json.load(wl)['whitelist']
            whitelist = []
            key = None
            for key in current_whitelist:
                name = xbmcaddon.Addon(key).getAddonInfo('name')
                whitelist.append(name)
                a = str(whitelist)
                b = a.replace("[", "\n       >>>  ", 1)
                #button_number_count = 2;
                #counter = count(button_number_count)
                #c = re.sub(r',', lambda x: x.group(0) + str(next(counter)), b)
                c = "".join(re.split("\[|\]", b)[::2])
                replacements = {"]": "", "'": "", ",": "\n       >>> "}
                for old, new in replacements.items():
                    c = c.replace(old, new)
                    cleanlist = c
            return cleanlist
your_whitelist = view_whitelist()'''
        
def read_whitelist(_excludes):
    if xbmcvfs.exists(file_path):
        with open(file_path, 'r') as wl:
            whitelist  = json.loads(wl.read())['whitelist']
        for x in whitelist:
            if not x in _excludes:
                _excludes.append(x)
        return _excludes
    else:
        return _excludes
EXCLUDES_INSTALL = read_whitelist(EXCLUDES_BASIC)
