import json
from os import path
from .addonvar import texts_path, addon_icon, addon_fanart
from .utils import add_dir
from .colors import colors

COLOR1 = colors.color_text1
COLOR2 = colors.color_text2

AUTH_FILE = path.join(texts_path, 'authorize.json')

def open_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def authorize_menu():
    file = open_file(AUTH_FILE)
    file = json.loads(file)
    add_dir(COLOR1('<><> [B]Authorize Services[/B] <><>'), '', '', addon_icon, addon_fanart, COLOR1('*** Authorize Services ***'))
    for key in file.keys():
        add_dir(COLOR2(key), '', 27, file[key]['icon'], file[key]['icon'], COLOR2(key), name2=key)

def  authorize_submenu(name, icon):
    file = open_file(AUTH_FILE)
    file = json.loads(file)
    for item in file[name]['items']:
        add_dir(COLOR2(item['name']), item['url'], 25, icon, icon, item['name'], isFolder=False)
