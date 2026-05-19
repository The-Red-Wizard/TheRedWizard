# -*- coding: utf-8 -*-
import json
from caches.settings_cache import get_setting, set_setting, set_default, default_setting_values
from modules import kodi_utils, settings
# logger = kodi_utils.logger

def window_theme_choice(params):
	if params['type'] == 'theme':
		choices = kodi_utils.addon_themes()
		list_items = [{'line1': i['name'], 'icon': kodi_utils.get_icon(i['icon'], 'themes')} for i in choices]
		kwargs = {'items': json.dumps(list_items), 'heading': 'Assign a Theme', 'narrow_window': 'true'}
		choice = kodi_utils.select_dialog(choices, **kwargs)
		if choice == None: return
		window_theme, window_theme_contrast, window_theme_name = choice['value'][0][2:], choice['value'][1], choice['name']
		window_theme_opacity = get_setting('redlight.window_theme_opacity', 'CC')
		set_setting('window_theme_name', window_theme_name)
	else:
		choices = kodi_utils.addon_themes_opacity()
		list_items = [{'line1': i['name']} for i in choices]
		kwargs = {'items': json.dumps(list_items), 'heading': 'Assign an Opacity Level', 'narrow_window': 'true'}
		choice = kodi_utils.select_dialog(choices, **kwargs)
		if choice == None: return
		window_theme_opacity, window_theme_opacity_name = choice['value'], choice['name']
		window_theme = get_setting('redlight.window_theme', 'FF1F2020')[2:]
		window_theme_contrast = get_setting('redlight.window_theme_contrast', 'FF4a4347')
		set_setting('window_theme_opacity', window_theme_opacity)
		set_setting('window_theme_opacity_name', window_theme_opacity_name)
	set_setting('window_theme', window_theme_opacity + window_theme)
	set_setting('window_theme_contrast', window_theme_contrast)

def rpdb_poster_format_choice(params):
	choices = [{'name': 'default', 'value': ''}, {'name': 'blocks', 'value': '&theme=blocks'}, {'name': 'rounded', 'value': '&theme=rounded-blocks'}]
	list_items = [{'line1': i['name'], 'icon': kodi_utils.get_icon('rpdb_%s' % i['name'], 'rpdb_posters', 'jpg')} for i in choices]
	kwargs = {'items': json.dumps(list_items)}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	set_setting('rpdb_format', choice['value'])
	set_setting('rpdb_format_name', choice['name'])

def navigate_to_page_choice(params):
	def _builder():
		for item in start_list:
			if item == current_page: line1 = '[COLOR blue][B]Page %s   |   Current Page[/B][/COLOR]' % item
			else: line1 = 'Page %s' % item
			yield {'line1': line1}
	try:
		current_page, total_pages = int(params.get('current_page')), int(params.get('total_pages'))
		start_list = [i for i in range(1, total_pages+1)]
		list_items = list(_builder())
		kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true', 'set_focus': current_page - 1}
		new_page = kodi_utils.select_dialog(start_list, **kwargs)
		if new_page == None or new_page == current_page: return
		url_params = json.loads(params['url_params'])
		url_params.update({'new_page': new_page, 'refreshed': 'true'})
		kodi_utils.container_update(url_params)
	except: return

def list_display_order_choice(params):
	from modules.meta_lists import list_display_choices
	list_type = params['list_type']
	info = list_display_choices(list_type)
	choices = info['choices']
	list_items = [{'line1': i[0]} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	set_setting('%s.list_sort_name' % info['setting'], choice[0])
	set_setting('%s.list_sort' % info['setting'], choice[1])

def language_invoker_choice(params):
	from xml.dom.minidom import parse as mdParse
	kodi_utils.close_all_dialog()
	addon_xml = kodi_utils.translate_path('special://home/addons/plugin.video.redlight/addon.xml')
	root = mdParse(addon_xml)
	invoker_instance = root.getElementsByTagName('reuselanguageinvoker')[0].firstChild
	current_invoker_setting = invoker_instance.data
	new_value = {'true': 'false', 'false': 'true'}[current_invoker_setting]
	if not kodi_utils.confirm_dialog(text='Turn [B]Reuse Langauage Invoker[/B] %s?' % ('On' if new_value == 'true' else 'Off')): return
	invoker_instance.data = new_value
	new_xml = str(root.toxml()).replace('<?xml version="1.0" ?>', '')
	with open(addon_xml, 'w') as f: f.write(new_xml)
	set_setting('reuse_language_invoker', new_value)
	kodi_utils.execute_builtin('ActivateWindow(Home)', True)
	kodi_utils.update_local_addons()
	kodi_utils.disable_enable_addon()

def addon_icon_choice(params):
	import os
	from xml.dom.minidom import parse as mdParse
	addon_xml = kodi_utils.translate_path('special://home/addons/plugin.video.redlight/addon.xml')
	root = mdParse(addon_xml)
	icon_instance = root.getElementsByTagName('icon')[0].firstChild
	icons_path = 'special://home/addons/plugin.video.redlight/resources/media/addon_icons'
	all_icons = kodi_utils.list_dirs(kodi_utils.translate_path(icons_path))[1]
	all_icons.sort()
	list_items = [{'line1': i, 'icon': kodi_utils.translate_path(os.path.join(icons_path, i))} for i in all_icons]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose New Icon Image'}
	new_icon = kodi_utils.select_dialog(all_icons, **kwargs)
	if new_icon == None: return
	new_icon_path = 'resources/media/addon_icons/%s' % new_icon
	if not kodi_utils.confirm_dialog(text='Set New Icon?'): return
	icon_instance.data = new_icon_path
	new_xml = str(root.toxml()).replace('<?xml version="1.0" ?>', '')
	with open(addon_xml, 'w') as f: f.write(new_xml)
	set_setting('addon_icon_choice', new_icon_path)
	set_setting('addon_icon_choice_name', new_icon)
	kodi_utils.execute_builtin('ActivateWindow(Home)', True)
	kodi_utils.update_local_addons()
	kodi_utils.disable_enable_addon()

def rescrape_actions_choice(params):
	set_focus = params.get('set_focus', 0)
	action_values, order_values = {0: 'Off', 1: 'Auto', 2: 'Prompt'}, {0: 'Highest', 1: 'High', 2: 'Middle', 3: 'Low', 4: 'Lowest'}
	rescrape_settings = settings.rescrape_settings()
	choices = [dict(i, **{'line1': '%02d, %s' % (int(k[2]) + 1, i['name']),
				'line2': 'Current | Action: [B]%s[/B] | Order: [B]%s[/B]' % (action_values[k[1]], order_values[k[2]]), 'value': i['value'],
				'action': k[1], 'order': k[2]}) for i in kodi_utils.rescrape_items() for k in rescrape_settings if k[0] == i['value']]
	choices = [dict(i, **{'position': c}) for c, i in enumerate(sorted(choices, key=lambda k: k['order']))]
	kwargs = {'items': json.dumps(choices), 'heading': 'Choose Properties for Rescrape Functions', 'multi_line': 'true', 'narrow_window': 'true', 'set_focus': set_focus}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	choice_value, choice_action, choice_order = choice['value'], choice['action'], choice['order']
	params['set_focus'] = choice['position']
	choices = [{'line1': 'Set Action', 'action': 'set_action'}, {'line1': 'Set Order', 'action': 'set_order'}]
	kwargs = {'items': json.dumps(choices), 'heading': 'Choose Properties for Rescrape Functions', 'narrow_window': 'true', 'set_focus': set_focus}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return rescrape_actions_choice(params)
	action = choice['action']
	if action == 'set_action':
		choices = [{'line1': 'Off', 'value': '0'}, {'line1': 'Auto', 'value': '1'}, {'line1': 'Prompt', 'value': '2'}]
		heading, setting = 'Choose Action Value', 'rescrape.%s' % choice_value
		kwargs = {'items': json.dumps(choices), 'heading': heading, 'narrow_window': 'true'}
		choice = kodi_utils.select_dialog(choices, **kwargs)
		if choice == None: return rescrape_actions_choice(params)
		setting_value = choice['value']
		set_setting(setting, setting_value)
	else:
		choices = [{'line1': 'Highest', 'value': '0'}, {'line1': 'High', 'value': '1'}, {'line1': 'Middle', 'value': '2'},
					{'line1': 'Low', 'value': '3'}, {'line1': 'Lowest', 'value': '4'}]
		heading, setting = 'Choose Order', 'rescrape.%s.order'
		kwargs = {'items': json.dumps(choices), 'heading': heading, 'narrow_window': 'true'}
		choice = kodi_utils.select_dialog(choices, **kwargs)
		if choice == None: return rescrape_actions_choice(params)
		setting_value = choice['value']
		new_settings = list(rescrape_settings)
		new_settings.remove((choice_value, choice_action, choice_order))
		new_settings.insert(int(setting_value), (choice_value, choice_action, setting_value))
		for item in [(i[0], str(c)) for c, i in enumerate(new_settings)]: set_setting(setting % item[0], item[1])
		params['set_focus'] = int(setting_value)
	return rescrape_actions_choice(params)

def context_menu_choice(params):
	choices = kodi_utils.context_menu_items()
	current_settings = settings.cm_enabled()
	try: preselect = [choices.index(i) for i in choices if i['value'] in current_settings]
	except: preselect = []
	list_items = [{'line1': i['name']} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Enable Content for the Context Menu', 'multi_choice': 'true', 'preselect': preselect}
	selection = kodi_utils.select_dialog(choices, **kwargs)
	if selection  == []:
		kodi_utils.ok_dialog(text='You must select at least 1 item')
		return context_menu_choice(params)
	elif selection == None: return
	selection = [i['value'] for i in selection]
	set_setting('context_menu.enabled', ','.join(selection))

def context_menu_order_choice(params):
	set_focus = params.get('set_focus', 0)
	all_items = kodi_utils.context_menu_items()
	enabled_items = settings.cm_enabled()
	current_order = settings.cm_current_order()
	active_items = [i for i in all_items if i['value'] in enabled_items]
	sorted_active_items = sorted(active_items, key=lambda k: current_order.index(k['value']))
	choices = [{'line1': 'Position %02d' % (count + 1), 'line2': 'Currently [B]%s[/B]' % (item['name']),
			 'current_item': item, 'display_position': count + 1, 'position': count} for count, item in enumerate(sorted_active_items)]
	kwargs = {'items': json.dumps(choices), 'heading': 'Choose Order for Context Menu', 'multi_line': 'true', 'narrow_window': 'true', 'set_focus': set_focus}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	current_item = choice['current_item']
	position = choice['position']
	display_position = choice['display_position']
	choices = [{'line1': item['name'], 'value': item['value']} for item in active_items if item != current_item]
	kwargs = {'items': json.dumps(choices), 'narrow_window': 'true', 'heading': 'Choose Context Menu Item for Position %02d' % display_position}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice != None:
		value = choice['value']
		current_order.remove(value)
		current_order.insert(position, value)
		current_order = [str(i) for i in current_order]
		set_setting('context_menu.order', ','.join(current_order))
		params['set_focus'] = position
	return context_menu_order_choice(params)

def personallists_manager_choice(params):
	from indexers.personal_lists import get_all_personal_lists, make_new_personal_list, new_list_check
	icon = params.get('icon', None) or kodi_utils.get_icon('lists')
	list_type = params['list_type']
	all_lists = get_all_personal_lists(get_setting('redlight.personal_list.list_sort', '0'))
	choices = []
	if not all_lists: action = 'add_new'
	else:
		choices = [('Add To Personal List...', 'add'), ('Remove From Personal List...', 'remove'), ('Add To [B]NEW[/B] Personal List...', 'add_new')]
		list_items = [{'line1': item[0], 'icon': icon} for item in choices]
		kwargs = {'items': json.dumps(list_items), 'heading': 'Personal Lists Manager'}
		action = kodi_utils.select_dialog([i[1] for i in choices], **kwargs)
		if action == None: return
	if action == 'add_new':
		list_name, author = make_new_personal_list({'external_creation': 'true'})
		if not list_name: return kodi_utils.notification('Error Creating List', 3000)
		action = 'add'
	else:
		new_template, normal_template = '[COLOR FF008EB2]%s [I](x%02d)[/I][/COLOR]', '%s [I](x%02d)[/I]'
		choices = [((new_template if new_list_check(i['seen']) else normal_template) % (i['name'], i['total']), (i['name'], i['author'])) for i in all_lists]
		list_items = [{'line1': i[0]} for i in choices]
		kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
		try:list_name, author = kodi_utils.select_dialog([i[1] for i in choices], **kwargs)
		except: return
	if action == 'add': new_contents = {'media_id': params['tmdb_id'], 'title': params['title'], 'type': list_type,
										'release_date': params['premiered'], 'date_added': params['current_time']}
	else: new_contents = params['tmdb_id']
	from caches.personal_lists_cache import personal_lists_cache
	result = personal_lists_cache.add_remove_list_item(list_name, author, action, new_contents)
	kodi_utils.notification(result, 3000)
	if action == 'remove' and any([kodi_utils.path_check(list_name) or kodi_utils.external()]): kodi_utils.kodi_refresh()

def tmdblists_manager_choice(params):
	from caches.tmdb_lists import tmdb_lists_cache
	from indexers.tmdb_lists import get_all_tmdb_lists, make_new_tmdb_list, add_to_tmdb_list, remove_from_tmdb_list, check_item_status, check_item_status_watchfav, add_remove_watchfavs
	icon = params.get('icon', None) or kodi_utils.get_icon('tmdb')
	media_type, tmdb_id = params['media_type'], params['tmdb_id']
	choices = [('Add To TMDb List...', 'list_add'), ('Remove From TMDb List...', 'list_remove'), ('Add To [B]NEW[/B] TMDb List...', 'list_add_new'),
				('Add To [B]Watchlist[/B]', 'watchlist_add'), ('Remove From [B]Watchlist[/B]', 'watchlist_remove'),
				('Add To [B]Favorites[/B]', 'favorites_add'), ('Remove From [B]Favorites[/B]', 'favorites_remove')]
	list_items = [{'line1': item[0], 'icon': icon} for item in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'TMDb Lists Manager'}
	action = kodi_utils.select_dialog([i[1] for i in choices], **kwargs)
	if action == None: return
	if action.startswith(('watchlist', 'favorites')):
		from indexers.tmdb_lists import check_item_status_watchfav
		list_id = action.split('_')[0]
		status = True if 'add' in action else False
		item_in_list = check_item_status_watchfav(list_id, media_type, tmdb_id)
		if item_in_list and status: return kodi_utils.notification('Item already in %s' % list_id.capitalize())
		if not item_in_list and not status: return kodi_utils.notification('Item not in %s' % list_id.capitalize())
		success = add_remove_watchfavs(media_type, tmdb_id, list_id, status)
		tmdb_lists_cache.clear_watchfavrecs(list_id, media_type)
	else:
		from indexers.tmdb_lists import get_all_tmdb_lists, make_new_tmdb_list, add_to_tmdb_list, remove_from_tmdb_list, check_item_status
		all_lists = get_all_tmdb_lists('0')
		if not all_lists: action = 'list_add_new'
		if action == 'list_add_new':
			list_id = make_new_tmdb_list({'external_creation': 'true'})
			if not list_id: return kodi_utils.notification('Error Creating List')
			action, item_in_list = 'list_add', False
		else:
			choices = [('%s [I](x%02d)[/I]' % (i['name'], i['number_of_items']), i['id']) for i in all_lists]
			list_items = [{'line1': i[0]} for i in choices]
			kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
			list_id = kodi_utils.select_dialog([i[1] for i in choices], **kwargs)
			if list_id == None: return
			item_in_list = check_item_status(list_id, media_type, tmdb_id)
		new_contents = {'items': [{'media_type': media_type, 'media_id': tmdb_id}]}
		if action == 'list_add':
			if item_in_list: return kodi_utils.notification('Item already in List')
			success = add_to_tmdb_list(list_id, new_contents)
		elif action == 'list_remove':
			if not item_in_list: return kodi_utils.notification('Item not in List')
			success = remove_from_tmdb_list(list_id, new_contents)
		tmdb_lists_cache.clear_list(list_id)
		tmdb_lists_cache.clear_all_lists()
	kodi_utils.notification('Success' if success else 'Failed', 3000)
	if 'remove' in action and any([kodi_utils.path_check(str(list_id)) or kodi_utils.external()]): kodi_utils.kodi_refresh()

def favorites_manager_choice(params):
	from caches.favorites_cache import favorites_cache
	media_type, tmdb_id, title = params.get('media_type'), params.get('tmdb_id'), params.get('title')
	current_favorites = favorites_cache.get_favorites(media_type)
	people_favorite = media_type == 'people'
	current_favorite = any(i['tmdb_id'] == tmdb_id for i in current_favorites)
	if current_favorite:
		function, text = favorites_cache.delete_favourite, 'Remove From Favorites?'
		param_refresh = params.get('refresh', None)
		if param_refresh == None: refresh = any(i in kodi_utils.folder_path() for i in ('action=favorites_movies', 'action=favorites_tvshows', 'action=favorites_anime'))
		else: refresh = param_refresh == 'true'
	else: function, text, refresh = favorites_cache.set_favourite, 'Add To Favorites?', False
	heading = title.split('|')[0] if people_favorite else title
	if not kodi_utils.confirm_dialog(heading=heading, text=text): return
	success = function(media_type, tmdb_id, title)
	if success:
		if refresh: kodi_utils.kodi_refresh()
		kodi_utils.notification('Success', 3500)
	else: kodi_utils.notification('Error', 3500)
	if people_favorite and success: return text

def ai_model_order_choice(params):
	model_descriptions = {'gemini-2.5-flash-lite': ('GEMINI FAST, 20 RPD', 'gemini'), 'llama-3.3-70b-versatile': ('GROQ FAST, 140 RPD', 'groq'),
							'gemma-3-27b-it': ('GEMMA Fast, MANY RPD', 'gemma'), 'llama-3.1-8b-instant': ('GROQ FAST, MANY RPD', 'groq')}
	default_order = default_setting_values('ai_model.order')['setting_default'].split(',')
	current_order = settings.ai_model_order()
	choices = [{'line1': 'Position %02d' % (count + 1), 'line2': 'Currently [B]%s[/B] (%s)' % (item, model_descriptions[item][0]),
				'icon': kodi_utils.get_icon(model_descriptions[item][1]), 'current_item': item, 'display_position': count + 1, 'position': count}
				for count, item in enumerate(current_order)]
	kwargs = {'items': json.dumps(choices), 'multi_line': 'true', 'heading': 'Choose Sort Order Of AI Models'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	current_model_id = choice['current_item']
	position = choice['position']
	display_position = choice['display_position']
	choices = [{'line1': item, 'line2': model_descriptions[item][0], 'icon': kodi_utils.get_icon(model_descriptions[item][1]), 'model_id': item}
				for item in default_order if item != current_model_id]
	kwargs = {'items': json.dumps(choices), 'multi_line': 'true', 'heading': 'Choose Model for Position %02d' % display_position}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice != None:
		from caches.lists_cache import lists_cache
		lists_cache.delete_like("ai_similar_%")
		model_id = choice['model_id']
		current_order.remove(model_id)
		current_order.insert(position, model_id)
		set_setting('ai_model.order', ','.join(current_order))
	return ai_model_order_choice(params)

def extras_lists_choice(params={}):
	current_settings = settings.extras_enabled()
	choices = kodi_utils.extras_items()
	list_items = [{'line1': i['name']} for i in choices]
	try: preselect = [choices.index(i) for i in choices if i['value'] in current_settings]
	except: preselect = []
	kwargs = {'items': json.dumps(list_items), 'heading': 'Enable Content for Extras Lists', 'multi_choice': 'true', 'preselect': preselect}
	selection = kodi_utils.select_dialog(choices, **kwargs)
	if selection  == []:
		kodi_utils.ok_dialog(text='You must select at least 1 item')
		return extras_lists_choice(params)
	elif selection == None: return
	selection = [str(i['value']) for i in selection]
	set_setting('extras.enabled', ','.join(selection))

def extras_order_choice(params={}):
	all_items = kodi_utils.extras_items()
	enabled_items = settings.extras_enabled()
	current_order = settings.extras_order()
	active_items = [i for i in all_items if i['value'] in enabled_items]
	active_items = sorted(active_items, key=lambda k: current_order.index(k['value']))
	choices = [{'line1': 'Position %02d' % (count + 1), 'line2': 'Currently [B]%s[/B]' % (item['name']),
			 'current_item': item, 'display_position': count + 1, 'position': count} for count, item in enumerate(active_items)]
	kwargs = {'items': json.dumps(choices), 'heading': 'Choose Order Of Extras Lists', 'multi_line': 'true', 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None:
		if params.get('remake', False):
			from windows.base_window import ExtrasUtils
			ExtrasUtils().run()
		return
	current_item = choice['current_item']
	position = choice['position']
	display_position = choice['display_position']
	choices = [{'line1': item['name'], 'value': item['value']} for item in active_items if item != current_item]
	kwargs = {'items': json.dumps(choices), 'narrow_window': 'true', 'heading': 'Choose List Item for Position %02d' % display_position}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice != None:
		value = choice['value']
		current_order.remove(value)
		current_order.insert(position, value)
		current_order = [str(i) for i in current_order]
		set_setting('extras.order', ','.join(current_order))
		params['remake'] = True
	return extras_order_choice(params)

def preferred_filters_choice(params):
	from modules.source_utils import source_filters, include_exclude_filters
	def _default_choices():
		return [{'name': '1st Sort', 'value': 'Choose 1st Sort Param'}, {'name': '2nd Sort', 'value': 'Choose 2nd Sort Param'},
				{'name': '3rd Sort', 'value': 'Choose 3rd Sort Param'}, {'name': '4th Sort', 'value': 'Choose 4th Sort Param'},
				{'name': '5th Sort', 'value': 'Choose 5th Sort Param'}]
	def _beginning_choices():
		defaults = _default_choices()
		for count, item in enumerate(auto_settings): defaults[count]['value'] = item
		return defaults
	def _rechoose_checker(choice):
		if choice['value'].startswith('Choose'): return (choice, True)
		clear_choice = kodi_utils.confirm_dialog(heading='Current Param Active', text='This sort slot is already filled.[CR]Please choose what action to take.',
						ok_label='Remake Slot', cancel_label='Clear Slot')
		if clear_choice == None: new_default, ask_params = (choice, False)
		else:
			choice_index = choices.index(choice)
			new_default = _default_choices()[choice_index]
			choices[choice_index] = new_default
		return (new_default, clear_choice)
	def _param_choices(choice):
		filter_keys = include_exclude_filters()
		disabled_filters = [v for k, v in filter_keys.items() if settings.filter_status(k) == 1]
		s_filters = source_filters()
		filters_choice = [(i[0], i[1].replace('[B]', '').replace('[/B]', '')) for i in s_filters]
		filters_choice = [i for i in filters_choice if not i[1] in disabled_filters]
		unused_filters = [i for i in filters_choice if not i[1] in auto_settings]
		param_list_items = [{'line1': i[0], 'line2': i[1]} for i in unused_filters]
		param_kwargs = {'items': json.dumps(param_list_items), 'multi_line': 'true', 'heading': 'Choose Sort to Top Params for Autoplay', 'narrow_window': 'true'}
		param_choice = kodi_utils.select_dialog(unused_filters, **param_kwargs)
		if param_choice == None: return ''
		choice['value'] = param_choice[1]
		return choice
	def _make_settings():
		new_settings = [i['value'] for i in choices if not i['value'].startswith('Choose')]
		if not new_settings: set_setting('filter.preferred_filters', 'empty_setting')
		else: set_setting('filter.preferred_filters', ', '.join(new_settings))
	auto_settings = settings.preferred_filters()
	choices = params.get('choices') or _beginning_choices()
	list_items = [{'line1': i['name'], 'line2': i['value']} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'multi_line': 'true', 'heading': 'Choose Sort to Top Params for Autoplay', 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return _make_settings()
	choice, ask_params = _rechoose_checker(choice)
	if not ask_params: return preferred_filters_choice({'choices': choices})
	param_choice = _param_choices(choice)
	if not param_choice: return preferred_filters_choice({'choices': choices})
	choices[choices.index(choice)] = param_choice
	_make_settings()
	return preferred_filters_choice({'choices': choices})

def tmdb_api_check_choice(params):
	from apis.tmdb_api import movie_details
	data = movie_details('299534', settings.tmdb_api_key())
	if not data.get('success', True): text = 'There is an issue with your API Key.[CR][B]"Error: %s"[/B]' % data.get('status_message', '')
	else: text = 'Your TMDb API Key is enabled and working'
	return kodi_utils.ok_dialog(text=text)

def clear_sources_folder_choice(params):
	setting_id = params['setting_id']
	set_default(['%s.display_name' % setting_id, '%s.movies_directory' % setting_id, '%s.tv_shows_directory' % setting_id])

def widget_refresh_timer_choice(params):
	choices = [{'name': 'OFF', 'value': '0'}]
	choices.extend([{'name': 'Every %s Minutes' % i, 'value': str(i)} for i in range(5,25,5)])
	choices.extend([{'name': 'Every %s Minutes' % i, 'value': str(i)} for i in range(30,65,10)])
	choices.extend([{'name': 'Every %s Hours' % (float(i)/60), 'value': str(i)} for i in range(90,720,30)])
	list_items = [{'line1': i['name']} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	set_setting('widget_refresh_timer', choice['value'])
	set_setting('widget_refresh_timer_name', choice['name'])

def limit_number_quality_choice(params):
	choices = [{'name': 'OFF', 'value': '0'}]
	choices.extend([{'name': '%sx Per Quality' % i, 'value': str(i)} for i in range(1,5)])
	choices.extend([{'name': '%sx Per Quality' % i, 'value': str(i)} for i in range(5,205,5)])
	list_items = [{'line1': i['name']} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	set_setting('results.limit_number_quality', choice['value'])
	set_setting('results.limit_number_quality_name', choice['name'])

def limit_number_total_choice(params):
	choices = [{'name': 'OFF', 'value': '0'}]
	choices.extend([{'name': '%sx Total Results' % i, 'value': str(i)} for i in range(1,10)])
	choices.extend([{'name': '%sx Total Results' % i, 'value': str(i)} for i in range(10,1000,5)])
	list_items = [{'line1': i['name']} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return
	set_setting('results.limit_number_total', choice['value'])
	set_setting('results.limit_number_total_name', choice['name'])

def external_scraper_choice(params):
	from modules.utils import append_module_to_syspath, manual_function_import
	try:
		results = kodi_utils.jsonrpc_get_addons('xbmc.python.module')
		results = [i for i in results if kodi_utils.addon_enabled(i['addonid'])]
	except: return
	list_items = [{'line1': i['name'], 'icon': i['thumbnail']} for i in results]
	kwargs = {'items': json.dumps(list_items)}
	choice = kodi_utils.select_dialog(results, **kwargs)
	if choice == None: return
	module_id, module_name = choice['addonid'], choice['name']
	success = False
	try:
		append_module_to_syspath('special://home/addons/%s/lib' % module_id)
		main_folder_name = module_id.split('.')[-1]
		sourceDict = manual_function_import(main_folder_name, 'sources')(specified_folders=['torrents'])
		success = True
	except: pass
	if success:
		try:
			set_setting('external_scraper.module', module_id)
			set_setting('external_scraper.name', module_name)
			set_setting('provider.external', 'true')
			kodi_utils.ok_dialog(text='Success.[CR][B]%s[/B] set as External Scraper' % module_name)
		except: kodi_utils.ok_dialog(text='Error')
	else:
		kodi_utils.ok_dialog(text='The [B]%s[/B] Module is not compatible.[CR]Please choose a different Module...' % module_name.upper())
		return external_scraper_choice(params)

def audio_filters_choice(params={}):
	from modules.source_utils import audio_filter_choices
	icon = kodi_utils.get_icon('audio')
	audio_filters = audio_filter_choices()
	list_items = [{'line1': item[0], 'line2': item[1], 'icon': icon} for item in audio_filters]
	try: preselect = [audio_filters.index(item) for item in audio_filters if item[1] in settings.audio_filters()]
	except: preselect = []
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Audio Properties to Exclude', 'multi_choice': 'true', 'multi_line': 'true', 'preselect': preselect}
	selection = kodi_utils.select_dialog([i[1] for i in audio_filters], **kwargs)
	if selection == None: return
	if selection == []: set_setting('filter_audio', 'empty_setting')
	else: set_setting('filter_audio', ', '.join(selection))

def genres_choice(params):
	genres_list, genres, poster = params['genres_list'], params['genres'], params['poster']
	genre_list = [i for i in genres_list if i['name'] in genres]
	if not genre_list:
		kodi_utils.notification('No Results', 2500)
		return None
	list_items = [{'line1': i['name'], 'icon': poster} for i in genre_list]
	kwargs = {'items': json.dumps(list_items)}
	return kodi_utils.select_dialog([i['id'] for i in genre_list], **kwargs)

def keywords_choice(params):
	media_type, meta = params['media_type'], params['meta']
	keywords, tmdb_id, poster = meta.get('keywords', []), meta['tmdb_id'], meta['poster']
	if keywords: keywords = keywords.get('keywords') or keywords.get('results')
	else:
		kodi_utils.show_busy_dialog()
		from apis.tmdb_api import tmdb_movie_keywords, tmdb_tv_keywords
		if media_type == 'movie': function, key = tmdb_movie_keywords, 'keywords'
		else: function, key = tmdb_tv_keywords, 'results'
		try: keywords = function(tmdb_id)[key]
		except: keywords = []
		kodi_utils.hide_busy_dialog()
	if not keywords:
		kodi_utils.notification('No Results', 2500)
		return None
	list_items = [{'line1': i['name'], 'icon': poster} for i in keywords]
	kwargs = {'items': json.dumps(list_items)}
	return kodi_utils.select_dialog([i['id'] for i in keywords], **kwargs)

def random_choice(params):
	meta, poster, return_choice = params.get('meta'), params.get('poster'), params.get('return_choice', 'false')
	meta = params.get('meta', None)	
	list_items = [{'line1': 'Single Random Play', 'icon': poster}, {'line1': 'Continual Random Play', 'icon': poster}]
	choices = ['play_random', 'play_random_continual']
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Random Play Type...'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if return_choice == 'true': return choice
	if choice == None: return
	from modules.episode_tools import EpisodeTools
	exec('EpisodeTools(meta).%s()' % choice)

def trakt_manager_choice(params):
	if not settings.trakt_user_active(): return kodi_utils.notification('No Active Trakt Account', 3500)
	tmdb_id, tvdb_id, imdb_id, media_type = params['tmdb_id'], params['tvdb_id'], params['imdb_id'], params['media_type']
	icon = params.get('icon', None) or kodi_utils.get_icon('trakt')
	choices = [('Add to [B]Watchlist[/B]', 'add_watchlist'), ('Remove from [B]Watchlist[/B]', 'remove_watchlist'),
				('Add to [B]Collection[/B]', 'add_collection'), ('Remove from [B]Collection[/B]', 'remove_collection'),
				('Add To [B]Personal List[/B]...', 'add'), ('Remove from [B]Personal List[/B]...', 'remove')]
	list_items = [{'line1': item[0], 'icon': icon} for item in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Trakt Lists Manager'}
	choice = kodi_utils.select_dialog([i[1] for i in choices], **kwargs)
	if choice == None: return
	from apis import trakt_api
	if media_type == 'movie': key, media_key, media_id = ('movies', 'tmdb', int(tmdb_id))
	else:
		key = 'shows'
		media_ids = [(tmdb_id, 'tmdb'), (imdb_id, 'imdb'), (tvdb_id, 'tvdb')]
		media_id, media_key = next(item for item in media_ids if item[0] not in ('None', None, ''))
		if media_id in (tmdb_id, tvdb_id): media_id = int(media_id)
	data = {key: [{'ids': {media_key: media_id}}]}
	if choice == 'add_watchlist': return trakt_api.add_to_watchlist(data)
	if choice == 'remove_watchlist': return trakt_api.remove_from_watchlist(data)
	if choice == 'add_collection': return trakt_api.add_to_collection(data)
	if choice == 'remove_collection': return trakt_api.remove_from_collection(data)
	selected = trakt_api.get_trakt_list_selection(['personal'])
	if selected == None: return
	trakt_api.add_to_list(selected['user'], selected['slug'], data) if choice == 'add' else trakt_api.remove_from_list(selected['user'], selected['slug'], data)

def episode_groups_choice(params):
	from modules.metadata import episode_groups
	episode_group_types = {1: 'Original Air Date', 2: 'Absolute', 3: 'DVD', 4: 'Digital', 5: 'Story Arc', 6: 'Production', 7: 'TV'}
	meta = params.get('meta')
	poster = params.get('poster') or kodi_utils.get_icon('box_office')
	groups = episode_groups(meta['tmdb_id'])
	if not groups:
		kodi_utils.notification('No Episode Groups to choose from.')
		return None
	list_items = [{'line1': '%s | %s Order | %d Groups | %02d Episodes' % (item['name'], episode_group_types[item['type']], item['group_count'], item['episode_count']),
					'line2': item['description'], 'icon': poster} for item in groups]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Episode Groups', 'enable_context_menu': 'true', 'enumerate': 'true', 'multi_line': 'true'}
	choice = kodi_utils.select_dialog([i['id'] for i in groups], **kwargs)
	return choice

def assign_episode_group_choice(params):
	from caches.episode_groups_cache import episode_groups_cache
	from modules import metadata
	tmdb_id = params['meta']['tmdb_id']
	current_group = episode_groups_cache.get(tmdb_id)
	if current_group:
		action = kodi_utils.confirm_dialog(text='Set new Group or Clear Current Group?', ok_label='Set New', cancel_label='Clear', default_control=10)
		if action == None: return
		if not action:
			episode_groups_cache.delete(tmdb_id)
			return kodi_utils.notification('Success', 2000)
	choice = episode_groups_choice(params)
	if choice == None: return
	group_details = metadata.group_details(choice)
	group_data = {'name': group_details['name'], 'id': group_details['id']}
	episode_groups_cache.set(tmdb_id, group_data)
	kodi_utils.notification('Success', 2000)

def playback_choice(params):
	from modules.utils import get_datetime
	from modules.debrid import debrid_for_ext_cache_check
	from modules.source_utils import get_aliases_titles, make_alias_dict
	from modules import metadata
	media_type, season, episode, episode_id = params.get('media_type'), params.get('season', ''), params.get('episode', ''), params.get('episode_id', None)
	playcount = params.get('playcount', '0')
	playback_key = settings.playback_key()
	play_mode = 'playback.%s' % playback_key
	meta = params.get('meta')
	try: meta = json.loads(meta)
	except: pass
	if not isinstance(meta, dict):
		function = metadata.movie_meta if media_type == 'movie' else metadata.tvshow_meta
		meta = function('tmdb_id', meta, settings.tmdb_api_key(), settings.mpaa_region(), get_datetime())
	poster = meta.get('poster') or kodi_utils.get_icon('box_office')
	aliases = get_aliases_titles(make_alias_dict(meta, meta['title']))
	check_cache_status, check_cache_toggle =  ('OFF', 'false') if settings.external_cache_check() else ('ON', 'true')
	items = [{'line': 'Select Source', 'function': 'scrape'},
			{'line': 'Rescrape & Select Source', 'function': 'clear_and_rescrape'}]
	if debrid_for_ext_cache_check():
		items.append({'line': 'Rescrape with External Cache Check [B]%s[/B]' % check_cache_status, 'function': 'rescrape_external_cache_check'})
	items.extend([{'line': 'Clear Debrid Cache & Show Results', 'function': 'clear_debrid_cache_and_show'},
				{'line': 'Scrape with ALL External Scrapers', 'function': 'scrape_with_disabled'},
				{'line': 'Scrape With All Filters Ignored', 'function': 'scrape_with_filters_ignored'}])
	if media_type == 'episode': items.append({'line': 'Scrape with Custom Episode Groups Value', 'function': 'scrape_with_episode_group'})
	if aliases: items.append({'line': 'Scrape with an Alias', 'function': 'scrape_with_aliases'})
	items.append({'line': 'Scrape with Custom Values', 'function': 'scrape_with_custom_values'})
	list_items = [{'line1': i['line'], 'icon': poster} for i in items]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Playback Options'}
	choice = kodi_utils.select_dialog([i['function'] for i in items], **kwargs)
	if choice == None: return kodi_utils.notification('Cancelled', 2500)
	if choice in ('clear_and_rescrape', 'scrape_with_custom_values'):
		kodi_utils.show_busy_dialog()
		from caches.base_cache import clear_cache
		from caches.external_cache import ExternalCache
		clear_cache('internal_scrapers', silent=True)
		ExternalCache().delete_cache_single(media_type, str(meta['tmdb_id']))
		kodi_utils.hide_busy_dialog()
	if choice == 'scrape':
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'], 'autoplay': 'false', 'prescrape': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'],
							'season': season, 'episode': episode, 'autoplay': 'false', 'prescrape': 'false'}
	elif choice == 'clear_and_rescrape':
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'], 'autoplay': 'false', 'prescrape': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'],
							'season': season, 'episode': episode, 'autoplay': 'false', 'prescrape': 'false'}
	elif choice == 'rescrape_external_cache_check':
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'],
												'external_cache_check': check_cache_toggle, 'prescrape': 'false'}
		else:
			play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season, 'episode': episode,
							'external_cache_check': check_cache_toggle, 'prescrape': 'false'}
	elif choice == 'clear_debrid_cache_and_show':
		from caches.debrid_cache import debrid_cache
		debrid_cache.clear_cache()	
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'], 'autoplay': 'false', 'prescrape': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'],
							'season': season, 'episode': episode, 'autoplay': 'false', 'prescrape': 'false'}
	elif choice == 'scrape_with_disabled':
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'],
												'disabled_ext_ignored': 'true', 'prescrape': 'false', 'autoplay': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season,
							'episode': episode, 'disabled_ext_ignored': 'true', 'prescrape': 'false', 'autoplay': 'false'}
	elif choice == 'scrape_with_filters_ignored':
		if media_type == 'movie': play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'],
												'ignore_scrape_filters': 'true', 'prescrape': 'false', 'autoplay': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season,
							'episode': episode, 'ignore_scrape_filters': 'true', 'prescrape': 'false', 'autoplay': 'false'}
		kodi_utils.set_property('fs_filterless_search', 'true')
	elif choice == 'scrape_with_episode_group':
		choice = episode_groups_choice({'meta': meta, 'poster': poster})
		if choice == None: return playback_choice(params)
		episode_details = metadata.group_episode_data(metadata.group_details(choice), episode_id, season, episode)
		if not episode_details:
			kodi_utils.notification('No matching episode')
			return playback_choice(params)
		play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season, 'episode': episode, 'prescrape': 'false',
		'custom_season': episode_details['season'], 'custom_episode': episode_details['episode']}
	elif choice == 'scrape_with_aliases':
		if len(aliases) == 1: custom_title = aliases[0]
		else:
			list_items = [{'line1': i, 'icon': poster} for i in aliases]
			kwargs = {'items': json.dumps(list_items)}
			custom_title = kodi_utils.select_dialog(aliases, **kwargs)
			if custom_title == None: return kodi_utils.notification('Cancelled', 2500)
		custom_title = kodi_utils.kodi_dialog().input('Title', defaultt=custom_title)
		if not custom_title: return kodi_utils.notification('Cancelled', 2500)
		if media_type in ('movie', 'movies'): play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'],
						'custom_title': custom_title, 'prescrape': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season, 'episode': episode,
							'custom_title': custom_title, 'prescrape': 'false'}
	elif choice == 'scrape_with_custom_values':
		default_title, default_year = meta['title'], str(meta['year'])
		if media_type in ('movie', 'movies'): play_params = {'mode': play_mode, 'media_type': 'movie', 'tmdb_id': meta['tmdb_id'], 'prescrape': 'false'}
		else: play_params = {'mode': play_mode, 'media_type': 'episode', 'tmdb_id': meta['tmdb_id'], 'season': season, 'episode': episode, 'prescrape': 'false'}
		if aliases:
			if len(aliases) == 1: alias_title = aliases[0]
			list_items = [{'line1': i, 'icon': poster} for i in aliases]
			kwargs = {'items': json.dumps(list_items)}
			alias_title = kodi_utils.select_dialog(aliases, **kwargs)
			if alias_title: custom_title = kodi_utils.kodi_dialog().input('Title', defaultt=alias_title)
			else: custom_title = kodi_utils.kodi_dialog().input('Title', defaultt=default_title)
		else: custom_title = kodi_utils.kodi_dialog().input('Title', defaultt=default_title)
		if not custom_title: return kodi_utils.notification('Cancelled', 2500)
		def _process_params(default_value, custom_value, param_value):
			if custom_value and custom_value != default_value: play_params[param_value] = custom_value
		_process_params(default_title, custom_title, 'custom_title')
		custom_year = kodi_utils.kodi_dialog().input('Year', type=1, defaultt=default_year)
		_process_params(default_year, custom_year, 'custom_year')
		if media_type == 'episode':
			custom_season = kodi_utils.kodi_dialog().input('Season', type=1, defaultt=season)
			_process_params(season, custom_season, 'custom_season')
			custom_episode = kodi_utils.kodi_dialog().input('Episode', type=1, defaultt=episode)
			_process_params(episode, custom_episode, 'custom_episode')
			if any(i in play_params for i in ('custom_season', 'custom_episode')):
				if settings.autoplay_next_episode(): _process_params('', 'true', 'disable_autoplay_next_episode')
		all_choice = kodi_utils.confirm_dialog(heading=meta.get('rootname', ''), text='Scrape with ALL External Scrapers?', ok_label='Yes', cancel_label='No')
		if all_choice == None: return kodi_utils.notification('Cancelled', 2500)
		if all_choice: _process_params('', 'true', 'disabled_ext_ignored')
		disable_filters_choice = kodi_utils.confirm_dialog(heading=meta.get('rootname', ''), text='Disable All Filters for Search?', ok_label='Yes', cancel_label='No')
		if disable_filters_choice == None: return kodi_utils.notification('Cancelled', 2500)
		if disable_filters_choice:
			_process_params('', 'true', 'ignore_scrape_filters')
			kodi_utils.set_property('fs_filterless_search', 'true')
	else: episodes_data = metadata.episodes_meta(orig_season, meta)
	if media_type == 'episode': play_params['playcount'] = playcount
	play_params[playback_key] = playback_key
	from modules.sources import Sources
	Sources().playback_prep(play_params)

def set_quality_choice(params):
	quality_setting = params.get('setting_id')
	icon = params.get('icon', None) or ''
	dl = ['Include 4K', 'Include 1080p', 'Include 720p', 'Include SD']
	fl = ['4K', '1080p', '720p', 'SD']
	q_setting = get_setting('redlight.%s' % quality_setting).split(', ')
	try: preselect = [fl.index(i) for i in q_setting]
	except: preselect = []
	list_items = [{'line1': item, 'icon': icon} for item in dl]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose the Included Qualities', 'multi_choice': 'true', 'preselect': preselect}
	choice = kodi_utils.select_dialog(fl, **kwargs)
	if choice is None: return
	if choice == []:
		kodi_utils.ok_dialog(text='You must select at least 1 Quality')
		return set_quality_choice(params)
	set_setting(quality_setting, ', '.join(choice))

def extras_buttons_choice(params):
	extras_button_label_values = kodi_utils.extras_button_label_values()
	media_type, button_dict, orig_button_dict = params.get('media_type', None), params.get('button_dict', {}), params.get('orig_button_dict', {})
	if not orig_button_dict:
		for _type in ('movie', 'tvshow'):
			setting_id_base = 'extras.%s.button' % _type
			for item in range(10, 18):
				setting_id = 'extras.%s.button%s' % (_type, item)
				try:
					button_action = get_setting('redlight.%s' % setting_id)
					button_label = extras_button_label_values[_type][button_action]
				except:
					set_setting(setting_id.replace('redlight.', ''), default_setting_values(setting_id)['setting_default'])
					button_action = get_setting('redlight.%s' % setting_id)
					button_label = extras_button_label_values[_type][button_action]
				button_dict[setting_id] = {'button_action': button_action, 'button_label': button_label, 'button_name': 'Button %s' % str(item - 9)}
				orig_button_dict[setting_id] = {'button_action': button_action, 'button_label': button_label, 'button_name': 'Button %s' % str(item - 9)}
	if media_type == None:
		choices = [('Set [B]Movie[/B] Buttons', 'movie'),
					('Set [B]TV Show[/B] Buttons', 'tvshow'),
					('Restore [B]Movie[/B] Buttons to Default', 'restore.movie'),
					('Restore [B]TV Show[/B] Buttons to Default', 'restore.tvshow'),
					('Restore [B]Movie & TV Show[/B] Buttons to Default', 'restore.both')]
		list_items = [{'line1': i[0]} for i in choices]
		kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Media Type to Set Buttons', 'narrow_window': 'true'}
		choice = kodi_utils.select_dialog(choices, **kwargs)
		if choice == None:
			if button_dict != orig_button_dict:
				for k, v in button_dict.items(): set_setting(k, v['button_action'])
			return
		media_type = choice[1]
		if 'restore' in media_type:
			restore_type = media_type.split('.')[1]
			if restore_type in ('movie', 'both'):
				for item in [(i, default_setting_values(i)['setting_default']) for i in ('extras.movie.button%s' % i for i in range(10,18))]:
					set_setting(item[0], item[1])
			if restore_type in ('tvshow', 'both'):
				for item in [(i, default_setting_values(i)['setting_default']) for i in ('extras.tvshow.button%s' % i for i in range(10,18))]:
					set_setting(item[0], item[1])
			return extras_buttons_choice({})
	choices = [('[B]%s[/B]   |   %s' % (v['button_name'], v['button_label']), v['button_name'], v['button_label'], k) for k, v in button_dict.items() if media_type in k]
	list_items = [{'line1': i[0]} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Button to Set', 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return extras_buttons_choice({'button_dict': button_dict, 'orig_button_dict': orig_button_dict})
	button_name, button_label, button_setting = choice[1:]
	choices = [(v, k) for k, v in extras_button_label_values[media_type].items() if not v == button_label]
	choices = [i for i in choices if not i[0] == button_label]
	list_items = [{'line1': i[0]} for i in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Action For %s' % button_name, 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice == None: return extras_buttons_choice({'button_dict': button_dict, 'orig_button_dict': orig_button_dict, 'media_type': media_type})
	button_label, button_action = choice
	button_dict[button_setting] = {'button_action': button_action, 'button_label': button_label, 'button_name': button_name}
	return extras_buttons_choice({'button_dict': button_dict, 'orig_button_dict': orig_button_dict, 'media_type': media_type})

def extras_ratings_choice(params={}):
	choices = [('Metacritic', 'Meta', 'metacritic.png'), ('Tomato Rating Critic', 'Tom/Critic', 'rtcertified.png'),
				('Tomato Rating User', 'Tom/User', 'popcorn.png'), ('IMDb', 'IMDb', 'imdb.png'), ('TMDb', 'TMDb', 'tmdb.png')]
	list_items = [{'line1': i[0], 'icon': 'redlight_flags/ratings/%s' % i[2]} for i in choices]
	current_settings = settings.extras_enabled_ratings()
	try: preselect = [choices.index(i) for i in choices if i[1] in current_settings]
	except: preselect = []
	kwargs = {'items': json.dumps(list_items), 'heading': 'Ratings to Display', 'multi_choice': 'true', 'preselect': preselect}
	selection = kodi_utils.select_dialog(choices, **kwargs)
	if selection == None: return
	if selection == []:
		kodi_utils.ok_dialog(text='You must select at least 1 Ratings Provider')
		return extras_ratings_choice()
	set_setting('extras.enabled_ratings', ', '.join([i[1] for i in selection]))

def set_language_filter_choice(params):
	from modules.meta_lists import language_choices
	filter_setting_id, multi_choice, include_none = params.get('filter_setting_id'), params.get('multi_choice', 'false'), params.get('include_none', 'false')
	lang_choices = language_choices()
	if include_none == 'false': lang_choices.pop('None')
	dl, fl = list(lang_choices.keys()), list(lang_choices.values())
	set_filter = get_setting('redlight.%s' % filter_setting_id).split(', ')
	try: preselect = [fl.index(i) for i in set_filter]
	except: preselect = []
	list_items = [{'line1': item} for item in dl]
	kwargs = {'items': json.dumps(list_items), 'multi_choice': multi_choice, 'preselect': preselect}
	choice = kodi_utils.select_dialog(fl, **kwargs)
	if choice == None: return
	if multi_choice == 'true':
		if choice == []: set_setting(filter_setting_id, 'eng')
		else: set_setting(filter_setting_id, ', '.join(choice))
	else: set_setting(filter_setting_id, choice)

def enable_scrapers_choice(params={}):
	icon = params.get('icon', None) or kodi_utils.get_icon('redlight')
	scrapers = ['external', 'easynews', 'rd_cloud', 'pm_cloud', 'ad_cloud', 'tb_cloud', 'folders']
	cloud_scrapers = {'rd_cloud': 'rd.enabled', 'pm_cloud': 'pm.enabled', 'ad_cloud': 'ad.enabled', 'tb_cloud': 'tb.enabled'}
	scraper_names = ['EXTERNAL SCRAPERS', 'EASYNEWS', 'RD CLOUD', 'PM CLOUD', 'AD CLOUD', 'TB CLOUD', 'FOLDERS 1-5']
	set_scrapers = settings.active_internal_scrapers()
	preselect = [scrapers.index(i) for i in set_scrapers]
	list_items = [{'line1': item, 'icon': icon} for item in scraper_names]
	kwargs = {'items': json.dumps(list_items), 'multi_choice': 'true', 'preselect': preselect}
	choice = kodi_utils.select_dialog(scrapers, **kwargs)
	if choice is None: return
	for i in scrapers:
		set_setting('provider.%s' % i, ('true' if i in choice else 'false'))
		if i in cloud_scrapers and i in choice: set_setting(cloud_scrapers[i], 'true')

def sources_folders_choice(params):
	from windows.base_window import open_window
	return open_window(('windows.settings_manager', 'SettingsManagerFolders'), 'settings_manager_folders.xml')

def results_sorting_choice(params):
	choices = [('Quality, Provider, Size', '0'), ('Quality, Size, Provider', '1'),
				('Provider, Quality, Size', '2'), ('Provider, Size, Quality', '3'),
				('Size, Quality, Provider', '4'), ('Size, Provider, Quality', '5')]
	list_items = [{'line1': item[0]} for item in choices]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice is None: return
	set_setting('results.sort_order_display', choice[0])
	set_setting('results.sort_order', choice[1])

def results_format_choice(params):
	choices = [('List', kodi_utils.get_icon('results_list', 'results')), ('Rows', kodi_utils.get_icon('results_row', 'results')),
				('WideList', kodi_utils.get_icon('results_widelist', 'results'))]
	list_items = [{'line1': item[0], 'icon': item[1]} for item in choices]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Choose Results Format'}
	choice = kodi_utils.select_dialog(choices, **kwargs)
	if choice is None: return
	set_setting('results.list_format', choice[0])

def clear_favorites_choice(params):
	fl = [('Clear Movies Favorites', 'movie'), ('Clear TV Show Favorites', 'tvshow'), ('Clear People Favorites', 'people')]
	list_items = [{'line1': item[0]} for item in fl]
	kwargs = {'items': json.dumps(list_items), 'narrow_window': 'true'}
	media_type = kodi_utils.select_dialog([item[1] for item in fl], **kwargs)
	if media_type == None: return
	if not kodi_utils.confirm_dialog(): return
	from caches.favorites_cache import favorites_cache
	favorites_cache.clear_favorites(media_type)
	kodi_utils.notification('Success', 3000)

def scraper_color_choice(params):
	setting = params.get('setting_id')
	current_setting, original_highlight = get_setting('redlight.%s' % setting), default_setting_values(setting)['setting_default']
	if current_setting != original_highlight:
		action = kodi_utils.confirm_dialog(text='Set new Highlight or Restore Default Highlight?', ok_label='Set New', cancel_label='Restore Default', default_control=10)
		if action == None: return
		if not action: return set_setting(setting, original_highlight)
	chosen_color = color_choice({'current_setting': current_setting})
	if chosen_color: set_setting(setting, chosen_color)

def personal_list_unseen_color_choice(params):
	setting = 'personal_list.unseen_highlight'
	current_setting, original_highlight = get_setting('redlight.%s' % setting), default_setting_values(setting)['setting_default']
	if current_setting != original_highlight:
		action = kodi_utils.confirm_dialog(text='Set new Highlight or Restore Default Highlight?', ok_label='Set New', cancel_label='Restore Default', default_control=10)
		if action == None: return
		if not action: return set_setting(setting, original_highlight)
	chosen_color = color_choice({'current_setting': current_setting})
	if chosen_color: set_setting(setting, chosen_color)

def color_choice(params):
	from windows.base_window import open_window
	return open_window(('windows.color', 'SelectColor'), 'color.xml', current_setting=params.get('current_setting', None))

def mpaa_region_choice(params={}):
	from modules.meta_lists import regions as rg
	regions = rg()
	regions.sort(key=lambda x: x['name'])
	list_items = [{'line1': i['name']} for i in regions]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Set MPAA Region', 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(regions, **kwargs)
	if choice == None: return None
	from caches.meta_cache import delete_meta_cache
	set_setting('mpaa_region', choice['id'])
	set_setting('mpaa_region_display_name', choice['name'])
	delete_meta_cache(silent=True)

def lists_cache_duration_choice(params={}):
	durations = [{'name': '6 hours', 'duration': '6'}, {'name': '12 hours', 'duration': '12'}, {'name': '18 hours', 'duration': '18'}, {'name': '1 Day', 'duration': '24'},
				{'name': '2 Days', 'duration': '48'}, {'name': '3 Days', 'duration': '72'}, {'name': '4 Days', 'duration': '96'}, {'name': '5 Days', 'duration': '120'},
				{'name': '6 Days', 'duration': '144'}, {'name': '7 Days', 'duration': '168'}]
	list_items = [{'line1': i['name']} for i in durations]
	kwargs = {'items': json.dumps(list_items), 'heading': 'Set Generic List Cache Duration', 'narrow_window': 'true'}
	choice = kodi_utils.select_dialog(durations, **kwargs)
	if choice == None: return None
	set_setting('lists_cache_duraton', choice['duration'])
	set_setting('lists_cache_duraton_display_name', choice['name'])

def options_menu_choice(params, meta=None):
	from caches.episode_groups_cache import episode_groups_cache
	from modules.utils import get_datetime
	from modules import metadata
	params_get = params.get
	tmdb_id, content, poster = params_get('tmdb_id', None), params_get('content', None), params_get('poster', None)
	is_external, from_extras = params_get('is_external') in (True, 'True', 'true'), params_get('from_extras', 'false') == 'true'
	season, episode = params_get('season', ''), params_get('episode', '')
	single_ep_list = ('episode.progress', 'episode.recently_watched', 'episode.next_trakt', 'episode.next_redlight', 'episode.trakt_recently_aired', 'episode.trakt_calendar')
	if not content: content = kodi_utils.container_content()[:-1]
	menu_type = content
	if content.startswith('episode.'): content = 'episode'
	if not meta:
		function = metadata.movie_meta if content == 'movie' else metadata.tvshow_meta
		meta = function('tmdb_id', tmdb_id, settings.tmdb_api_key(), settings.mpaa_region(), get_datetime())
	meta_get = meta.get
	rootname, title, imdb_id, tvdb_id = meta_get('rootname', None), meta_get('title'), meta_get('imdb_id', None), meta_get('tvdb_id', None)
	window_function = kodi_utils.activate_window if is_external else kodi_utils.container_update
	listing = []
	listing_append = listing.append
	if from_extras:
		if menu_type in ('movie', 'episode'): listing_append(('Playback Options', 'Scrapers Options', 'playback_choice'))
		if settings.trakt_user_active(): listing_append(('Trakt Lists Manager', '', 'trakt_manager'))
		listing_append(('Personal Lists Manager', '', 'personallists_manager_choice'))
		listing_append(('TMDb Lists Manager', '', 'tmdblists_manager_choice'))
		listing_append(('Favorites Manager', '', 'favorites_manager_choice'))
	if menu_type == 'tvshow': listing_append(('Play Random', 'Based On %s' % rootname, 'random'))
	if menu_type in ('tvshow', 'season'):
		listing_append(('Assign an Episode Group to %s' % rootname, 'Currently %s' % episode_groups_cache.get(tmdb_id).get('name', 'None'), 'episode_group'))
	if menu_type in ('movie', 'episode') or menu_type in single_ep_list:
		base_str1, base_str2, on_str, off_str = '%s%s', 'Currently: [B]%s[/B]', 'On', 'Off'
		if settings.auto_play(content): autoplay_status, autoplay_toggle, quality_setting = on_str, 'false', 'autoplay_quality_%s' % content
		else: autoplay_status, autoplay_toggle, quality_setting = off_str, 'true', 'results_quality_%s' % content
		set_active = settings.active_internal_scrapers()
		active_int_scrapers = [i.replace('_', '') for i in set_active]
		current_scrapers_status = ', '.join([i for i in active_int_scrapers]) if len(active_int_scrapers) > 0 else 'N/A'
		current_quality_status =  ', '.join(settings.quality_filter(quality_setting))
		autoplay_next_status, autoplay_next_toggle = (on_str, 'false') if settings.autoplay_next_episode() else (off_str, 'true')
		listing_append((base_str1 % ('Auto Play', ' (%s)' % content), base_str2 % autoplay_status, 'toggle_autoplay'))
		if menu_type == 'episode' or menu_type in single_ep_list:
			if autoplay_status == on_str:
				autoplay_next_status, autoplay_next_toggle = (on_str, 'false') if settings.autoplay_next_episode() else (off_str, 'true')
				listing_append((base_str1 % ('Autoplay Next Episode', ''), base_str2 % autoplay_next_status, 'toggle_autoplay_next'))
			else:
				autoscrape_next_status, autoscrape_next_toggle = (on_str, 'false') if settings.autoscrape_next_episode() else (off_str, 'true')
				listing_append((base_str1 % ('Autoscrape Next Episode', ''), base_str2 % autoscrape_next_status, 'toggle_autoscrape_next'))
		listing_append((base_str1 % ('Quality Limit', ' (%s)' % content), base_str2 % current_quality_status, 'set_quality'))
		listing_append((base_str1 % ('', 'Enable Scrapers'), base_str2 % current_scrapers_status, 'enable_scrapers'))
		if menu_type == 'episode' or menu_type in single_ep_list:
			listing_append(('Assign an Episode Group to %s' % rootname, base_str2 % episode_groups_cache.get(tmdb_id).get('name', 'None'), 'episode_group'))
	if not from_extras:
		if menu_type in ('movie', 'tvshow'):
			listing_append(('Re-Cache %s Info' % ('Movies' if menu_type == 'movie' else 'TV Shows'), 'Clear %s Cache' % rootname, 'clear_media_cache'))
		if menu_type in ('movie', 'episode') or menu_type in single_ep_list: listing_append(('Clear Scrapers Cache', '', 'clear_scrapers_cache'))
		if menu_type in ('tvshow', 'season', 'episode'): listing_append(('TV Shows Progress Manager', '', 'nextep_manager'))
		listing_append(('Open Download Manager', '', 'open_download_manager'))
		listing_append(('Open Tools', '', 'open_tools'))
		if menu_type in ('movie', 'episode') or menu_type in single_ep_list: listing_append(('Open External Scraper Settings', '', 'open_external_scraper_settings'))
		listing_append(('Open Settings', '', 'open_settings'))
	list_items = [{'line1': item[0], 'line2': item[1] or item[0], 'icon': poster} for item in listing]
	heading = rootname or 'Options...'
	kwargs = {'items': json.dumps(list_items), 'heading': heading, 'multi_line': 'true'}
	choice = kodi_utils.select_dialog([i[2] for i in listing], **kwargs)
	if choice == None: return
	if choice == 'clear_media_cache':
		from caches.base_cache import refresh_cached_data
		kodi_utils.close_all_dialog()
		return refresh_cached_data(meta)
	if choice == 'clear_scrapers_cache':
		from modules.source_utils import clear_scrapers_cache
		return clear_scrapers_cache()
	if choice == 'open_download_manager':
		from modules.downloader import manager
		kodi_utils.close_all_dialog()
		return manager()
	if choice == 'open_tools':
		kodi_utils.close_all_dialog()
		return window_function({'mode': 'navigator.tools'})
	if choice == 'open_settings':
		kodi_utils.close_all_dialog()
		return kodi_utils.open_settings()
	if choice == 'open_external_scraper_settings':
		kodi_utils.close_all_dialog()
		return kodi_utils.external_scraper_settings()
	if choice == 'playback_choice':
		return playback_choice({'media_type': content, 'poster': poster, 'meta': meta, 'season': season, 'episode': episode})
	if choice == 'nextep_manager':
		return window_function({'mode': 'build_next_episode_manager'})
	if choice == 'random':
		kodi_utils.close_all_dialog()
		return random_choice({'meta': meta, 'poster': poster})
	if choice == 'trakt_manager':
		return trakt_manager_choice({'tmdb_id': tmdb_id, 'imdb_id': imdb_id, 'tvdb_id': tvdb_id or 'None', 'media_type': content, 'icon': poster})
	if choice == 'personallists_manager_choice':
		from modules.utils import get_current_timestamp
		return personallists_manager_choice({'list_type': content, 'tmdb_id': tmdb_id, 'title': title,
							'premiered': meta_get('premiered'), 'current_time': get_current_timestamp(), 'icon': poster})
	if choice == 'favorites_manager_choice':
		return favorites_manager_choice({'media_type': content if content in ('movie', 'tvshow') else 'tvshow', 'tmdb_id': tmdb_id, 'title': title})
	if choice == 'tmdblists_manager_choice':
		return tmdblists_manager_choice({'media_type': content if content in ('movie', 'movies') else 'tv', 'tmdb_id': tmdb_id, 'icon': poster})
	if choice == 'toggle_autoplay':
		set_setting('auto_play_%s' % content, autoplay_toggle)
	elif choice == 'toggle_autoplay_next':
		set_setting('autoplay_next_episode', autoplay_next_toggle)
	elif choice == 'toggle_autoscrape_next':
		set_setting('autoscrape_next_episode', autoscrape_next_toggle)
	elif choice == 'set_quality':
		set_quality_choice({'setting_id': 'autoplay_quality_%s' % content if autoplay_status == on_str else 'results_quality_%s' % content, 'icon': poster})
	elif choice == 'enable_scrapers':
		enable_scrapers_choice({'icon': poster})
	elif choice == 'episode_group':
		assign_episode_group_choice({'meta': meta, 'poster': poster})
	options_menu_choice(params, meta=meta)

def extras_menu_choice(params):
	from windows.base_window import open_window
	from modules.utils import get_datetime
	from modules import metadata
	stacked = params.get('stacked', 'false') == 'true'
	if not stacked: kodi_utils.show_busy_dialog()
	media_type = params['media_type']
	function = metadata.movie_meta if media_type == 'movie' else metadata.tvshow_meta
	meta = function('tmdb_id', params['tmdb_id'], settings.tmdb_api_key(), settings.mpaa_region(), get_datetime())
	if not stacked: kodi_utils.hide_busy_dialog()
	open_window(('windows.extras', 'Extras'), 'extras.xml', meta=meta, is_external=params.get('is_external', 'true' if kodi_utils.external() else 'false'),
															options_media_type=media_type, starting_position=params.get('starting_position', None))

def open_movieset_choice(params):
	kodi_utils.hide_busy_dialog()
	window_function = kodi_utils.activate_window if params['is_external'] in (True, 'True', 'true') else kodi_utils.container_update
	return window_function({'mode': 'build_movie_list', 'action': 'tmdb_movies_sets', 'key_id': params['key_id'], 'name': params['name']})

def media_extra_info_choice(params):
	from modules.utils import adjust_premiered_date
	from modules.source_utils import get_aliases_titles, make_alias_dict
	media_type, meta = params.get('media_type'), params.get('meta')
	extra_info, listings = meta.get('extra_info', None), []
	append = listings.append
	try:
		if media_type == 'movie':
			if meta['tagline']: append('[B]Tagline:[/B] %s' % meta['tagline'])
			aliases = get_aliases_titles(make_alias_dict(meta, meta['title']))
			if aliases: append('[B]Aliases:[/B] %s' % ', '.join(aliases))
			append('[B]Status:[/B] %s' % extra_info['status'])
			append('[B]Premiered:[/B] %s' % meta['premiered'])
			append('[B]Rating:[/B] %s (%s Votes)' % (str(round(meta['rating'], 1)), meta['votes']))
			append('[B]Runtime:[/B] %s mins' % int(float(meta['duration'])/60))
			append('[B]Genre/s:[/B] %s' % ', '.join(meta['genre']))
			append('[B]Budget:[/B] %s' % extra_info['budget'])
			append('[B]Revenue:[/B] %s' % extra_info['revenue'])
			append('[B]Director:[/B] %s' % ', '.join(meta['director']))
			append('[B]Writer/s:[/B] %s' % ', '.join(meta['writer']) or 'N/A')
			append('[B]Studio:[/B] %s' % ', '.join(meta['studio']) or 'N/A')
			if extra_info['collection_name']: append('[B]Collection:[/B] %s' % extra_info['collection_name'])
			append('[B]Homepage:[/B] %s' % extra_info['homepage'])
		else:
			append('[B]Type:[/B] %s' % extra_info['type'])
			if meta['tagline']: append('[B]Tagline:[/B] %s' % meta['tagline'])
			aliases = get_aliases_titles(make_alias_dict(meta, meta['title']))
			if aliases: append('[B]Aliases:[/B] %s' % ', '.join(aliases))
			append('[B]Status:[/B] %s' % extra_info['status'])
			append('[B]Premiered:[/B] %s' % meta['premiered'])
			append('[B]Rating:[/B] %s (%s Votes)' % (str(round(meta['rating'], 1)), meta['votes']))
			append('[B]Runtime:[/B] %d mins' % int(float(meta['duration'])/60))
			append('[B]Classification:[/B] %s' % meta['mpaa'])
			append('[B]Genre/s:[/B] %s' % ', '.join(meta['genre']))
			append('[B]Networks:[/B] %s' % ', '.join(meta['studio']))
			append('[B]Created By:[/B] %s' % extra_info['created_by'])
			try:
				last_ep = extra_info['last_episode_to_air']
				append('[B]Last Aired:[/B] %s - [B]S%.2dE%.2d[/B] - %s' \
					% (adjust_premiered_date(last_ep['air_date'], settings.date_offset())[0].strftime('%d %B %Y'),
						last_ep['season_number'], last_ep['episode_number'], last_ep['name']))
			except: pass
			try:
				next_ep = extra_info['next_episode_to_air']
				append('[B]Next Aired:[/B] %s - [B]S%.2dE%.2d[/B] - %s' \
					% (adjust_premiered_date(next_ep['air_date'], settings.date_offset())[0].strftime('%d %B %Y'),
						next_ep['season_number'], next_ep['episode_number'], next_ep['name']))
			except: pass
			append('[B]Seasons:[/B] %s' % meta['total_seasons'])
			append('[B]Episodes:[/B] %s' % meta['total_aired_eps'])
			append('[B]Homepage:[/B] %s' % extra_info['homepage'])
	except: return kodi_utils.notification('Error', 2000)
	return '[CR][CR]'.join(listings)

def discover_choice(params):
	from windows.base_window import open_window
	open_window(('windows.discover', 'Discover'), 'discover.xml', media_type=params['media_type'])
