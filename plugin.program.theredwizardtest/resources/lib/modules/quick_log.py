import xbmcaddon
import xbmcvfs
import xbmcgui
import re

addon_name = xbmcaddon.Addon().getAddonInfo('name')
log_path = xbmcvfs.translatePath('special://logpath/')
text_view = xbmcgui.Dialog().textviewer
addons_path = xbmcvfs.translatePath('special://home/addons')
select_three = xbmcgui.Dialog().yesnocustom

def color_text(color: str, txt: str):
    return(f'[B][COLOR {color}]{txt}[/COLOR][/B]')

def get_log():
    pattern = re.compile('EXCEPTION Thrown(.+?)-->End of Python script error report<--', re.MULTILINE | re.DOTALL)
    log = ''
    choice = select_three(addon_name, '[COLOR gold]Select Log Type:[/COLOR]', 'Kodi.log', nolabel='Error Log', yeslabel='Kodi.old')
    if choice == 2 or choice == 0:
        path = log_path+'kodi.log'
    elif choice == 1:
        path = log_path+'kodi.old.log'
    else:
        return 
        
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        log = f.read()
    if choice == 0:
        errors = pattern.findall(log)
        if errors:
            string = color_text('snow', '\n'.join(f'*** Error ***\n\n{error}\n*** End of Error Report ***\n' for error in errors))
        else:
            string = color_text('snow', 'No Errors Found')
    else:
        string = color_text('snow', log)
    return string.replace('  ', '').replace(addons_path, addons_path+'\n')

KEY_NAV_BACK = 92
TEXTBOX = 300
CLOSEBUTTON = 302

def log_viewer() -> None:
    message = get_log()
    if not message:
        return
    
    
    class Logview(xbmcgui.WindowXMLDialog):
        
        def onInit(self):
            self.getControl(TEXTBOX).setText(message)
            
        def onAction(self, action):
            if action.getId() == KEY_NAV_BACK:
                self.Close()
    
        def onClick(self, controlId):
            if controlId == CLOSEBUTTON:
                self.Close()

        def Close(self):
            self.close()
    
    d = Logview('logview.xml', xbmcaddon.Addon().getAddonInfo('path'), 'Default', '720p')
    d.doModal()
    del d