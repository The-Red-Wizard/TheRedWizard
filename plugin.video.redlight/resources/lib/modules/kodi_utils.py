# -*- coding: utf-8 -*-
# TRUMP - UNFIT FOR OFFICE
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
import os
from urllib.parse import urlencode, unquote

def addon_themes():
	return [{'name': 'Light', 'value': ('FF434343', 'FF2E2E2E'), 'icon': 'light'}, {'name': 'Medium', 'value': ('FF373737', 'FF4a4347'), 'icon': 'medium'},
			{'name': 'Dark', 'value': ('FF1F2020', 'FF4F4F4F'), 'icon': 'dark'}]

def addon_themes_opacity():
	return [{'name': '100%', 'value': 'FF'}, {'name': '95%', 'value': 'F2'}, {'name': '90%', 'value': 'E6'}, {'name': '85%', 'value': 'D9'}, {'name': '80%', 'value': 'CC'},
			{'name': '75%', 'value': 'BF'}, {'name': '70%', 'value': 'B3'}, {'name': '65%', 'value': 'A6'}, {'name': '60%', 'value': '99'}, {'name': '55%', 'value': '8C'},
			{'name': '50%', 'value': '80'}]

def random_valid_type_check():
	return {'build_movie_list': 'movie', 'build_tvshow_list': 'tvshow', 'build_season_list': 'season', 'build_episode_list': 'episode',
	'build_in_progress_episode': 'single_episode', 'build_recently_watched_episode': 'single_episode', 'build_next_episode': 'single_episode',
	'build_my_calendar': 'single_episode', 'build_trakt_lists': 'trakt_list',
	'trakt.list.build_trakt_list': 'trakt_list', 'build_trakt_lists_contents': 'trakt_list', 'personal_lists.build_personal_list': 'personal_list',
	'build_personal_lists_contents': 'personal_list', 'tmdblist.build_tmdb_list': 'tmdb_list', 'build_tmdb_lists_contents': 'tmdb_list'}

def random_episodes_check():
	return {'build_in_progress_episode': 'episode.progress', 'build_recently_watched_episode': 'episode.recently_watched',
	'build_next_episode': 'episode.next', 'build_my_calendar': 'episode.trakt'}

def extras_button_label_values():
	return {'movie':
				{'movies_play': 'Play', 'show_trailers': 'Trailer', 'show_images': 'Images',  'show_extrainfo': 'Extra Info', 'show_genres': 'Genres',
				'show_director': 'Director', 'show_options': 'Options', 'show_recommended': 'Recommended', 'show_related': 'Related', 'show_more_like_this': 'More Like This',
				'show_similar': 'Similar', 'show_reviews': 'Reviews', 'show_comments': 'Comments', 'show_trivia': 'Trivia', 'show_blunders': 'Blunders',
				'show_year': 'More Year', 'show_genre': 'More Genres', 'show_network': 'More Network',
				'show_trakt_manager': 'Trakt Lists', 'show_personallists_manager': 'Personal Lists', 'show_tmdb_manager': 'TMDb Lists',
				'show_favorites_manager': 'Favorites Lists', 'playback_choice': 'Play Options', 'show_plot': 'Plot', 'show_keywords': 'Keywords',
				'show_in_trakt_lists': 'In Trakt Lists', 'close_all': 'Close'},
			'tvshow':
				{'tvshow_browse': 'Browse', 'show_trailers': 'Trailer', 'show_images': 'Images', 'show_extrainfo': 'Extra Info', 'show_genres': 'Genres',
				'play_nextep': 'Play Next', 'show_options': 'Options', 'show_recommended': 'Recommended', 'show_related': 'Related', 'show_more_like_this': 'More Like This',
				'show_similar': 'Similar', 'show_reviews': 'Reviews', 'show_comments': 'Comments', 'show_trivia': 'Trivia', 'show_blunders': 'Blunders',
				'show_year': 'More Year', 'show_genre': 'More Genres', 'show_network': 'More Network',
				'show_trakt_manager': 'Trakt Lists', 'show_personallists_manager': 'Personal Lists', 'show_tmdb_manager': 'TMDb Lists',
				'show_favorites_manager': 'Favorites Lists', 'play_random_episode': 'Play Random', 'show_plot': 'Plot', 'show_keywords': 'Keywords',
				'show_in_trakt_lists': 'In Trakt Lists', 'close_all': 'Close'}}

def extras_items():
	return [{'name': 'Plot', 'value': 2050}, {'name': 'Cast', 'value': 2051}, {'name': 'Recommended', 'value': 2052}, {'name': 'Related', 'value': 2053},
	{'name': 'More Like This', 'value': 2054}, {'name': 'Similar', 'value': 2055}, {'name': 'Reviews', 'value': 2056}, {'name': 'Comments', 'value': 2057},
	{'name': 'Trivia', 'value': 2058}, {'name': 'Blunders', 'value': 2059}, {'name': 'Parental Guide', 'value': 2060}, {'name': 'In Trakt Lists', 'value': 2061},
	{'name': 'Videos', 'value': 2062}, {'name': 'More from Year', 'value': 2063}, {'name': 'More from Genres', 'value': 2064}, {'name': 'More from Networks', 'value': 2065},
	{'name': 'More from Collection', 'value': 2066}]

def context_menu_items():
	return [
	{'name': 'Extras', 'value': 'extras'}, {'name': 'Options', 'value': 'options'}, {'name': 'Play Options', 'value': 'playback_options'},
	{'name': 'Browse Movie Set', 'value': 'browse_movie_set'}, {'name': 'Browse TV Seasons', 'value': 'browse_seasons'},
	{'name': 'Browse Season Episodes', 'value': 'browse_episodes'}, {'name': 'Browse Recommended', 'value': 'recommended'}, {'name': 'Browse Related', 'value': 'related'},
	{'name': 'Browse More Like This', 'value': 'more_like_this'}, {'name': 'Browse Similar', 'value': 'similar'}, {'name': 'In Trakt Lists', 'value': 'in_trakt_list'},
	{'name': 'Trakt Lists Manager', 'value': 'trakt_manager'}, {'name': 'Personal Lists Manager', 'value': 'personal_manager'},
	{'name': 'TMDb Lists Manager', 'value': 'tmdb_manager'}, {'name': 'Favorites Manager', 'value': 'favorites_manager'}, {'name': 'Mark Watched/Unwatched', 'value': 'mark_watched'},
	{'name': 'Unmark Previous Watched Episode', 'value': 'unmark_previous_episode'}, {'name': 'Exit List', 'value': 'exit'}, {'name': 'Refresh Widgets', 'value': 'refresh'},
	{'name': 'Reload Widgets', 'value': 'reload'}]

def rescrape_items():
	return [
	{'name': 'Rescrape With No Cache Check', 'value': 'cache_ignored'},
	{'name': 'Rescrape With IMDb Year Data', 'value': 'imdb_year'},
	{'name': 'Rescrape With All Scrapers', 'value': 'with_all'},
	{'name': 'Rescrape With Episode Group', 'value': 'episode_group'},
	{'name': 'Rescrape with Filters Ignored', 'value': 'ignore_filters'}]

def video_extensions():
	return ('m4v', '3g2', '3gp', 'nsv', 'tp', 'ts', 'ty', 'pls', 'rm', 'rmvb', 'mpd', 'ifo', 'mov', 'qt', 'divx', 'xvid', 'bivx', 'vob', 'nrg', 'img', 'iso', 'udf', 'pva',
			'wmv', 'asf', 'asx', 'ogm', 'm2v', 'avi', 'bin', 'dat', 'mpg', 'mpeg', 'mp4', 'mkv', 'mk3d', 'avc', 'vp3', 'svq3', 'nuv', 'viv', 'dv', 'fli', 'flv', 'wpl',
			'xspf', 'vdr', 'dvr-ms', 'xsp', 'mts', 'm2t', 'm2ts', 'evo', 'ogv', 'sdp', 'avs', 'rec', 'url', 'pxml', 'vc1', 'h264', 'rcv', 'rss', 'mpls', 'mpl', 'webm',
			'bdmv', 'bdm', 'wtv', 'trp', 'f4v', 'pvr', 'disc')

def image_extensions():
	return ('jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi', 'bmp', 'dib', 'png', 'gif', 'webp', 'tiff', 'tif',
			'psd', 'raw', 'arw', 'cr2', 'nrw', 'k25', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2')

def kodi_progress_background():
	return xbmcgui.DialogProgressBG()

def get_visibility(obj):
	return xbmc.getCondVisibility(obj)

def get_infolabel(label):
	return xbmc.getInfoLabel(label)

def kodi_actor():
	return xbmc.Actor

def translate_path(_path):
	return xbmcvfs.translatePath(_path)

def kodi_monitor():
	return xbmc.Monitor()

def kodi_player():
	return xbmc.Player()

def kodi_dialog():
	return xbmcgui.Dialog()

def addon_info(info):
	return xbmcaddon.Addon('plugin.video.redlight').getAddonInfo(info)

def addon_version():
	return get_property('redlight.addon_version') or addon_info('version')

def addon_path():
	return get_property('redlight.addon_path') or addon_info('path')

def addon_profile():
	return get_property('redlight.addon_profile') or translate_path(addon_info('profile'))

def addon_icon():
	return get_property('redlight.addon_icon') or translate_path(addon_info('icon'))

def addon_icon_mini():
	return get_property('redlight.addon_icon_mini') or os.path.join(addon_info('path'), 'resources', 'media', 'addon_icons', 'minis',
														os.path.basename(translate_path(addon_info('icon'))))

def addon_fanart():
	return (
		get_property('redlight.addon_fanart')
		or 'special://home/addons/plugin.video.redlight/resources/media/fanart.jpg'
	)

def get_icon(image_name, image_folder='icons', image_type='png'):
	local_path = os.path.join(
		addon_info('path'),
		'resources',
		'media',
		image_folder,
		'%s.%s' % (image_name, image_type)
	)

	if os.path.exists(local_path):
		return local_path

	return None

def get_addon_fanart():
	return get_property('redlight.default_addon_fanart') or addon_fanart()

def build_url(url_params):
	return 'plugin://plugin.video.redlight/?%s' % urlencode(url_params)

def add_dir(handle, url_params, list_name, icon_image='folder', fanart_image=None, isFolder=True):
	fanart = fanart_image or get_addon_fanart()
	icon = get_icon(icon_image)
	url = build_url(url_params)
	listitem = make_listitem()
	listitem.setLabel(list_name)
	listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': fanart})
	info_tag = listitem.getVideoInfoTag(True)
	info_tag.setPlot(' ')
	add_item(handle, url, listitem, isFolder)

def make_listitem():
	return xbmcgui.ListItem(offscreen=True)

def add_item(handle, url, listitem, isFolder):
	xbmcplugin.addDirectoryItem(handle, url, listitem, isFolder)

def add_items(handle, item_list):
	xbmcplugin.addDirectoryItems(handle, item_list)

def set_content(handle, content):
	xbmcplugin.setContent(handle, content)

def set_category(handle, label):
	xbmcplugin.setPluginCategory(handle, label)

def end_directory(handle, cacheToDisc=True):
	xbmcplugin.endOfDirectory(handle, cacheToDisc=cacheToDisc)

def set_view_mode(view_type, content='files', is_external=None):
	if not get_property('redlight.use_viewtypes') == 'true': return
	if is_external == None: is_external = external()
	if is_external: return
	view_id = get_property('redlight.%s' % view_type) or None
	if not view_id: return
	try:
		hold = 0
		sleep(100)
		while not container_content() == content:
			hold += 1
			if hold < 3000: sleep(1)
			else: return
		execute_builtin('Container.SetViewMode(%s)' % view_id)
	except: return

def random_integer(start=1, end=1000000):
	from random import randint
	return randint(start, end)

def remove_keys(dict_item, dict_removals):
	for k in dict_removals: dict_item.pop(k, None)
	return dict_item

def append_path(_path):
	import sys
	sys.path.append(translate_path(_path))

def logger(heading, function):
	xbmc.log('###%s###: %s' % (heading, function), 1)

def kodi_window():
	return xbmcgui.Window(10000)

def get_property(prop):
	return kodi_window().getProperty(prop)

def set_property(prop, value):
	return kodi_window().setProperty(prop, value)

def clear_property(prop):
	return kodi_window().clearProperty(prop)

def clear_all_properties():
	return kodi_window().clearProperties()

def addon(addon_id='plugin.video.redlight'):
	return xbmcaddon.Addon(id=addon_id)

def addon_installed(addon_id):
	return get_visibility('System.HasAddon(%s)' % addon_id)

def addon_enabled(addon_id):
	return get_visibility('System.AddonIsEnabled(%s)' % addon_id)

def container_content():
	return get_infolabel('Container.Content')

def set_sort_method(handle, method):
	xbmcplugin.addSortMethod(handle, {'episodes': 24, 'files': 5, 'label': 2, 'none': 0}[method])

def make_session(url='https://'):
	import requests
	session = requests.Session()
	session.mount(url, requests.adapters.HTTPAdapter(pool_maxsize=100))
	return session	

def make_playlist(playlist_type='video'):
	return xbmc.PlayList({'music': 0, 'video': 1}[playlist_type])

def supported_media():
	return xbmc.getSupportedMedia('video')

def path_exists(path):
	return xbmcvfs.exists(path)

def open_file(_file, mode='r'):
	return xbmcvfs.File(_file, mode)

def copy_file(source, destination):
	return xbmcvfs.copy(source, destination)

def delete_file(_file):
	xbmcvfs.delete(_file)

def delete_folder(_folder, force=False):
	xbmcvfs.rmdir(_folder, force)

def rename_file(old, new):
	xbmcvfs.rename(old, new)

def list_dirs(location):
	return xbmcvfs.listdir(location)

def make_directory(path):
	xbmcvfs.mkdir(path)

def make_directories(path):
	xbmcvfs.mkdirs(path)

def sleep(time):
	return xbmc.sleep(time)

def execute_builtin(command, block=False):
	return xbmc.executebuiltin(command, block)

def current_skin():
	return xbmc.getSkinDir()

def get_window_id():
	return xbmcgui.getCurrentWindowId()

def current_window_object():
	return xbmcgui.Window(get_window_id())

def kodi_version():
	return int(get_infolabel('System.BuildVersion')[0:2])

def get_video_database_path():
	return translate_path('special://profile/Database/MyVideos%s.db' % {19: '119', 20: '121', 21: '124'}[kodi_version()])

def show_busy_dialog():
	return execute_builtin('ActivateWindow(busydialognocancel)')

def hide_busy_dialog():
	execute_builtin('Dialog.Close(busydialognocancel)')
	execute_builtin('Dialog.Close(busydialog)')

def close_dialog(dialog, block=False):
	execute_builtin('Dialog.Close(%s,true)' % dialog, block)

def close_all_dialog():
	execute_builtin('Dialog.Close(all,true)')

def run_addon(addon='plugin.video.redlight', block=False):
	return execute_builtin('RunAddon(%s)' % addon, block)

def external():
	return 'redlight' not in get_infolabel('Container.PluginName')

def home():
	return xbmcgui.getCurrentWindowId() == 10000

def folder_path():
	return get_infolabel('Container.FolderPath')

def path_check(string):
	return string in unquote(folder_path())

def reload_skin():
	execute_builtin('ReloadSkin()')

def kodi_refresh():
	execute_builtin('UpdateLibrary(video,special://skin/foo)')

def refresh_widgets():
	from caches.settings_cache import get_setting
	from caches.random_widgets_cache import RandomWidgets
	RandomWidgets().delete_like('random_list.%')
	kodi_refresh()
	if get_setting('redlight.widget_refresh_notification', 'true') == 'true': notification('Widgets Refreshed', 2500)

def run_plugin(params, block=False):
	if isinstance(params, dict): params = build_url(params)
	return execute_builtin('RunPlugin(%s)' % params, block)

def container_update(params, block=False):
	if isinstance(params, dict): params = build_url(params)
	return execute_builtin('Container.Update(%s)' % params, block)

def activate_window(params, block=False):
	if isinstance(params, dict): params = build_url(params)
	return execute_builtin('ActivateWindow(Videos,%s,return)' % params, block)

def container_refresh():
	return execute_builtin('Container.Refresh')

def container_refresh_input(params, block=False):
	if isinstance(params, dict): params = build_url(params)
	return execute_builtin('Container.Refresh(%s)' % params, block)

def replace_window(params, block=False):
	if isinstance(params, dict): params = build_url(params)
	return execute_builtin('ReplaceWindow(Videos,%s)' % params, block)

def disable_enable_addon(addon_name='plugin.video.redlight'):
	import json
	try:
		xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled', 'params': {'addonid': addon_name, 'enabled': False}}))
		xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled', 'params': {'addonid': addon_name, 'enabled': True}}))
	except: pass

def update_local_addons():
	execute_builtin('UpdateLocalAddons', True)
	sleep(2500)
 
def update_kodi_addons_db(addon_name='plugin.video.redlight'):
	import time
	import sqlite3 as database
	try:
		date = time.strftime('%Y-%m-%d %H:%M:%S')
		dbcon = database.connect(translate_path('special://database/Addons33.db'), timeout=40.0)
		dbcon.execute("INSERT OR REPLACE INTO installed (addonID, enabled, lastUpdated) VALUES (?, ?, ?)", (addon_name, 1, date))
		dbcon.close()
	except: pass

def get_jsonrpc(request):
	import json
	response = xbmc.executeJSONRPC(json.dumps(request))
	result = json.loads(response)
	return result.get('result', None)

def jsonrpc_get_directory(directory, properties=['title', 'file', 'thumbnail']):
	command = {'jsonrpc': '2.0', 'id': 1, 'method': 'Files.GetDirectory', 'params': {'directory': directory, 'media': 'files', 'properties': properties}}
	try:
		files = get_jsonrpc(command).get('files')
		results = [i for i in files if i['file'].startswith('plugin://') and i['filetype'] == 'directory']
	except: results = None
	return results

def jsonrpc_get_addons(_type, properties=['thumbnail', 'name']):
	command = {'jsonrpc': '2.0', 'method': 'Addons.GetAddons','params':{'type':_type, 'properties': properties}, 'id': '1'}
	results = get_jsonrpc(command).get('addons')
	return results

def jsonrpc_get_system_setting(setting_id, setting_value=''):
	command = {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue', 'params': {'setting': setting_id}}
	try: result = get_jsonrpc(command)['value']
	except: result = setting_value
	return result

def open_settings():
	from windows.base_window import open_window
	open_window(('windows.settings_manager', 'SettingsManager'), 'settings_manager.xml')

def external_scraper_settings():
	try:
		external = get_property('redlight.external_scraper.module')
		if external in ('empty_setting', ''): return
		execute_builtin('Addon.OpenSettings(%s)' % external)
	except: pass

def progress_dialog(heading='', icon=None):
	from threading import Thread
	from windows.base_window import create_window
	progress_dialog = create_window(('windows.progress', 'Progress'), 'progress.xml', heading=heading, icon=icon or addon_icon())
	Thread(target=progress_dialog.run).start()
	return progress_dialog

def select_dialog(function_list, **kwargs):
	from windows.base_window import open_window
	selection = open_window(('windows.default_dialogs', 'Select'), 'select.xml', **kwargs)
	if selection in (None, []): return selection
	if kwargs.get('multi_choice', 'false') == 'true': return [function_list[i] for i in selection]
	return function_list[selection]

def confirm_dialog(heading='', text='Are you sure?', ok_label='OK', cancel_label='Cancel', default_control=11):
	from windows.base_window import open_window
	kwargs = {'heading': heading, 'text': text, 'ok_label': ok_label, 'cancel_label': cancel_label, 'default_control': default_control}
	return open_window(('windows.default_dialogs', 'Confirm'), 'confirm.xml', **kwargs)

def ok_dialog(heading='', text='No Results', ok_label='OK'):
	from windows.base_window import open_window
	kwargs = {'heading': heading, 'text': text, 'ok_label': ok_label}
	return open_window(('windows.default_dialogs', 'OK'), 'ok.xml', **kwargs)

def show_text(heading, text=None, file=None, font_size='small', kodi_log=False):
	from windows.base_window import open_window
	heading = heading.replace('[B]', '').replace('[/B]', '')
	if file:
		with open(file, encoding='utf-8') as r: text = r.readlines()
	if kodi_log:
		confirm = confirm_dialog(text='Show Log Errors Only?', ok_label='Yes', cancel_label='No')
		if confirm == None: return
		if confirm: text = [i for i in text if any(x in i.lower() for x in ('exception', 'error', '[test]'))]
	text = ''.join(text)
	return open_window(('windows.textviewer', 'TextViewer'), 'textviewer.xml', heading=heading, text=text, font_size=font_size)

def notification(line1, time=5000, icon=None):
	kodi_dialog().notification('Red Light', line1, icon or addon_icon(), time)

def player_check(mode, params):
	from modules.settings import playback_key
	if mode == 'playback.%s' % playback_key():
		from modules.sources import Sources
		Sources().playback_prep(params)
	elif mode == 'playback.video':
		from modules.player import RedLightPlayer
		RedLightPlayer().run(params.get('url', None), params.get('obj', None))
	else: ok_dialog('External Playback Detected', 'Playback through external addons is not supported')

def external_playback_check(params):
	return True

def timeIt(func):
	# Thanks to 123Venom
	import time
	fnc_name = func.__name__
	def wrap(*args, **kwargs):
		started_at = time.time()
		result = func(*args, **kwargs)
		logger('%s.%s' % (__name__ , fnc_name), (time.time() - started_at))
		return result
	return wrap

def volume_checker():
	# 0% == -60db, 100% == 0db
	try:
		if get_property('redlight.playback.volumecheck_enabled') == 'false' or get_visibility('Player.Muted'): return
		from modules.utils import string_alphanum_to_num
		max_volume = min(int(get_property('redlight.playback.volumecheck_percent') or '50'), 100)
		if int(100 - (float(string_alphanum_to_num(get_infolabel('Player.Volume').split('.')[0]))/60)*100) > max_volume: execute_builtin('SetVolume(%d)' % max_volume)
	except: pass

def focus_index(index):
	current_window = current_window_object()
	focus_id = current_window.getFocusId()
	try: current_window.getControl(focus_id).selectItem(index)
	except: pass

def get_all_icons():
	import requests
	from caches.main_cache import cache_object
	def _process(dummy):
		try:
			results = requests.get('https://repo.redwizard.xyz/images/redlight')
			results = [i['name'].replace('.png', '') for i in results.json()]
			return results
		except: return ['folder.png']
	username, location = get_property('redlight.update.username'), get_property('redlight.update.location')
	return cache_object(_process, 'all_icons', 'foo', False, 168)

def get_all_addon_icons():
	import requests
	from caches.main_cache import cache_object
	def _process(dummy):
		try:
			results = requests.get('https://repo.redwizard.xyz/images/redlight')
			return results
		except: return []
	username, location = get_property('redlight.update.username'), get_property('redlight.update.location')
	return cache_object(_process, 'all_addon_icons', 'foo', True, 168)

def upload_logfile(params):
	import json
	import requests
	from modules.utils import copy2clip, make_qrcode
	log_files = [('Current Kodi Log', 'kodi.log'), ('Previous Kodi Log', 'kodi.old.log')]
	list_items = [{'line1': i[0]} for i in log_files]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Which Log File to Upload', 'narrow_window': 'true'}
	log_file = select_dialog(log_files, **kwargs)
	if log_file == None: return
	log_name, log_file = log_file
	if not confirm_dialog(heading=log_name): return
	show_busy_dialog()
	url = 'https://paste.kodi.tv/'
	log_file = translate_path('special://logpath/%s' % log_file)
	if not path_exists(log_file): return ok_dialog(text='Error. Log Upload Failed')
	try:
		with open_file(log_file) as f: text = f.read()
		UserAgent = 'script.kodi.loguploader: 1.0'
		response = requests.post('%s%s' % (url, 'documents'), data=text.encode('utf-8', errors='ignore'), headers={'User-Agent': UserAgent}).json()
		if 'key' in response:
			user_code = response['key']
			url = '%s%s' % (url, user_code)
			copy2clip(url)
			qr_code = make_qrcode(url) or ''
			progressDialog = progress_dialog(heading='Kodi Log Uploader', icon=qr_code)
			count, success = 20, None
			while not progressDialog.iscanceled() and count >= 0 and success == None:
				try:
					count -= 1
					progressDialog.update('Share or Access with this url: [B]%s[/B][CR]Or Access using this QR Code' % url, count)
					sleep(2500)
				except: success = False
		else: ok_dialog(text='Error. Log Upload Failed')
	except: ok_dialog(text='Error. Log Upload Failed')
	hide_busy_dialog()

def fetch_kodi_imagecache(image):
	import sqlite3 as database
	result = None
	try:
		dbcon = database.connect(translate_path('special://database/Textures13.db'), timeout=40.0)
		dbcur = dbcon.cursor()
		dbcur.execute("SELECT cachedurl FROM texture WHERE url = ?", (image,))
		result = dbcur.fetchone()[0]
	except: pass
	return result
