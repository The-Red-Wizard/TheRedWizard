import xbmc
import xbmcvfs
import xbmcaddon
import os
import json
import time
import uservar
    
class Installer:
    
    addon_data = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    get_setting = xbmcaddon.Addon().getSetting
    set_setting = xbmcaddon.Addon().setSetting
    name = uservar.addon_name
    plugin_id = uservar.addon_plugin_id
    
    def create_folder(self, folder_path):
        if not xbmcvfs.exists(folder_path):
            return xbmcvfs.mkdir(folder_path)
        
    def installer(self):
        xbmc.sleep(5000)
        install = self.install_addon(self.plugin_id)
        if install is not True:
            self.set_setting('activate_installer', 'true')
        else:
            self.set_setting('activate_installer', 'false')
            quit()
    
    def install_addon(self, plugin_id):
        if xbmc.getCondVisibility(f'System.HasAddon({plugin_id})'):
            return True
        xbmc.executebuiltin(f'InstallAddon({plugin_id})')
        clicked = False
        start = time.time()
        timeout = 20
        while not self.isinstalled(self.plugin_id):
            if time.time() >= start + timeout:
                return False
            xbmc.sleep(500)
            if xbmc.getCondVisibility('Window.IsTopMost(yesnodialog)') and not clicked:
                xbmc.executebuiltin('SendClick(yesnodialog, 11)')
                clicked = True
        return True

    def isinstalled(self, addonid):
        query = '{ "jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddonDetails", "params": { "addonid": "%s", "properties" : ["name", "thumbnail", "fanart", "enabled", "installed", "path", "dependencies"] } }' % addonid
        addonDetails = xbmc.executeJSONRPC(query)
        details_result = json.loads(addonDetails)
        if "error" in details_result:
            return False
        elif details_result['result']['addon']['installed'] == True:
            return True
        else:
            return False
