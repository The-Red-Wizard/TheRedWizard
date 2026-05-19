# -*- coding: utf-8 -*-
import json
from modules import kodi_utils
from caches.base_cache import connect_database
# logger = kodi_utils.logger

class SettingsCache:
	def get(self, setting_id):
		try:
			dbcon = connect_database('settings_db')
			setting_id = setting_id.replace('redlight.', '')
			setting_value = dbcon.execute('SELECT setting_value from settings WHERE setting_id = ?', (setting_id,)).fetchone()[0]
			self.set_memory_cache(setting_id, setting_value)
		except: setting_value = None
		return setting_value

	def remove_setting(self, setting_id):
		dbcon = connect_database('settings_db')
		dbcon.execute('DELETE FROM settings WHERE setting_id = ?', (setting_id,))

	def get_many(self, settings_list):
		try:
			dbcon = connect_database('settings_db')
			results = dict(dbcon.execute('SELECT setting_id, setting_value FROM settings WHERE setting_id in (%s)' \
										% (', '.join('?' for _ in settings_list)), settings_list).fetchall())
			return results
		except: results = {}
		return results

	def get_all(self):
		dbcon = connect_database('settings_db')
		try: all_settings = dict(dbcon.execute('SELECT setting_id, setting_value FROM settings').fetchall())
		except: all_settings = {}
		return all_settings

	def set(self, setting_id, setting_value=None):
		dbcon = connect_database('settings_db')
		setting_info = default_setting_values(setting_id)
		setting_type, setting_default = setting_info['setting_type'], setting_info['setting_default']
		if setting_value is None: setting_value = setting_default
		dbcon.execute('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)', (setting_id, setting_type, setting_default, setting_value))
		self.set_memory_cache(setting_id, setting_value)
		if setting_type == 'action' and 'settings_options' in setting_info:
			name_setting_id = '%s_name' % setting_id
			name_setting_value = setting_info['settings_options'][setting_value]
			dbcon.execute('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)', (name_setting_id, 'name', '', name_setting_value))
			self.set_memory_cache(name_setting_id, name_setting_value)

	def set_many(self, settings_list):
		dbcon = connect_database('settings_db')
		dbcon.executemany('INSERT OR REPLACE INTO settings VALUES (?, ?, ?, ?)', settings_list)
		for item in settings_list: self.set_memory_cache(item[0], item[3] or item[2])

	def set_memory_cache(self, setting_id, setting_value):
		kodi_utils.set_property('redlight.%s' % setting_id, setting_value)

	def delete_memory_cache(self, setting_id):
		clear_property('redlight.%s' % setting_id)

	def setting_info(self, setting_id):
		d_settings = default_settings()
		return [i for i in d_settings if i['setting_id'] == setting_id][0]

	def clean_database(self):
		try:
			dbcon = connect_database('settings_db')
			dbcon.execute('VACUUM')
			return True
		except: return False

settings_cache = SettingsCache()

def set_setting(setting_id, value):
	settings_cache.set(setting_id, value)

def get_setting(setting_id, fallback=''):
	return kodi_utils.get_property(setting_id) or settings_cache.get(setting_id) or fallback

def get_many(settings_list):
	return settings_cache.get_many(settings_list)

def sync_settings(params={}):
	silent = params.get('silent', 'true') == 'true'
	insert_list = []
	insert_list_append = insert_list.append
	currentsettings = settings_cache.get_all()
	d_settings = default_settings()
	defaultsettings_ids = [i['setting_id'] for i in d_settings]
	defaultsettings_names = [i['setting_id'] for i in d_settings if 'settings_options' in i]
	defaultsettings_ids.extend(['%s_name' % i for i in defaultsettings_names])
	try:
		c_settings = currentsettings.items()
		obsoletesettings_ids = [k for k, v in c_settings if not k in defaultsettings_ids]
		if obsoletesettings_ids:
			for item in obsoletesettings_ids: settings_cache.remove_setting(item)
	except: pass
	if currentsettings:
		c_settings = currentsettings.items()
		for k, v  in c_settings: settings_cache.set_memory_cache(k, v)
	for item in d_settings:
		setting_id = item['setting_id']
		if setting_id in currentsettings: continue
		setting_type = item['setting_type']
		setting_default = item['setting_default']
		if setting_type == 'action' and 'settings_options' in item:
			name_default = item['settings_options'][setting_default]
			insert_list_append(('%s_name' % setting_id, 'name', name_default, name_default))
		insert_list_append((setting_id, setting_type, setting_default, setting_default))
	if insert_list: settings_cache.set_many(insert_list)
	settings_cache.clean_database()
	if not silent: kodi_utils.notification('Settings Cache Remade')

def set_default(setting_ids):
	if not isinstance(setting_ids, list): setting_ids = [setting_ids]
	if not kodi_utils.confirm_dialog(text='Are You Sure?', ok_label='Yes', cancel_label='No', default_control=11): return
	for setting_id in setting_ids:
		try: set_setting(setting_id, default_setting_values(setting_id)['setting_default'])
		except: pass

def set_boolean(params):
	boolean_dict = {'true': 'false', 'false': 'true'}
	setting = params['setting_id']
	set_setting(setting, boolean_dict[get_setting('redlight.%s' % setting)])

def set_string(params):
	current_value = get_setting('redlight.%s' % params['setting_id'])
	current_value = current_value.replace('empty_setting', '')
	new_value = kodi_utils.kodi_dialog().input('', defaultt=current_value)
	if not new_value and not kodi_utils.confirm_dialog(text='Enter Blank Value?', ok_label='Yes', cancel_label='Re-Enter Value', default_control=11):
		return set_string(params)
	set_setting(params['setting_id'], new_value or 'empty_setting')

def set_numeric(params):
	setting_id = params['setting_id']
	setting_values = default_setting_values(setting_id)
	values_get = setting_values.get
	min_value, max_value = int(values_get('min_value', '0')), int(values_get('max_value', '100000000000000'))
	negative_included = any((n < 0 for n in [min_value, max_value]))
	if negative_included:
		multiplier_values = [('Positive(+)', 1), ('Negative(-)', -1)]
		list_items = [{'line1': item[0]} for item in multiplier_values]
		kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true', 'heading': 'Will this be a positive or negative number?'}
		multiplier = kodi_utils.select_dialog(multiplier_values, **kwargs)
	else: multiplier = None
	new_value = kodi_utils.kodi_dialog().input('Range [B]%s - %s[/B].' % (min_value, max_value), type=1)
	if not new_value: return
	if multiplier: new_value = str(int(float(new_value) * multiplier[1]))
	if int(new_value) < min_value or int(new_value) > max_value:
		kodi_utils.ok_dialog(text='Please Choose Between the Range [B]%s - %s[/B].' % (min_value, max_value))
		return set_numeric(params)
	set_setting(setting_id, new_value)

def set_path(params):
	setting_id = params['setting_id']
	browse_mode = int(default_setting_values(setting_id)['browse_mode'])
	new_value = kodi_utils.kodi_dialog().browse(browse_mode, '', '', defaultt=get_setting('redlight.%s' % setting_id))
	set_setting(setting_id, new_value)

def set_from_list(params):
	setting_id = params['setting_id']
	settings_options = default_setting_values(setting_id)['settings_options'].items()
	settings_list = [(v, k) for k, v in settings_options]
	new_value = kodi_utils.select_dialog(settings_list, **{'items': json.dumps([{'line1': item[0]} for item in settings_list]), 'narrow_window': 'true'})
	if not new_value: return
	setting_value = new_value[1]
	set_setting(setting_id, setting_value)

def set_source_folder_path(params):
	setting_id = params['setting_id']
	current_setting = get_setting('redlight.%s' % setting_id)
	if current_setting not in (None, 'None', ''):
		if kodi_utils.confirm_dialog(text='Enter Blank Value?', ok_label='Yes', cancel_label='Re-Enter Value', default_control=11):
			return set_setting(setting_id, 'None')
	return set_path(params)

def restore_setting_default(params):
	silent = params.get('silent', 'false') == 'true'
	if not silent and not kodi_utils.confirm_dialog(): return
	try:
		setting_id = params['setting_id']
		setting_default = default_setting_values(setting_id)['setting_default']
		set_setting(setting_id, setting_default)
	except:
		if not silent: kodi_utils.ok_dialog(text='Error restoring default setting')

def default_setting_values(setting_id):
	if 'redlight.' in setting_id: setting_id = setting_id.replace('redlight.', '')
	d_settings = default_settings()
	return next((i for i in d_settings if i['setting_id'] == setting_id), None)

def default_settings():
	return [
#===============================================================================#
#====================================GENERAL====================================#
#===============================================================================#
#==================== General
{'setting_id': 'auto_start_redlight', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'addon_icon_choice', 'setting_type': 'string', 'setting_default': 'resources/media/addon_icons/icon.png'},
{'setting_id': 'default_addon_fanart', 'setting_type': 'path', 'setting_default': kodi_utils.addon_fanart(), 'browse_mode': '2'},
{'setting_id': 'limit_concurrent_threads', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'max_threads', 'setting_type': 'action', 'setting_default': '60', 'min_value': '10', 'max_value': '250'},
#==================== Window Theme
{'setting_id': 'window_theme', 'setting_type': 'string', 'setting_default': 'CC1F2020'},
{'setting_id': 'window_theme_opacity', 'setting_type': 'string', 'setting_default': 'CC'},
#==================== Manage Updates
{'setting_id': 'update.action', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Prompt', '1': 'Automatic', '2': 'Notification', '3': 'Off'}},
{'setting_id': 'update.delay', 'setting_type': 'action', 'setting_default': '10', 'min_value': '10', 'max_value': '300'},
{'setting_id': 'update.username', 'setting_type': 'string', 'setting_default': 'TheRedWizard'},
{'setting_id': 'update.location', 'setting_type': 'string', 'setting_default': 'TheRedWizard.github.io'},
#==================== Watched Indicators
{'setting_id': 'watched_indicators', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Red Light', '1': 'Trakt'}},
#======+============= Trakt Cache
{'setting_id': 'trakt.sync_interval', 'setting_type': 'action', 'setting_default': '60', 'min_value': '5', 'max_value': '600'},
{'setting_id': 'trakt.refresh_widgets', 'setting_type': 'boolean', 'setting_default': 'true'},
#==================== UTC Time Offset
{'setting_id': 'datetime.offset', 'setting_type': 'action', 'setting_default': '0', 'min_value': '-15', 'max_value': '15'},
#==================== Downloads
{'setting_id': 'movie_download_directory', 'setting_type': 'path', 'setting_default': 'special://profile/addon_data/plugin.video.redlight/Movies Downloads/', 'browse_mode': '0'},
{'setting_id': 'tvshow_download_directory', 'setting_type': 'path', 'setting_default': 'special://profile/addon_data/plugin.video.redlight/TV Show Downloads/', 'browse_mode': '0'},
{'setting_id': 'premium_download_directory', 'setting_type': 'path', 'setting_default': 'special://profile/addon_data/plugin.video.redlight/Premium Downloads/', 'browse_mode': '0'},
{'setting_id': 'image_download_directory', 'setting_type': 'path', 'setting_default': 'special://profile/addon_data/plugin.video.redlight/Image Downloads/', 'browse_mode': '0'},


#================================================================================#
#====================================FEATURES====================================#
#================================================================================#
#==================== Extras
{'setting_id': 'extras.enable_extra_ratings', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'extras.enabled_ratings', 'setting_type': 'string', 'setting_default': 'Meta, Tom/Critic, Tom/User, IMDb, TMDb'},
{'setting_id': 'extras.enable_item_ratings', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'extras.enable_scrollbars', 'setting_type': 'boolean', 'setting_default': 'false'},
#==================== Special Open Actions
{'setting_id': 'media_open_action_movie', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Open Extras', '2': 'Open Movie Set', '3': 'Both'}},
{'setting_id': 'media_open_action_tvshow', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Open Extras'}},
#==================== AI Generated Similar Titles
{'setting_id': 'ai_model.order', 'setting_type': 'string', 'setting_default': 'gemini-2.5-flash-lite,llama-3.3-70b-versatile,gemma-3-27b-it,llama-3.1-8b-instant'},
{'setting_id': 'ai_model.limit', 'setting_type': 'action', 'setting_default': '15', 'min_value': '1', 'max_value': '25'},


#==================================================================================#
#====================================CONTENT=======================================#
#==================================================================================#
#==================== General
{'setting_id': 'paginate.lists', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Within Addon Only', '2': 'Widgets Only', '3': 'Both'}},
{'setting_id': 'paginate.limit_addon', 'setting_type': 'action', 'setting_default': '20'},
{'setting_id': 'paginate.limit_widgets', 'setting_type': 'action', 'setting_default': '20'},
{'setting_id': 'paginate.jump_to', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'ignore_articles', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'recommend_service', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Recommended (TMDb)', '1': 'More Like This (IMDb)',
'2': 'Similar (AI)', '3': 'Related (Trakt)'}},
{'setting_id': 'recommend_seed', 'setting_type': 'action', 'setting_default': '5', 'settings_options': {'1': 'Last Watched Only', '2': 'Last 2 Watched',
'3': 'Last 3 Watched', '4': 'Last 4 Watched', '5': 'Last 5 Watched', '6': 'Last 6 Watched', '7': 'Last 7 Watched', '8': 'Last 8 Watched',
'9': 'Last 9 Watched', '10': 'Last 10 Watched'}},
{'setting_id': 'mpaa_region', 'setting_type': 'string', 'setting_default': 'US'},
{'setting_id': 'lists_cache_duraton', 'setting_type': 'string', 'setting_default': '24'},
{'setting_id': 'tv_progress_location', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Watched', '1': 'In Progress', '2': 'Both'}},
{'setting_id': 'show_specials', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'use_season_name', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'default_all_episodes', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Never', '1': 'If Only One Season', '2': 'Always'}},
{'setting_id': 'avoid_episode_spoilers', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'include_anime_tvshow', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'show_unaired_watchlist', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'meta_filter', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'use_viewtypes', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'manual_viewtypes', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'view.main', 'setting_type': 'string', 'setting_default': '55'},
{'setting_id': 'view.movies', 'setting_type': 'string', 'setting_default': '500'},
{'setting_id': 'view.tvshows', 'setting_type': 'string', 'setting_default': '500'},
{'setting_id': 'view.seasons', 'setting_type': 'string', 'setting_default': '55'},
{'setting_id': 'view.episodes', 'setting_type': 'string', 'setting_default': '55'},
{'setting_id': 'view.episodes_single', 'setting_type': 'string', 'setting_default': '55'},
{'setting_id': 'view.premium', 'setting_type': 'string', 'setting_default': '55'},
#==================== Contents Sort Order For Watched Progress
{'setting_id': 'sort.progress', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Title', '1': 'Recently Watched'}},
{'setting_id': 'sort.watched', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Title', '1': 'Recently Watched'}},
#==================== Contents Sort Order For Trakt Lists
{'setting_id': 'sort.collection', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Title', '1': 'Date Added', '2': 'Release Date'}},
{'setting_id': 'sort.watchlist', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Title', '1': 'Date Added', '2': 'Release Date'}},
#==================== Contents Sort Order For TMDb Lists
{'setting_id': 'tmdbsort.watchlist', 'setting_type': 'action', 'setting_default': '4', 'settings_options': {'0': 'Title', '1': 'Release Date (asc)', '2': 'Release Date (desc)',
'3': 'Shuffle', '4': 'Default from TMDb (None)'}},
{'setting_id': 'tmdbsort.favorites', 'setting_type': 'action', 'setting_default': '4', 'settings_options': {'0': 'Title', '1': 'Release Date (asc)', '2': 'Release Date (desc)',
'3': 'Shuffle', '4': 'Default from TMDb (None)'}},
#==================== Personal Lists
{'setting_id': 'personal_list.sort_unseen_to_top', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'personal_list.highlight_unseen', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'personal_list.unseen_highlight', 'setting_type': 'string', 'setting_default': 'FF4DDBFF'},
{'setting_id': 'personal_list.show_author', 'setting_type': 'boolean', 'setting_default': 'true'},
#==================== Widgets
{'setting_id': 'widget_refresh_timer', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'widget_refresh_notification', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'widget_hide_watched', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'widget_hide_next_page', 'setting_type': 'boolean', 'setting_default': 'false'},
#==================== RPDb Ratings Posters
{'setting_id': 'rpdb_enabled', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Movies', '2': 'TV Shows', '3': 'Both'}},
{'setting_id': 'rpdb_format', 'setting_type': 'string', 'setting_default': ''},
#==================== Context Menu
{'setting_id': 'context_menu.enabled', 'setting_type': 'string',
'setting_default': 'extras,options,playback_options,browse_movie_set,browse_seasons,browse_episodes,recommended,related,more_like_this,similar,in_trakt_list,' \
'trakt_manager,personal_manager,tmdb_manager,favorites_manager,mark_watched,unmark_previous_episode,exit,refresh,reload'},
{'setting_id': 'context_menu.order', 'setting_type': 'string',
'setting_default': 'extras,options,playback_options,browse_movie_set,browse_seasons,browse_episodes,recommended,related,more_like_this,similar,in_trakt_list,' \
'trakt_manager,personal_manager,tmdb_manager,favorites_manager,mark_watched,unmark_previous_episode,exit,refresh,reload'},


#==================================================================================#
#====================================SINGLE EPISODE LISTS==========================#
#==================================================================================#
#==================== General
{'setting_id': 'single_ep_display', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'TITLE: SxE - EPISODE', '1': 'SxE - EPISODE', '2': 'EPISODE'}},
{'setting_id': 'single_ep_display_widget', 'setting_type': 'action', 'setting_default': '1', 'settings_options': {'0': 'TITLE: SxE - EPISODE', '1': 'SxE - EPISODE', '2': 'EPISODE'}},
{'setting_id': 'single_ep_unwatched_episodes', 'setting_type': 'boolean', 'setting_default': 'false'},
#==================== Next Episodes
{'setting_id': 'nextep.method', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Last Aired', '1': 'Last Watched'}},
{'setting_id': 'nextep.sort_type', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Recently Watched', '1': 'Airdate', '2': 'Title'}},
{'setting_id': 'nextep.sort_order', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Descending', '1': 'Ascending'}},
{'setting_id': 'nextep.limit_history', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'nextep.limit', 'setting_type': 'action', 'setting_default': '20', 'min_value': '1', 'max_value': '200'},
{'setting_id': 'nextep.include_unwatched', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Watchlist', '2': 'Favorites', '3': 'Both'}},
{'setting_id': 'nextep.include_airdate', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'nextep.airing_today', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'nextep.include_unaired', 'setting_type': 'boolean', 'setting_default': 'false'},
#======+============= Trakt Calendar
{'setting_id': 'trakt.flatten_episodes', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'trakt.calendar_sort_order', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Descending', '1': 'Ascending'}},
{'setting_id': 'trakt.calendar_previous_days', 'setting_type': 'action', 'setting_default': '7', 'min_value': '0', 'max_value': '14'},
{'setting_id': 'trakt.calendar_future_days', 'setting_type': 'action', 'setting_default': '7', 'min_value': '0', 'max_value': '14'},


#=====================================================================================#
#====================================META ACCOUNTS====================================#
#=====================================================================================#
#==================== Trakt
#==================== Trakt
{'setting_id': 'trakt.user', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'trakt.client', 'setting_type': 'string', 'setting_default': '30e6c73030cc41dbff996200ac3060cde689555ba207020e08a2175533b912c3'},
{'setting_id': 'trakt.secret', 'setting_type': 'string', 'setting_default': '726f6b12a9f0079d5850a7bb0e15860725cd487cbfb54ce5471de217639465c5'},
#==================== TMDb API
{'setting_id': 'tmdb_api', 'setting_type': 'string', 'setting_default': 'a0bf207c5ff6c0caabac0327e39b1cd2'},
#==================== TMDb Lists
{'setting_id': 'tmdb.token', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'tmdb.username', 'setting_type': 'string', 'setting_default': 'empty_setting'},
#==================== OMDb
{'setting_id': 'omdb_api', 'setting_type': 'string', 'setting_default': 'empty_setting'},
#==================== RPDb
{'setting_id': 'rpdb_api', 'setting_type': 'string', 'setting_default': 't0-free-rpdb'},
#==================== Google API
{'setting_id': 'google_api', 'setting_type': 'string', 'setting_default': 'empty_setting'},
#==================== GROQ API
{'setting_id': 'groq_api', 'setting_type': 'string', 'setting_default': 'empty_setting'},


#=====================================================================================#
#====================================STREAMING ACCOUNTS===============================#
#=====================================================================================#
#==================== External
{'setting_id': 'provider.external', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'external_scraper.name', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'external.cache_check', 'setting_type': 'boolean', 'setting_default': 'false'},
#==================== Real Debrid
{'setting_id': 'rd.token', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'rd.enabled', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'rd.account_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'store_resolved_to_cloud.real-debrid', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'All', '2': 'Show Packs Only'}},
{'setting_id': 'provider.rd_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'rd_cloud.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'check.rd_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.rd_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.sort_rdcloud_first', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'rd.priority', 'setting_type': 'action', 'setting_default': '10', 'min_value': '1', 'max_value': '10'},
{'setting_id': 'rd.alternate_base_url', 'setting_type': 'boolean', 'setting_default': 'false'},
#==================== Premiumize
{'setting_id': 'pm.token', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'pm.enabled', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'pm.account_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'store_resolved_to_cloud.premiumize.me', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'All', '2': 'Show Packs Only'}},
{'setting_id': 'provider.pm_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'pm_cloud.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'check.pm_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.pm_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.sort_pmcloud_first', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'pm.priority', 'setting_type': 'action', 'setting_default': '10', 'min_value': '1', 'max_value': '10'},
#==================== All Debrid
{'setting_id': 'ad.token', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'ad.enabled', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'ad.account_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'store_resolved_to_cloud.alldebrid', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'All', '2': 'Show Packs Only'}},
{'setting_id': 'provider.ad_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'ad_cloud.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'check.ad_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.ad_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.sort_adcloud_first', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'ad.priority', 'setting_type': 'action', 'setting_default': '10', 'min_value': '1', 'max_value': '10'},
#==================== TorBox
{'setting_id': 'tb.token', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'tb.enabled', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'store_resolved_to_cloud.torbox', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'All', '2': 'Show Packs Only'}},
{'setting_id': 'provider.tb_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'tb_cloud.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'check.tb_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.tb_cloud', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.sort_tbcloud_first', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'tb.priority', 'setting_type': 'action', 'setting_default': '10', 'min_value': '1', 'max_value': '10'},
#==================== Easynews
{'setting_id': 'provider.easynews', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'easynews_user', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'easynews_password', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'easynews.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'easynews.filter_lang', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'easynews.lang_filters', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'check.easynews', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.easynews', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'en.priority', 'setting_type': 'action', 'setting_default': '7', 'min_value': '1', 'max_value': '10'},
#=========+========== Folders
{'setting_id': 'provider.folders', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'folders.title_filter', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'check.folders', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay.folders', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.sort_folders_first', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'results.folders_ignore_filters', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'folders.priority', 'setting_type': 'action', 'setting_default': '6', 'min_value': '1', 'max_value': '10'},


#===============================================================================#
#====================================RESULTS====================================#
#===============================================================================#
#==================== Display
{'setting_id': 'results.timeout', 'setting_type': 'action', 'setting_default': '20', 'min_value': '1'},
{'setting_id': 'results.list_format', 'setting_type': 'string', 'setting_default': 'List'},
#==================== Rescrape
{'setting_id': 'rescrape.cache_ignored', 'setting_type': 'action', 'setting_default': '1', 'settings_options': {'0': 'Off', '1': 'Auto', '2': 'Prompt'}},
{'setting_id': 'rescrape.cache_ignored.order', 'setting_type': 'action', 'setting_default': '0', 'min_value': '1', 'max_value': '5'},
{'setting_id': 'rescrape.imdb_year', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Auto', '2': 'Prompt'}},
{'setting_id': 'rescrape.imdb_year.order', 'setting_type': 'action', 'setting_default': '1', 'min_value': '1', 'max_value': '5'},
{'setting_id': 'rescrape.with_all', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Auto', '2': 'Prompt'}},
{'setting_id': 'rescrape.with_all.order', 'setting_type': 'action', 'setting_default': '2', 'min_value': '1', 'max_value': '5'},
{'setting_id': 'rescrape.episode_group', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Auto', '2': 'Prompt'}},
{'setting_id': 'rescrape.episode_group.order', 'setting_type': 'action', 'setting_default': '3', 'min_value': '1', 'max_value': '5'},
{'setting_id': 'rescrape.ignore_filters', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Auto', '2': 'Prompt'}},
{'setting_id': 'rescrape.ignore_filters.order', 'setting_type': 'action', 'setting_default': '4', 'min_value': '1', 'max_value': '5'},
#==================== Sorting and Filtering
{'setting_id': 'results.sort_order_display', 'setting_type': 'string', 'setting_default': 'Quality, Size, Provider'},
{'setting_id': 'results.filter_size_method', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Off', '1': 'Use Line Speed', '2': 'Use Size'}},
{'setting_id': 'results.line_speed', 'setting_type': 'action', 'setting_default': '25', 'min_value': '1'},
{'setting_id': 'results.movie_size_max', 'setting_type': 'action', 'setting_default': '10000', 'min_value': '1'},
{'setting_id': 'results.episode_size_max', 'setting_type': 'action', 'setting_default': '3000', 'min_value': '1'},
{'setting_id': 'results.movie_size_min', 'setting_type': 'action', 'setting_default': '0', 'min_value': '0'},
{'setting_id': 'results.episode_size_min', 'setting_type': 'action', 'setting_default': '0', 'min_value': '0'},
{'setting_id': 'results.size_unknown', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'results.size_sort_weighted', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results.size_sort_direction', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Descending', '1': 'Ascending'}},
{'setting_id': 'results.uncached_min_seeders', 'setting_type': 'action', 'setting_default': '0', 'min_value': '0'},
{'setting_id': 'results.limit_number_quality', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'results.limit_number_total', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'results.include.unknown.size', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'filter.include_prerelease', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.hevc', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.hevc.max_quality', 'setting_type': 'action', 'setting_default': '4K', 'settings_options': {'4K': '4K', '1080p': '1080p', '720p': '720p', 'SD': 'SD'}},
{'setting_id': 'filter.hevc.max_autoplay_quality', 'setting_type': 'action', 'setting_default': '4K', 'settings_options': {'4K': '4K', '1080p': '1080p', '720p': '720p', 'SD': 'SD'}},
{'setting_id': 'filter.3d', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.hdr', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.dv', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.av1', 'setting_type': 'action', 'setting_default': '0', 'settings_options':{'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.enhanced_upscaled', 'setting_type': 'action', 'setting_default': '0', 'settings_options':{'0': 'Include', '1': 'Exclude'}},
{'setting_id': 'filter.sort_to_top', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Source Select', '2': 'Autoplay', '3': 'Both'}},
{'setting_id': 'filter.preferred_filters', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'filter_audio', 'setting_type': 'string', 'setting_default': 'empty_setting'},
#==================== Results Color Highlights
{'setting_id': 'highlight.type', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Provider', '1': 'Quality', '2': 'Single Color'}},
{'setting_id': 'provider.easynews_highlight', 'setting_type': 'string', 'setting_default': 'FF00B3B2'},
{'setting_id': 'provider.debrid_cloud_highlight', 'setting_type': 'string', 'setting_default': 'FF7A01CC'},
{'setting_id': 'provider.folders_highlight', 'setting_type': 'string', 'setting_default': 'FFB36B00'},
{'setting_id': 'provider.rd_highlight', 'setting_type': 'string', 'setting_default': 'FF3C9900'},
{'setting_id': 'provider.pm_highlight', 'setting_type': 'string', 'setting_default': 'FFFF3300'},
{'setting_id': 'provider.ad_highlight', 'setting_type': 'string', 'setting_default': 'FFE6B800'},
{'setting_id': 'provider.oc_highlight', 'setting_type': 'string', 'setting_default': 'FF008EB2'},
{'setting_id': 'provider.ed_highlight', 'setting_type': 'string', 'setting_default': 'FF3233FF'},
{'setting_id': 'provider.tb_highlight', 'setting_type': 'string', 'setting_default': 'FF01662A'},
{'setting_id': 'scraper_4k_highlight', 'setting_type': 'string', 'setting_default': 'FFFF00FE'},
{'setting_id': 'scraper_1080p_highlight', 'setting_type': 'string', 'setting_default': 'FFE6B800'},
{'setting_id': 'scraper_720p_highlight', 'setting_type': 'string', 'setting_default': 'FF3C9900'},
{'setting_id': 'scraper_SD_highlight', 'setting_type': 'string', 'setting_default': 'FF0166FF'},
{'setting_id': 'scraper_single_highlight', 'setting_type': 'string', 'setting_default': 'FF008EB2'},


#===============================================================================#
#===================================PLAYBACK====================================#
#===============================================================================#
#==================== Playback Movies
{'setting_id': 'auto_play_movie', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results_quality_movie', 'setting_type': 'string', 'setting_default': 'SD, 720p, 1080p, 4K'},
{'setting_id': 'autoplay_quality_movie', 'setting_type': 'string', 'setting_default': 'SD, 720p, 1080p, 4K'},
{'setting_id': 'auto_resume_movie', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Never', '1': 'Always', '2': 'Autoplay Only'}},
{'setting_id': 'stinger_alert.show', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'stinger_alert.window_percentage', 'setting_type': 'action', 'setting_default': '90', 'min_value': '1', 'max_value': '99'},
{'setting_id': 'stinger_alert.use_chapters', 'setting_type': 'boolean', 'setting_default': 'true'},
#==================== Playback Episodes
{'setting_id': 'auto_play_episode', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'results_quality_episode', 'setting_type': 'string', 'setting_default': 'SD, 720p, 1080p, 4K'},
{'setting_id': 'autoplay_quality_episode', 'setting_type': 'string', 'setting_default': 'SD, 720p, 1080p, 4K'},
{'setting_id': 'autoplay_next_episode', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoplay_alert_method', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Window', '1': 'Notification'}},
{'setting_id': 'autoplay_default_action', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Play', '1': 'Cancel', '2': 'Pause & Wait'}},
{'setting_id': 'autoplay_next_window_percentage', 'setting_type': 'action', 'setting_default': '95', 'min_value': '75', 'max_value': '99'},
{'setting_id': 'autoplay_use_chapters', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'autoplay_watching_check', 'setting_type': 'action', 'setting_default': '3', 'min_value': '0', 'max_value': '5'},
{'setting_id': 'autoscrape_next_episode', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'autoscrape_next_window_percentage', 'setting_type': 'action', 'setting_default': '95', 'min_value': '75', 'max_value': '99'},
{'setting_id': 'autoscrape_use_chapters', 'setting_type': 'boolean', 'setting_default': 'true'},
{'setting_id': 'autoscrape_confirm', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'auto_resume_episode', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'Never', '1': 'Always', '2': 'Autoplay Only'}},
#==================== Playback Utilities
{'setting_id': 'playback.limit_resolve', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'easynews.playback_method', 'setting_type': 'action', 'setting_default': '0', 'settings_options': {'0': 'None', '1': 'Retry', '2': 'No Seek', '3': 'Both'}},
{'setting_id': 'easynews.playback_method_retries', 'setting_type': 'action', 'setting_default': '1', 'min_value': '1', 'max_value': '4'},
{'setting_id': 'easynews.playback_method_limited', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'playback.volumecheck_enabled', 'setting_type': 'boolean', 'setting_default': 'false'},
{'setting_id': 'playback.volumecheck_percent', 'setting_type': 'action', 'setting_default': '50', 'min_value': '1', 'max_value': '100'},
{'setting_id': 'playback.auto_enable_subs', 'setting_type': 'boolean', 'setting_default': 'false'},


#=========================================================================================#
#======================================HIDDEN=============================================#
#=========================================================================================#
{'setting_id': 'tmdb.account_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'tmdb.session_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'tmdb.account_session_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'reuse_language_invoker', 'setting_type': 'string', 'setting_default': 'true'},
{'setting_id': 'addon_icon_choice_name', 'setting_type': 'string', 'setting_default': 'icon.png'},
{'setting_id': 'widget_refresh_timer_name', 'setting_type': 'string', 'setting_default': 'Off'},
{'setting_id': 'mpaa_region_display_name', 'setting_type': 'string', 'setting_default': 'United States'},
{'setting_id': 'lists_cache_duraton_display_name', 'setting_type': 'string', 'setting_default': '1 Day'},
{'setting_id': 'results.limit_number_quality_name', 'setting_type': 'string', 'setting_default': 'Off'},
{'setting_id': 'results.limit_number_total_name', 'setting_type': 'string', 'setting_default': 'Off'},
{'setting_id': 'rpdb_format_name', 'setting_type': 'string', 'setting_default': 'Default'},
{'setting_id': 'window_theme_contrast', 'setting_type': 'string', 'setting_default': 'FF4a4347'},
{'setting_id': 'window_theme_name', 'setting_type': 'string', 'setting_default': 'Dark'},
{'setting_id': 'window_theme_opacity_name', 'setting_type': 'string', 'setting_default': '80%'},
{'setting_id': 'external_scraper.module', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'trakt.next_daily_clear', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'trakt.expires', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'trakt.refresh', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'trakt.token', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'tmdblist.list_sort', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'tmdblist.list_sort_name', 'setting_type': 'string', 'setting_default': 'Title'},
{'setting_id': 'personal_list.list_sort', 'setting_type': 'string', 'setting_default': '0'},
{'setting_id': 'personal_list.list_sort_name', 'setting_type': 'string', 'setting_default': 'Title'},
{'setting_id': 'rd.client_id', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'rd.refresh', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'rd.secret', 'setting_type': 'string', 'setting_default': 'empty_setting'},
{'setting_id': 'results.sort_order', 'setting_type': 'string', 'setting_default': '1'},
{'setting_id': 'folder1.display_name', 'setting_type': 'string', 'setting_default': 'Folder 1'},
{'setting_id': 'folder1.movies_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder1.tv_shows_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder2.display_name', 'setting_type': 'string', 'setting_default': 'Folder 2'},
{'setting_id': 'folder2.movies_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder2.tv_shows_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder3.display_name', 'setting_type': 'string', 'setting_default': 'Folder 3'},
{'setting_id': 'folder3.movies_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder3.tv_shows_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder4.display_name', 'setting_type': 'string', 'setting_default': 'Folder 4'},
{'setting_id': 'folder4.movies_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder4.tv_shows_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder5.display_name', 'setting_type': 'string', 'setting_default': 'Folder 5'},
{'setting_id': 'folder5.movies_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'folder5.tv_shows_directory', 'setting_type': 'path', 'setting_default': 'None', 'browse_mode': '0'},
{'setting_id': 'extras.enabled', 'setting_type': 'string', 'setting_default': '2050,2051,2052,2053,2054,2055,2056,2057,2058,2059,2060,2061,2062,2063,2064,2065,2066'},
{'setting_id': 'extras.order', 'setting_type': 'string', 'setting_default': '2050,2051,2052,2053,2054,2055,2056,2057,2058,2059,2060,2061,2062,2063,2064,2065,2066'},
{'setting_id': 'rescrape.enabled', 'setting_type': 'string', 'setting_default': 'cache_ignored,imdb_year,with_all,episode_group,ignore_filters'},
{'setting_id': 'rescrape.order', 'setting_type': 'string', 'setting_default': 'cache_ignored,imdb_year,with_all,episode_group,ignore_filters'},
{'setting_id': 'extras.tvshow.button10', 'setting_type': 'string', 'setting_default': 'tvshow_browse'},
{'setting_id': 'extras.tvshow.button11', 'setting_type': 'string', 'setting_default': 'show_trailers'},
{'setting_id': 'extras.tvshow.button12', 'setting_type': 'string', 'setting_default': 'show_keywords'},
{'setting_id': 'extras.tvshow.button13', 'setting_type': 'string', 'setting_default': 'show_images'},
{'setting_id': 'extras.tvshow.button14', 'setting_type': 'string', 'setting_default': 'show_extrainfo'},
{'setting_id': 'extras.tvshow.button15', 'setting_type': 'string', 'setting_default': 'show_genres'},
{'setting_id': 'extras.tvshow.button16', 'setting_type': 'string', 'setting_default': 'play_nextep'},
{'setting_id': 'extras.tvshow.button17', 'setting_type': 'string', 'setting_default': 'show_options'},
{'setting_id': 'extras.movie.button10', 'setting_type': 'string', 'setting_default': 'movies_play'},
{'setting_id': 'extras.movie.button11', 'setting_type': 'string', 'setting_default': 'show_trailers'},
{'setting_id': 'extras.movie.button12', 'setting_type': 'string', 'setting_default': 'show_keywords'},
{'setting_id': 'extras.movie.button13', 'setting_type': 'string', 'setting_default': 'show_images'},
{'setting_id': 'extras.movie.button14', 'setting_type': 'string', 'setting_default': 'show_extrainfo'},
{'setting_id': 'extras.movie.button15', 'setting_type': 'string', 'setting_default': 'show_genres'},
{'setting_id': 'extras.movie.button16', 'setting_type': 'string', 'setting_default': 'show_director'},
{'setting_id': 'extras.movie.button17', 'setting_type': 'string', 'setting_default': 'show_options'},
{'setting_id': 'updatechecks.refresh_addon_keys', 'setting_type': 'string', 'setting_default': 'false'}
	]
