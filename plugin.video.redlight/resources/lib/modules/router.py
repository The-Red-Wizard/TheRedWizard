# -*- coding: utf-8 -*-
from xbmc import getInfoLabel
from urllib.parse import parse_qsl
from modules.kodi_utils import external, get_property
# from modules.kodi_utils import logger

def sys_exit_check():
	if get_property('redlight.reuse_language_invoker') == 'false': return False
	return external()

def routing(sys):
	params = dict(parse_qsl(sys.argv[2][1:], keep_blank_values=True))
	mode = params.get('mode', 'navigator.main')
	if 'navigator.' in mode:
		from indexers.navigator import Navigator
		return exec('Navigator(params).%s()' % mode.split('.')[1])
	elif 'menu_editor.' in mode:
		from modules.menu_editor import MenuEditor
		return exec('MenuEditor(params).%s()' % mode.split('.')[1])
	elif 'personal_lists.' in mode:
		from indexers import personal_lists
		return exec('personal_lists.%s(params)' % mode.split('.')[1])
	elif 'tmdblist.' in mode:
		from indexers import tmdb_lists
		return exec('tmdb_lists.%s(params)' % mode.split('.')[1])
	elif 'easynews.' in mode:
		from indexers import easynews
		return exec('easynews.%s(params)' % mode.split('.')[1])
	elif 'playback.' in mode:
		from modules.kodi_utils import player_check
		return player_check(mode, params)
	elif 'choice' in mode:
		from indexers import dialogs
		return exec('dialogs.%s(params)' % mode)
	elif 'custom_key.' in mode:
		from modules import custom_keys
		return exec('custom_keys.%s()' % mode.split('custom_key.')[1])
	elif 'trakt.' in mode:
		if '.list' in mode:
			from indexers import trakt_lists
			return exec('trakt_lists.%s(params)' % mode.split('.')[2])
		from apis import trakt_api
		return exec('trakt_api.%s(params)' % mode.split('.')[1])
	elif 'build' in mode:
		if mode == 'build_movie_list':
			from indexers.movies import Movies
			return Movies(params).fetch_list()
		elif mode == 'build_tvshow_list':
			from indexers.tvshows import TVShows
			return TVShows(params).fetch_list()
		elif mode == 'build_season_list':
			from indexers.seasons import build_season_list
			return build_season_list(params)
		elif mode == 'build_episode_list':
			from indexers.episodes import build_episode_list
			return build_episode_list(params)
		elif mode == 'build_in_progress_episode':
			from indexers.episodes import build_single_episode
			return build_single_episode('episode.progress', params)
		elif mode == 'build_recently_watched_episode':
			from indexers.episodes import build_single_episode
			return build_single_episode('episode.recently_watched', params)
		elif mode == 'build_next_episode':
			from indexers.episodes import build_single_episode
			return build_single_episode('episode.next', params)
		elif mode == 'build_my_calendar':
			from indexers.episodes import build_single_episode
			return build_single_episode('episode.trakt', params)
		elif mode == 'build_next_episode_manager':
			from modules.episode_tools import build_next_episode_manager
			return build_next_episode_manager()
		elif mode == 'build_tmdb_people':
			from indexers.people import tmdb_people
			return tmdb_people(params)
		elif 'random.' in mode:
			from indexers.random_lists import RandomLists
			return RandomLists(params).run_random()
	elif 'watched_status.' in mode:
		if mode == 'watched_status.mark_episode':
			from modules.watched_status import mark_episode
			return mark_episode(params)
		elif mode == 'watched_status.mark_season':
			from modules.watched_status import mark_season
			return mark_season(params)
		elif mode == 'watched_status.mark_tvshow':
			from modules.watched_status import mark_tvshow
			return mark_tvshow(params)
		elif mode == 'watched_status.mark_movie':
			from modules.watched_status import mark_movie
			return mark_movie(params)
		elif mode == 'watched_status.erase_bookmark':
			from modules.watched_status import erase_bookmark
			return erase_bookmark(params.get('media_type'), params.get('tmdb_id'), params.get('season', ''), params.get('episode', ''), params.get('refresh', 'false'))
		elif mode == 'watched_status.unmark_previous_episode':
			from modules.watched_status import unmark_previous_episode
			return unmark_previous_episode(params)
	elif 'search.' in mode:
		if mode == 'search.get_key_id':
			from modules.search import get_key_id
			return get_key_id(params)
		elif mode == 'search.clear_search':
			from modules.search import clear_search
			return clear_search()
		elif mode == 'search.remove':
			from modules.search import remove_from_search
			return remove_from_search(params)
		elif mode == 'search.clear_all':
			from modules.search import clear_all
			return clear_all(params.get('setting_id'), params.get('refresh', 'false'))
	elif 'real_debrid' in mode:
		if mode == 'real_debrid.rd_cloud':
			from indexers.real_debrid import rd_cloud
			return rd_cloud()
		elif mode == 'real_debrid.rd_downloads':
			from indexers.real_debrid import rd_downloads
			return rd_downloads()
		elif mode == 'real_debrid.browse_rd_cloud':
			from indexers.real_debrid import browse_rd_cloud
			return browse_rd_cloud(params.get('id'))
		elif mode == 'real_debrid.resolve_rd':
			from indexers.real_debrid import resolve_rd
			return resolve_rd(params)
		elif mode == 'real_debrid.rd_account_info':
			from indexers.real_debrid import rd_account_info
			return rd_account_info()
		elif mode == 'real_debrid.authenticate':
			from apis.real_debrid_api import RealDebridAPI
			return RealDebridAPI().auth()
		elif mode == 'real_debrid.revoke_authentication':
			from apis.real_debrid_api import RealDebridAPI
			return RealDebridAPI().revoke()
		elif mode == 'real_debrid.delete':
			from indexers.real_debrid import rd_delete
			return rd_delete(params.get('id'), params.get('cache_type'))
	elif 'premiumize' in mode:
		if mode == 'premiumize.pm_cloud':
			from indexers.premiumize import pm_cloud
			return pm_cloud(params.get('id', None), params.get('folder_name', None))
		elif mode == 'premiumize.pm_transfers':
			from indexers.premiumize import pm_transfers
			return pm_transfers()
		elif mode == 'premiumize.pm_account_info':
			from indexers.premiumize import pm_account_info
			return pm_account_info()
		elif mode == 'premiumize.authenticate':
			from apis.premiumize_api import PremiumizeAPI
			return PremiumizeAPI().auth()
		elif mode == 'premiumize.revoke_authentication':
			from apis.premiumize_api import PremiumizeAPI
			return PremiumizeAPI().revoke()
		elif mode == 'premiumize.rename':
			from indexers.premiumize import pm_rename
			return pm_rename(params.get('file_type'), params.get('id'), params.get('name'))
		elif mode == 'premiumize.delete':
			from indexers.premiumize import pm_delete
			return pm_delete(params.get('file_type'), params.get('id'))
	elif 'alldebrid' in mode:
		if mode == 'alldebrid.ad_cloud':
			from indexers.alldebrid import ad_cloud
			return ad_cloud(params.get('id', None))
		elif mode == 'alldebrid.ad_downloads':
			from indexers.alldebrid import ad_downloads
			return ad_downloads()
		elif mode == 'alldebrid.ad_saved_links':
			from indexers.alldebrid import ad_saved_links
			return ad_saved_links()
		elif mode == 'alldebrid.browse_ad_cloud':
			from indexers.alldebrid import browse_ad_cloud
			return browse_ad_cloud(params.get('id'))
		elif mode == 'alldebrid.resolve_ad':
			from indexers.alldebrid import resolve_ad
			return resolve_ad(params)
		elif mode == 'alldebrid.ad_account_info':
			from indexers.alldebrid import ad_account_info
			return ad_account_info()
		elif mode == 'alldebrid.authenticate':
			from apis.alldebrid_api import AllDebridAPI
			return AllDebridAPI().auth()
		elif mode == 'alldebrid.revoke_authentication':
			from apis.alldebrid_api import AllDebridAPI
			return AllDebridAPI().revoke()
		elif mode == 'alldebrid.delete':
			from indexers.alldebrid import ad_delete
			return ad_delete(params.get('id'))
	elif 'torbox' in mode:
		if mode == 'torbox.tb_cloud':
			from indexers.torbox import tb_cloud
			return tb_cloud()
		elif mode == 'torbox.browse_tb_cloud':
			from indexers.torbox import browse_tb_cloud
			return browse_tb_cloud(params.get('folder_id'), params.get('media_type'))
		elif mode == 'torbox.resolve_tb':
			from indexers.torbox import resolve_tb
			return resolve_tb(params)
		elif mode == 'torbox.tb_account_info':
			from indexers.torbox import tb_account_info
			return tb_account_info()
		elif mode == 'torbox.authenticate':
			from apis.torbox_api import TorBoxAPI
			return TorBoxAPI().auth()
		elif mode == 'torbox.revoke_authentication':
			from apis.torbox_api import TorBoxAPI
			return TorBoxAPI().revoke()
		elif mode == 'torbox.delete':
			from indexers.torbox import tb_delete
			return tb_delete(params.get('folder_id'), params.get('media_type'))
		elif mode == 'torbox.send_webdl':
			from indexers.torbox import tb_send_webdl
			tb_send_webdl()
	elif 'tmdblist_api' in mode:
		if mode == 'tmdblist_api.authenticate':
			from apis.tmdblist_api import TMDbListAPI
			return TMDbListAPI().auth()
		elif mode == 'tmdblist_api.revoke_authentication':
			from apis.tmdblist_api import TMDbListAPI
			return TMDbListAPI().revoke()
	elif '_cache' in mode:
		from caches import base_cache
		if mode == 'clear_cache':
			return base_cache.clear_cache(params.get('cache'))
		elif mode == 'clear_all_cache':
			return base_cache.clear_all_cache()
		elif mode == 'clean_databases_cache':
			return base_cache.clean_databases()
		elif mode == 'check_databases_integrity_cache':
			return base_cache.check_databases_integrity()
	elif '_image' in mode:
		from indexers.images import Images
		return Images().run(params)
	elif '_text' in mode:
		if mode == 'show_text':
			from modules.kodi_utils import show_text
			return show_text(params.get('heading'), params.get('text', None), params.get('file', None),
							params.get('font_size', 'small'), params.get('kodi_log', 'false') == 'true')
		elif mode == 'show_text_media':
			from modules.kodi_utils import show_text_media
			return show_text(params.get('heading'), params.get('text', None), params.get('file', None), params.get('meta'), {})
	elif 'settings_manager.' in mode:
		from caches import settings_cache
		return exec('settings_cache.%s(params)' % mode.split('.')[1])
	elif 'downloader.' in mode:
		from modules import downloader
		return exec('downloader.%s(params)' % mode.split('.')[1])
	elif 'updater' in mode:
		from modules import updater
		return exec('updater.%s()' % mode.split('.')[1])
	##EXTRA modes##
	elif mode == 'set_view':
		from modules.kodi_utils import set_view
		return kodi_utils.set_view(params.get('view_type'))
	elif mode == 'sync_settings':
		from caches.settings_cache import sync_settings
		return sync_settings(params)
	elif mode == 'person_direct.search':
		from indexers.people import person_direct_search
		return person_direct_search(params.get('key_id') or params.get('query'))
	elif mode == 'kodi_refresh':
		from modules.kodi_utils import kodi_refresh
		return kodi_refresh()
	elif mode == 'refresh_widgets':
		from modules.kodi_utils import refresh_widgets
		return refresh_widgets()
	elif mode == 'person_data_dialog':
		from indexers.people import person_data_dialog
		return person_data_dialog(params)
	elif mode == 'favorite_people':
		from indexers.people import favorite_people
		return favorite_people()
	elif mode == 'manual_add_magnet_to_cloud':
		from modules.debrid import manual_add_magnet_to_cloud
		return manual_add_magnet_to_cloud(params)
	elif mode == 'upload_logfile':
		from modules.kodi_utils import upload_logfile
		return upload_logfile(params)
	elif mode == 'downloader':
		from modules.downloader import runner
		return runner(params)
	elif mode == 'debrid.browse_packs':
		from modules.sources import Sources
		return Sources().debridPacks(params.get('provider'), params.get('name'), params.get('magnet_url'), params.get('info_hash'))
	elif mode == 'open_settings':
		from modules.kodi_utils import open_settings
		return open_settings()
	elif mode == 'hide_unhide_progress_items':
		from modules.watched_status import hide_unhide_progress_items
		return hide_unhide_progress_items(params)
	elif mode == 'open_external_scraper_settings':
		from modules.kodi_utils import external_scraper_settings
		return external_scraper_settings()
