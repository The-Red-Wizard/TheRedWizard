# -*- coding: utf-8 -*-
from urllib.parse import parse_qsl
from modules.kodi_utils import get_infolabel, activate_window, container_update, hide_busy_dialog
from indexers import dialogs
# from modules.kodi_utils import logger

def extras_menu():
	params = get_params('extras_params')
	if params: dialogs.extras_menu_choice(params)

def options_menu():
	params = get_params('options_params')
	if params: dialogs.options_menu_choice(params)

def playback_options():
	params = get_params('playback_options_params')
	if params: dialogs.playback_choice(params)

def browse_movie_set():
	params = get_params('browse_movie_set_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def browse_recommended():
	params = get_params('browse_recommended_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def browse_related():
	params = get_params('browse_related_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def browse_more_like_this():
	hide_busy_dialog()
	params = get_params('browse_more_like_this_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def browse_similar():
	params = get_params('browse_similar_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def browse_in_trakt_list():
	params = get_params('browse_in_trakt_list_params')
	if params:
		window_function = activate_window if params['is_external'] in (True, 'True', 'true') else container_update
		return window_function(params)

def trakt_manager():
	params = get_params('trakt_manager_params')
	if params: dialogs.trakt_manager_choice(params)

def personal_manager():
	params = get_params('personal_manager_params')
	if params: dialogs.personallists_manager_choice(params)

def tmdb_manager():
	params = get_params('tmdb_manager_params')
	if params: dialogs.tmdblists_manager_choice(params)

def favorites_manager():
	params = get_params('favorites_manager_params')
	if params: dialogs.favorites_manager_choice(params)

def get_params(param_name):
	try: params = dict(parse_qsl(get_infolabel('ListItem.Property(redlight.%s)' % param_name).split('plugin://plugin.video.redlight/?')[1], keep_blank_values=True))
	except: params = None
	return params