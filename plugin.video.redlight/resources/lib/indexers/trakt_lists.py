# -*- coding: utf-8 -*-
import os
import sys
import json
from random import shuffle
from threading import Thread
from apis.trakt_api import trakt_get_lists, trakt_search_lists, get_trakt_list_contents, trakt_lists_with_media
from caches.trakt_cache import get_all_lists_custom_sort, set_list_custom_sort, delete_list_custom_sort
from indexers.movies import Movies
from indexers.tvshows import TVShows
from indexers.seasons import single_seasons
from indexers.episodes import build_single_episode
from modules import kodi_utils
from modules.utils import paginate_list, gen_md5, get_datetime, get_current_timestamp
from modules.settings import paginate, page_limit, widget_hide_next_page, tmdb_api_key, mpaa_region, jump_to_enabled
# logger = kodi_utils.logger

def search_trakt_lists(params):
	def _builder():
		for item in lists:
			try:
				list_key = item['type']
				list_info = item[list_key]
				if list_key == 'officiallist': continue
				item_count = list_info['item_count']
				if list_info['privacy'] == 'private' or item_count == 0: continue
				list_name, user, list_id = list_info['name'], list_info['username'], list_info['ids']['trakt']
				if not list_id: continue
				display = '%s | [I]%s (x%s)[/I]' % (list_name, user, str(item_count))
				url = build_url({'mode': 'trakt.list.build_trakt_list', 'list_id': list_id, 'list_type': 'user_lists', 'list_name': list_name, 'user': user,
				'iconImage': 'trakt', 'name': list_name})
				cm = [('[B]Like List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.trakt_like_a_list', 'list_id': list_id})),
				('[B]Unlike List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.trakt_unlike_a_list', 'list_id': list_id})),
				('[B]Add to Shortcut Folder[/B]', 'RunPlugin(%s)' % build_url({'mode': 'menu_editor.shortcut_folder_add_known', 'url': url}))]
				listitem = make_listitem()
				listitem.setLabel(display)
				listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': fanart})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				listitem.addContextMenuItems(cm)
				yield (url, listitem, True)
			except: pass
	handle, search_title, trakt_icon, fanart = int(sys.argv[1]), '', kodi_utils.get_icon('trakt'), kodi_utils.get_addon_fanart()
	build_url, make_listitem = kodi_utils.build_url, kodi_utils.make_listitem
	try:
		mode = params.get('mode')
		page = params.get('new_page', '1')
		search_title = params.get('key_id') or params.get('query')
		lists, pages = trakt_search_lists(search_title, page)
		kodi_utils.add_items(handle, list(_builder()))
		if pages > page:
			new_page = str(int(page) + 1)
			kodi_utils.add_dir(handle, {'mode': mode, 'key_id': search_title, 'new_page': new_page}, 'Next Page (%s) >>' % new_page,
								'nextpage', kodi_utils.get_icon('nextpage_landscape'))
	except: pass
	kodi_utils.set_content(handle, 'files')
	kodi_utils.set_category(handle, search_title.capitalize())
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.main')

def get_trakt_lists(params):
	def get_custom_image(list_name, list_type, user, image_type, images):
		try:
			md5_image_name = gen_md5('%s_%s' % (list_name, user))
			custom_image = [i for i in images if i.rsplit('_', 1)[0] == md5_image_name][0]
			return os.path.join(profile_path, 'images', 'trakt_%s_%s' % (list_type, image_type), custom_image)
		except: return ''
	def _process():
		for item in data:
			try:
				cm = []
				cm_append = cm.append
				list_name, list_id, user, slug, item_count = item['name'], item['ids']['trakt'], item['user']['ids']['slug'], item['ids']['slug'], item['item_count']
				if user in (None, 'None'): continue
				if str(list_id) in all_custom_sorts:
					custom_sorts = all_custom_sorts[str(list_id)]
					sort_by, sort_how = custom_sorts['sort_by'], custom_sorts['sort_how']
				else: sort_by, sort_how =  item['sort_by'], item['sort_how']
				custom_poster = get_custom_image(list_name, list_type, user, 'poster', all_posters)
				if custom_poster: poster = custom_poster
				else: poster = trakt_icon
				custom_fanart = get_custom_image(list_name, list_type, user, 'fanart', all_fanart)
				if custom_fanart: background = custom_fanart
				else: background = fanart
				mode = 'random.build_trakt_lists_contents' if random else 'trakt.list.build_trakt_list'
				url_params = {'mode': mode, 'user': user, 'slug': slug, 'list_type': list_type, 'list_id': list_id, 'list_name': list_name, 'iconImage': 'trakt',
				'name': list_name, 'sort_by': sort_by, 'sort_how': sort_how}
				if random: url_params['random'] = 'true'
				elif shuffle_lists: url_params['shuffle'] = 'true'
				url = build_url(url_params)
				if list_type == 'liked_lists':
					display = '%s | [I]%s (x%s)[/I]' % (list_name, user, str(item_count))
					cm_append(('[B]Unlike List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug})))
				else:
					display = '%s [I](x%s)[/I]' % (list_name, str(item_count))
					cm_append(('[B]Make New List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.make_new_trakt_list'})))
					cm_append(('[B]Delete List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.delete_trakt_list', 'user': user, 'list_slug': slug})))
				cm_append(('[B]Add to Shortcut Folder[/B]', 'RunPlugin(%s)' % build_url({'mode': 'menu_editor.shortcut_folder_add_known', 'url': url})))
				cm_append(('[B]Set Custom Sort[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.list.set_list_custom_sort', 'list_id': list_id,
					'sort_by': sort_by, 'sort_how': sort_how})))
				cm_append(('[B]Make Custom Poster[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.list.make_custom_artwork', 'action': 'make_poster',
					'custom_image': custom_poster, 'list_name': list_name, 'list_type': list_type, 'list_id': list_id, 'user': user, 'list_slug': slug})))
				cm_append(('[B]Make Custom Fanart[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.list.make_custom_artwork', 'action': 'make_fanart',
					'custom_image': custom_fanart, 'list_name': list_name, 'list_type': list_type, 'list_id': list_id, 'user': user, 'list_slug': slug})))
				if custom_poster: cm_append(('[B]Delete Custom Poster[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.list.delete_current_image', 'custom_image': custom_poster})))
				if custom_fanart: cm_append(('[B]Delete Custom Fanart[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.list.delete_current_image', 'custom_image': custom_fanart})))
				listitem = make_listitem()
				listitem.setLabel(display)
				listitem.setArt({'icon': poster, 'poster': poster, 'thumb': poster, 'fanart': background, 'banner': background})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				listitem.addContextMenuItems(cm)
				yield (url, listitem, True)
			except: pass
	handle, trakt_icon, fanart = int(sys.argv[1]), kodi_utils.get_icon('trakt'), kodi_utils.get_addon_fanart()
	try:
		list_type, random, shuffle_lists = params['list_type'], params.get('random', 'false') == 'true', params.get('shuffle', 'false') == 'true'
		build_url, make_listitem = kodi_utils.build_url, kodi_utils.make_listitem
		profile_path = kodi_utils.addon_profile()
		all_posters = kodi_utils.list_dirs(os.path.join(profile_path, 'images', 'trakt_%s_poster' % list_type))[1]
		all_fanart = kodi_utils.list_dirs(os.path.join(profile_path, 'images', 'trakt_%s_fanart' % list_type))[1]
		returning_to_list = False
		data = trakt_get_lists(list_type)
		all_custom_sorts = get_all_lists_custom_sort()
		if list_type == 'liked_lists': data = [i['list'] for i in data]
		if data:
			if shuffle_lists:
				returning_to_list = 'build_trakt_lists_contents' in kodi_utils.folder_path()
				if returning_to_list:
					try: data = json.loads(kodi_utils.get_property('redlight.trakt.lists.order'))
					except: pass
				else:
					shuffle(data)
					kodi_utils.set_property('redlight.trakt.lists.order', json.dumps(data))
			else:
				kodi_utils.clear_property('redlight.trakt.lists.order')
				data.sort(key=lambda k: k['name'])
			result = list(_process())
		else: result = list(_new_process())
		kodi_utils.add_items(handle, result)
	except: pass
	kodi_utils.set_content(handle, 'files')
	kodi_utils.set_category(handle, params.get('category_name', ''))
	if shuffle_lists and not returning_to_list: kodi_utils.focus_index(0)
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.main')

def get_trakt_user_lists(params):
	def _process():
		for _list in lists:
			try:
				cm = []
				cm_append = cm.append
				item = _list['list']
				item_count = item.get('item_count', 0)
				if item_count == 0: continue
				list_name, list_id, user, slug = item['name'], item['ids']['trakt'], item['user']['ids']['slug'], item['ids']['slug']
				if not slug: continue
				if item['type'] == 'official': user = 'Trakt Official'
				if not user: continue
				sort_by, sort_how =  item['sort_by'], item['sort_how']
				display = '%s | [I]%s (x%s)[/I]' % (list_name, user, str(item_count))
				mode = 'random.build_trakt_lists_contents' if random else 'trakt.list.build_trakt_list'
				url_params = {'mode': mode, 'user': user, 'slug': slug, 'list_id': list_id, 'list_type': 'user_lists', 'list_name': list_name, 'iconImage': 'trakt',
								'name': list_name, 'sort_by': sort_by, 'sort_how': sort_how}
				if random: url_params['random'] = 'true'
				url = build_url(url_params)
				listitem = make_listitem()
				if user != 'Trakt Official':
					cm_append(('[B]Like List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.trakt_like_a_list', 'user': user, 'list_slug': slug})))
					cm_append(('[B]Unlike List[/B]', 'RunPlugin(%s)' % build_url({'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug})))
				cm_append(('[B]Add to Shortcut Folder[/B]', 'RunPlugin(%s)' % build_url({'mode': 'menu_editor.shortcut_folder_add_known', 'url': url})))
				listitem.addContextMenuItems(cm)
				listitem.setLabel(display)
				listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': fanart})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				yield (url, listitem, True)
			except: pass
	handle, trakt_icon, fanart = int(sys.argv[1]), kodi_utils.get_icon('trakt'), kodi_utils.get_addon_fanart()
	build_url, make_listitem = kodi_utils.build_url, kodi_utils.make_listitem
	try:
		list_type, random = params['list_type'], params.get('random', 'false') == 'true'
		page = params.get('new_page', '1')
		new_page = str(int(page) + 1)
		lists = trakt_get_lists(list_type, page)
		kodi_utils.add_items(handle, list(_process()))
		kodi_utils.add_dir(handle, {'mode': 'trakt.list.get_trakt_user_lists', 'list_type': list_type, 'new_page': new_page},
				'Next Page (%s) >>' % new_page, 'nextpage', kodi_utils.get_icon('nextpage_landscape'))
	except: pass
	kodi_utils.set_content(handle, 'files')
	kodi_utils.set_category(handle, params.get('category_name', 'Trakt Lists'))
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.main')

def in_trakt_lists(params):
	def _process():
		for item in lists:
			try:
				cm = []
				cm_append = cm.append
				item_count = item.get('item_count', 0)
				list_name, user, slug = item['name'], item['user']['ids']['slug'], item['ids']['slug']
				display = '%s | [I]%s (x%s)[/I]' % (list_name, user, str(item_count))
				url = kodi_utils.build_url({'mode': 'trakt.list.build_trakt_list', 'user': user, 'slug': slug, 'list_type': 'user_lists', 'list_name': list_name})
				listitem = kodi_utils.make_listitem()
				if not user == 'Trakt Official':
					cm_append(('[B]Like List[/B]', 'RunPlugin(%s)' % kodi_utils.build_url({'mode': 'trakt.trakt_like_a_list', 'user': user, 'list_slug': slug})))
					cm_append(('[B]Unlike List[/B]', 'RunPlugin(%s)' % kodi_utils.build_url({'mode': 'trakt.trakt_unlike_a_list', 'user': user, 'list_slug': slug})))
				listitem.addContextMenuItems(cm)
				listitem.setLabel(display)
				listitem.setArt({'icon': trakt_icon, 'poster': trakt_icon, 'thumb': trakt_icon, 'fanart': fanart, 'banner': fanart})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				yield (url, listitem, True)
			except: pass
	handle, trakt_icon, fanart = int(sys.argv[1]), kodi_utils.get_icon('trakt'), kodi_utils.get_addon_fanart()
	try:
		lists = trakt_lists_with_media(params['media_type'], params['imdb_id'])
		kodi_utils.add_items(handle, list(_process()))
	except: pass
	kodi_utils.set_content(handle, 'files')
	kodi_utils.set_category(handle, params.get('category_name', 'Trakt Lists'))
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.main')

def build_trakt_list(params):
	def _process(function, _list, _type):
		if not _list['list']: return
		if _type in ('movies', 'tvshows'): item_list_extend(function(_list).worker())
		elif _type == 'seasons': item_list_extend(function(_list['list']))
		else: item_list_extend(function('episode.trakt_list', _list['list']))
	def _paginate_list(data, page_no, paginate_start):
		if use_result: total_pages = 1
		elif paginate_enabled:
			limit = page_limit(is_external)
			data, total_pages = paginate_list(data, page_no, limit, paginate_start)
			if is_external: paginate_start = limit
		else: total_pages = 1
		return data, total_pages, paginate_start
	handle, is_external, list_name, content = int(sys.argv[1]), kodi_utils.external(), params.get('list_name'), 'movies'
	hide_next_page = is_external and widget_hide_next_page()
	try:
		threads, item_list = [], []
		item_list_extend = item_list.extend
		paginate_enabled = paginate(is_external)
		use_result = 'result' in params
		page_no, paginate_start = int(params.get('new_page', '1')), int(params.get('paginate_start', '0'))
		if page_no == 1 and not is_external: kodi_utils.set_property('redlight.exit_params', kodi_utils.folder_path())
		if use_result: result = params.get('result', [])
		else:
			user, slug, list_id, list_type = params.get('user'), params.get('slug'), params.get('list_id'), params.get('list_type')
			sort_by, sort_how = params.get('sort_by'), params.get('sort_how')
			with_auth = list_type == 'my_lists'
			result = get_trakt_list_contents(list_type, user, slug, with_auth, list_id, sort_by, sort_how)
		process_list, total_pages, paginate_start = _paginate_list(result, page_no, paginate_start)
		all_movies = [i for i in process_list if i['type'] == 'movie']
		all_tvshows = [i for i in process_list if i['type'] == 'show']
		all_seasons = [i for i in process_list if i['type'] == 'season']
		all_episodes = [i for i in process_list if i['type'] == 'episode']
		movie_list = {'list': [(i['order'], i['media_ids']) for i in all_movies], 'id_type': 'trakt_dict', 'custom_order': 'true'}
		tvshow_list = {'list': [(i['order'], i['media_ids']) for i in all_tvshows], 'id_type': 'trakt_dict', 'custom_order': 'true'}
		season_list = {'list': all_seasons}
		episode_list = {'list': all_episodes}
		content = max([('movies', len(all_movies)), ('tvshows', len(all_tvshows)), ('seasons', len(all_seasons)), ('episodes', len(all_episodes))], key=lambda k: k[1])[0]
		for item in ((Movies, movie_list, 'movies'), (TVShows, tvshow_list, 'tvshows'),
					(single_seasons, season_list, 'seasons'), (build_single_episode, episode_list, 'episodes')):
			threaded_object = Thread(target=_process, args=item)
			threaded_object.start()
			threads.append(threaded_object)
		[i.join() for i in threads]
		item_list.sort(key=lambda k: k[1])
		if use_result: return content, [i[0] for i in item_list]
		new_params = {'mode': 'trakt.list.build_trakt_list', 'list_type': list_type, 'list_name': list_name, 'user': user, 'slug': slug, 'paginate_start': paginate_start,
						'sort_by': sort_by, 'sort_how': sort_how}
		kodi_utils.add_items(handle, [i[0] for i in item_list])
		if total_pages > 2 and jump_to_enabled() and not is_external:
				kodi_utils.add_dir(handle, {'mode': 'navigate_to_page_choice', 'current_page': page_no, 'total_pages': total_pages, 'url_params': json.dumps(new_params)},
											'Jump To...', 'item_jump', kodi_utils.get_icon('item_jump_landscape'), isFolder=False)
		if total_pages > page_no and not hide_next_page:
			new_page = str(page_no + 1)
			new_params['new_page'] = new_page
			kodi_utils.add_dir(handle, new_params,  'Next Page (%s) >>' % new_page, 'nextpage', kodi_utils.get_icon('nextpage_landscape'))
	except: pass
	kodi_utils.set_content(handle, content)
	kodi_utils.set_category(handle, list_name)
	kodi_utils.end_directory(handle, cacheToDisc=False if is_external else True)
	if not is_external:
		if params.get('refreshed') == 'true': kodi_utils.sleep(1000)
		kodi_utils.set_view_mode('view.%s' % content, content, is_external)

def make_custom_artwork(params):
	action, list_name, list_type, list_id = params['action'], params['list_name'], params['list_type'], params['list_id'],
	user, slug, custom_image = params['user'], params['list_slug'], params['custom_image']
	art_type, image_type = ('Posters', 'poster') if action == 'make_poster' else ('Fanart', 'fanart')
	shuffle_art = kodi_utils.confirm_dialog(
		heading='Trakt My Lists', text='Use [B]4 Random[/B] %s from List?[CR]OR[CR]Use [B]First 4[/B] %s from List?' % (art_type, art_type),
		ok_label='4 Random', cancel_label='First 4')
	if shuffle_art == None: return
	new_image = trakt_image_maker(list_name, list_type, list_id, image_type, user, slug, custom_image, shuffle_art)
	kodi_utils.kodi_refresh()

def trakt_image_maker(list_name, list_type, list_id, image_type, user, slug, custom_image, shuffle_sort_order):
	from caches.trakt_cache import get_list_custom_sort
	from modules import metadata
	from modules.utils import make_image
	kodi_utils.show_busy_dialog()
	sort_info = get_list_custom_sort(list_id)
	sort_by, sort_how = sort_info['sort_by'], sort_info['sort_how']
	content = get_trakt_list_contents(list_type, user, slug, True, list_id, sort_by, sort_how)
	if shuffle_sort_order: shuffle(content)
	images = []
	api_key, mpaa, current_time, current_timestamp = tmdb_api_key(), mpaa_region(), get_datetime(), get_current_timestamp()
	for item in content:
		try:
			tmdb_id = item.get('tmdb_id') or item['media_ids']['tmdb']
			if not tmdb_id: continue
			media_type = item.get('type') or media_type_check[trakt_media_type]
			if media_type == 'movie': function = metadata.movie_meta
			else: function = metadata.tvshow_meta
			meta = function('tmdb_id', tmdb_id, api_key, mpaa, current_time, current_timestamp)
			if meta.get(image_type): images.append(meta[image_type])
			if len(images) == 4: break
		except: pass
	final_image = make_image('trakt_%s' % list_type, image_type, '%s_%s' % (list_name, user), images, custom_image)
	kodi_utils.hide_busy_dialog()
	return final_image

def delete_current_image(params):
	custom_image = params['custom_image']
	os.remove(custom_image)
	kodi_utils.sleep(1000)
	success = not kodi_utils.path_exists(custom_image)
	if success: kodi_utils.kodi_refresh()
	else: kodi_utils.notification('Error Deleting Image')

def set_list_custom_sort(params):
	list_id, current_by, current_how = params['list_id'], params['sort_by'], params['sort_how']
	choices = [('default', 'Default From Trakt%s'), ('rank', 'Rank%s'), ('added', 'Date Added%s'), ('title', 'Title%s'), ('released', 'Date Released%s'), ('runtime', 'Runtime%s'),
	('popularity', 'Popularity%s'), ('percentage', 'Percentage%s'), ('votes', 'Votes%s'), ('random', 'Random%s')]
	choices = [(i[0], i[1] % ('   [B][COLOR green][CURRENT][/COLOR][/B]' if i[0] == current_by else '')) for i in choices]
	list_items = [{'line1': item[1], 'line2': ''} for item in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Trakt List Custom Sort By', 'narrow_window': 'true'}
	sort_by = kodi_utils.select_dialog([i[0] for i in choices], **kwargs)
	if sort_by == None: return
	if sort_by == 'default':
		from caches.trakt_cache import delete_list_custom_sort
		success = delete_list_custom_sort(list_id)
		if success:
			kodi_utils.ok_dialog('Trakt List Custom Sort', 'Success')
			kodi_utils.kodi_refresh()
		else: kodi_utils.ok_dialog('Trakt List Custom Sort', 'An Error Occured')
		return
	else:
		choices = [('asc', 'Ascending%s'), ('desc', 'Descending%s')]
		choices = [(i[0], i[1] % ('   [B][COLOR green][CURRENT][/COLOR][/B]' if i[0] == current_how else '')) for i in choices]
		list_items = [{'line1': item[1], 'line2': ''} for item in choices]
		kwargs = {'items': json.dumps(list_items), 'heading': 'Trakt List Custom Sort How', 'narrow_window': 'true'}
		sort_how = kodi_utils.select_dialog([i[0] for i in choices], **kwargs)
		if sort_how == None: return
	from caches.trakt_cache import set_list_custom_sort
	success = set_list_custom_sort(list_id, {'list_id': list_id, 'sort_by': sort_by, 'sort_how': sort_how})
	if success:
		kodi_utils.ok_dialog('Trakt List Custom Sort', 'Success')
		kodi_utils.kodi_refresh()
	else: kodi_utils.ok_dialog('Trakt List Custom Sort', 'An Error Occured')
