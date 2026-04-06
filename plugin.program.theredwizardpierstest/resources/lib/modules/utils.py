import sys
from inspect import getframeinfo, stack
from urllib.parse import quote_plus, unquote_plus
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import shutil
from .addonvar import addon_name, addon_version, addons_path
from . import  addonvar

translatePath = xbmcvfs.translatePath

#PB Fixes
fix_chk = 'PB-FIX'
fix_path = translatePath('special://home/addons/plugin.program.709wiz/resources/skins/Default/pbf/')
fen = addons_path + translatePath('plugin.video.fen/')
fenlt = addons_path + translatePath('plugin.video.fenlight/')
pov = addons_path + translatePath('plugin.video.pov/')
fen_fix = fix_path + translatePath('fn/player.py')
fenlt_fix = fix_path + translatePath('fnlt/player.py')
pov_fix = fix_path + translatePath('pv/sources.py')
fen_file = addons_path + translatePath('plugin.video.fen/resources/lib/modules/player.py')
fenlt_file = addons_path + translatePath('plugin.video.fenlight/resources/lib/modules/player.py')
pov_file = addons_path + translatePath('plugin.video.pov/resources/lib/modules/sources.py')

def add_dir(name,url,mode,icon,fanart,description, name2='', version='', kodi='', size='', addcontext=False,isFolder=True):
    u=sys.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)+"&name="+quote_plus(name)+"&icon="+quote_plus(icon) +"&fanart="+quote_plus(fanart)+"&description="+quote_plus(description)+"&name2="+quote_plus(name2)+"&version="+quote_plus(version)+"&kodi="+quote_plus(kodi)+"&size="+quote_plus(size)
    liz=xbmcgui.ListItem(name)
    liz.setArt({'fanart':fanart,'icon':icon,'thumb':icon})
    liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "plotoutline": description})
    if addcontext:
        contextMenu = []
        liz.addContextMenuItems(contextMenu)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)

def play_video(name, url, icon, description):
    xbmcplugin.setPluginCategory(int(sys.argv[1]), name)
    url = unquote_plus(url)
    if url.endswith('.jpg') or url.endswith('.jpeg') or url.endswith('.png'):
        string = "ShowPicture(%s)" %url
        xbmc.executebuiltin(string)
        return
    liz = xbmcgui.ListItem(name)
    liz.setInfo('video', {'title': name, 'plot': description})
    liz.setArt({'thumb': icon, 'icon': icon})
    xbmc.Player().play(url, liz)

def GetParams():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

def get_mode():
    params=GetParams()
    mode = None
    try:
        mode=int(params["mode"])
    except:
        pass
    return mode

def Log(msg):
    fileinfo = getframeinfo(stack()[1][0])
    xbmc.log('*__{}__{}*{} Python file name = {} Line Number = {}'.format(addon_name,addon_version,msg,fileinfo.filename,fileinfo.lineno), level=xbmc.LOGINFO)

def log(_text, _var):
    xbmc.log(f'{_text} = {str(_var)}', xbmc.LOGINFO)

def pbf():
    if xbmcvfs.exists(fen):
        with open(fen_file, encoding="utf8") as f:
            if fix_chk not in f.read():
                try:
                    shutil.copyfile(fen_fix, fen_file)
                except:
                    pass
    if xbmcvfs.exists(fenlt):
        with open(fenlt_file, encoding="utf8") as f:
            if fix_chk not in f.read():
                try:
                    shutil.copyfile(fenlt_fix, fenlt_file)
                except:
                    pass
    if xbmcvfs.exists(pov):
        with open(pov_file, encoding="utf8") as f:
            if fix_chk not in f.read():
                try:
                    shutil.copyfile(pov_fix, pov_file)
                except:
                    pass
