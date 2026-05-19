# -*- coding: utf-8 -*-
import json
from windows.base_window import BaseDialog
from caches.settings_cache import set_setting
from modules.debrid import debrid_for_ext_cache_check
from modules.utils import TaskPool
from modules.source_utils import source_filters
from modules.settings import provider_sort_ranks, avoid_episode_spoilers, max_threads
from modules.kodi_utils import get_icon, kodi_dialog, hide_busy_dialog, addon_fanart, select_dialog, ok_dialog, notification
# from modules.kodi_utils import logger

class SourcesResults(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, *args)
		self.window_format = kwargs.get('window_format', 'list')
		self.window_id = kwargs.get('window_id', 2000)
		self.filter_window_id = 2100
		self.results = kwargs.get('results')
		self.uncached_results = kwargs.get('uncached_results', [])
		self.info_highlights_dict = kwargs.get('scraper_settings')
		self.episode_group_label = kwargs.get('episode_group_label', '')
		self.prescrape = kwargs.get('prescrape')
		self.meta = kwargs.get('meta')
		self.filters_ignored = kwargs.get('filters_ignored', False)
		self.meta_get = self.meta.get
		self.make_poster = self.window_format in ('list', 'medialist')
		self.empty_poster = get_icon('box_office')
		self.addon_fanart = addon_fanart()
		self.poster = self.meta_get('poster') or self.empty_poster
		self.external_cache_check = kwargs.get('external_cache_check')
		self.prerelease_values, self.prerelease_key = ('CAM', 'SCR', 'TELE'), 'CAM/SCR/TELE'
		self.info_icons_dict = {'easynews': get_icon('easynews'), 'alldebrid': get_icon('alldebrid'), 'real-debrid': get_icon('realdebrid'),
		'premiumize': get_icon('premiumize'), 'torbox': get_icon('torbox'), 'ad_cloud': get_icon('alldebrid'), 'rd_cloud': get_icon('realdebrid'),
		'pm_cloud': get_icon('premiumize'), 'tb_cloud': get_icon('torbox')}
		self.info_quality_dict = {'4k': get_icon('flag_4k', 'flags'), '1080p': get_icon('flag_1080p', 'flags'), '720p': get_icon('flag_720p', 'flags'),
		'sd': get_icon('flag_sd', 'flags'), 'cam': get_icon('flag_sd', 'flags'), 'tele': get_icon('flag_sd', 'flags'), 'scr': get_icon('flag_sd', 'flags')}
		self.make_items()
		self.make_filter_items()
		self.set_properties()

	def onInit(self):
		self.filter_applied = False
		if self.make_poster: self.set_poster()
		self.add_items(self.window_id, self.item_list)
		self.add_items(self.filter_window_id, self.filter_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		self.clearProperties()
		self.clear_home_property('window_theme.sources')
		hide_busy_dialog()
		return self.selected

	def get_provider_and_path(self, provider):
		try: return provider, self.info_icons_dict[provider]
		except: return 'folders', get_icon('folder')

	def get_quality_and_path(self, quality):
		try: return quality, self.info_quality_dict[quality]
		except: return 'sd', get_icon('flag_sd')

	def filter_action(self, action):
		if action == self.right_action or action in self.closing_actions:
			self.select_item(self.filter_window_id, 0)
			self.setFocusId(self.window_id)
		if action in self.selection_actions:
			chosen_listitem = self.get_listitem(self.filter_window_id)
			filter_type, filter_value = chosen_listitem.getProperty('filter_type'), chosen_listitem.getProperty('filter_value')
			if filter_type in ('quality', 'provider'):
				if filter_value == self.prerelease_key: filtered_list = [i for i in self.item_list if i.getProperty(filter_type) in self.prerelease_values]
				else: filtered_list = [i for i in self.item_list if i.getProperty(filter_type) == filter_value]
			elif filter_type == 'special':
				if filter_value == 'title':
					keywords = kodi_dialog().input('Enter Keyword (Comma Separated for Multiple)')
					if not keywords: return
					keywords.replace(' ', '')
					keywords = keywords.split(',')
					choice = [i.upper() for i in keywords]
					filtered_list = [i for i in self.item_list if all(x in i.getProperty('name') for x in choice)]
				elif filter_value == 'extraInfo':
					filters = source_filters()
					list_items = [{'line1': item[0], 'icon': self.poster} for item in filters]
					kwargs = {'items': json.dumps(list_items), 'heading': 'Filter Results', 'multi_choice': 'true'}
					choice = select_dialog(filters, **kwargs)
					if choice == None: return
					choice = [i[1] for i in choice]
					filtered_list = [i for i in self.item_list if all(x in i.getProperty('extraInfo') for x in choice)]
				elif filter_value == 'showuncached': filtered_list = self.make_items(self.uncached_results)
				else: #cache_check_rescrape
					self.selected = ('cache_change_rescrape', 'false' if self.external_cache_check else 'true')
					return self.close()
			if not filtered_list: return ok_dialog(text='No Results')
			self.set_filter(filtered_list)

	def onAction(self, action):
		if self.get_visibility('Control.HasFocus(%s)' % self.filter_window_id): return self.filter_action(action)
		chosen_listitem = self.get_listitem(self.window_id)
		if action in self.closing_actions:
			if self.filter_applied: return self.clear_filter()
			self.selected = (None, '')
			return self.close()
		if action == self.info_action:
			self.open_window(('windows.sources', 'SourcesInfo'), 'sources_info.xml', item=chosen_listitem)
		elif action in self.selection_actions:
			if self.prescrape and chosen_listitem.getProperty('perform_full_search') == 'true':
				self.selected = ('perform_full_search', '')
				return self.close()
			chosen_source = json.loads(chosen_listitem.getProperty('source'))
			if 'Uncached' in chosen_source.get('cache_provider', ''):
				from modules.debrid import manual_add_magnet_to_cloud
				return manual_add_magnet_to_cloud({'mode': 'manual_add_magnet_to_cloud', 'provider': chosen_source['debrid'], 'magnet_url': chosen_source['url']})
			self.selected = ('play', chosen_source)
			return self.close()
		elif action in self.context_actions:
			source = json.loads(chosen_listitem.getProperty('source'))
			choice = self.context_menu(source)
			if choice:
				if isinstance(choice, dict): return self.execute_code('RunPlugin(%s)' % self.build_url(choice))
				if choice == 'results_info': return self.open_window(('windows.sources', 'SourcesInfo'), 'sources_info.xml', item=chosen_listitem)
				if choice == 'rd_cloud_delete':
					from apis.real_debrid_api import RealDebridAPI
					rd_api = RealDebridAPI()
					function = rd_api.delete_torrent if source['cache_type'] == 'torrent' else rd_api.delete_download
					result = function(source['folder_id'])
					if result.status_code in (401, 403, 404): return notification('Error', 1200)
					rd_api.clear_cache()
					self.delete_single_source(source)

	def delete_single_source(self, single_source):
		self.results.remove(single_source)
		self.make_items()
		self.total_results = str(len(self.item_list))
		self.reset_window(self.window_id)
		self.add_items(self.window_id, self.item_list)
		self.setFocusId(self.window_id)
		self.set_properties()

	def make_items(self, filtered_list=None):
		def builder(count, item):
			try:
				get = item.get
				listitem = self.make_listitem()
				set_properties = listitem.setProperties
				scrape_provider, source, quality, name = get('scrape_provider'), get('source'), get('quality', 'SD'), get('display_name')
				basic_quality, quality_icon = self.get_quality_and_path(quality.lower())
				pack = get('package', 'false') in ('true', 'show', 'season')
				extraInfo = get('extraInfo', '')
				extraInfo = extraInfo.rstrip('| ')
				if pack: extraInfo = '[B]%s PACK[/B] | %s' % (get('package'), extraInfo)
				if self.episode_group_label: extraInfo = '%s | %s' % (self.episode_group_label, extraInfo)
				if not extraInfo: extraInfo = 'N/A'
				if scrape_provider == 'external':
					source_site = get('provider').upper()
					provider = get('debrid', source_site).replace('.me', '').upper()
					provider_lower = provider.lower()
					provider_icon = self.get_provider_and_path(provider_lower)[1]
					if 'Uncached' in item['cache_provider']:
						if 'seeders' in item: set_properties({'source_type': 'UNCACHED (%d SEEDERS)' % get('seeders', 0)})
						else: set_properties({'source_type': 'UNCACHED'})
						set_properties({'highlight': 'FF7C7C7C'})
					else:
						if provider in ('REAL-DEBRID', 'ALLDEBRID'):
							if self.external_cache_check: cache_flag = '[B]CACHED[/B]'
							else: cache_flag = 'UNCHECKED'
						else: cache_flag = '[B]CACHED[/B]'
						if highlight_type == 0: key = provider_lower
						else: key = basic_quality
						set_properties({'highlight': self.info_highlights_dict[key]})
						if pack: set_properties({'source_type': '%s [B]PACK[/B]' % cache_flag})
						else: set_properties({'source_type': '%s' % cache_flag})
					set_properties({'provider': provider})
				else:
					source_site = source.upper()
					provider, provider_icon = self.get_provider_and_path(source.lower())
					if highlight_type == 0: key = provider
					else: key = basic_quality
					set_properties({'highlight': self.info_highlights_dict[key], 'source_type': 'DIRECT', 'provider': provider.upper()})
				set_properties({'name': name.upper(), 'source_site': source_site, 'provider_icon': provider_icon, 'quality_icon': quality_icon, 'count': '%02d.' % count,
						'size_label': get('size_label', 'N/A'), 'extraInfo': extraInfo, 'quality': quality.upper(), 'hash': get('hash', 'N/A'), 'source': json.dumps(item)})	
				item_list.append((listitem, count))
			except: pass
		try:
			item_list = []
			highlight_type = self.info_highlights_dict['highlight_type']
			if filtered_list:
				threads = TaskPool().tasks_enumerate(builder, filtered_list, min(len(filtered_list), max_threads()))
				[i.join() for i in threads]
				item_list.sort(key=lambda k: k[1])
				item_list = [i[0] for i in item_list]
				return item_list
			threads = TaskPool().tasks_enumerate(builder, self.results, min(len(self.results), max_threads()))
			[i.join() for i in threads]
			item_list.sort(key=lambda k: k[1])
			self.item_list = [i[0] for i in item_list]
			if self.prescrape:
				prescrape_listitem = self.make_listitem()
				prescrape_listitem.setProperty('perform_full_search', 'true')
			self.total_results = str(len(self.item_list))
			if self.prescrape: self.item_list.append(prescrape_listitem)
		except: pass

	def make_filter_items(self):
		def builder(count, item):
			listitem = self.make_listitem()
			listitem.setProperties({'label': item[0], 'filter_type': item[1], 'filter_value': item[2]})
			self.filter_list.append((listitem, count))
		duplicates = set()
		qualities = [i.getProperty('quality') for i in self.item_list \
							if not (i.getProperty('quality') in duplicates or duplicates.add(i.getProperty('quality'))) \
							and not i.getProperty('quality') == '']
		if any(i in self.prerelease_values for i in qualities): qualities = [i for i in qualities if not i in self.prerelease_values] + [self.prerelease_key]
		qualities.sort(key=('4K', '1080P', '720P', 'SD', 'CAM/SCR/TELE').index)
		quality_totals = {i: len([x for x in self.item_list if x.getProperty('quality') == i]) for i in qualities}
		if 'CAM/SCR/TELE' in qualities: quality_totals['CAM/SCR/TELE'] = len([i for i in self.item_list if i.getProperty('quality') in self.prerelease_values])
		duplicates = set()
		providers = [i.getProperty('provider') for i in self.item_list \
							if not (i.getProperty('provider') in duplicates or duplicates.add(i.getProperty('provider'))) \
							and not i.getProperty('provider') == '']
		provider_totals = {i: len([x for x in self.item_list if x.getProperty('provider') == i]) for i in providers}
		sort_ranks = provider_sort_ranks()
		cache_functions_debrid = debrid_for_ext_cache_check()
		sort_ranks['premiumize'] = sort_ranks.pop('premiumize.me')
		provider_choices = sorted(sort_ranks.keys(), key=sort_ranks.get)
		provider_choices = [i.upper() for i in provider_choices]
		providers.sort(key=provider_choices.index)
		qualities = [('Show [B]%s[/B] Only | [B]%d[/B] Results' % (i, quality_totals[i]), 'quality', i) for i in qualities]
		providers = [('Show [B]%s[/B] Only | [B]%d[/B] Results' % (i, provider_totals[i]), 'provider', i) for i in providers]
		data = []
		if cache_functions_debrid: data.append(('Rescrape with External Cache Check [B]%s[/B]' % ('OFF' if self.external_cache_check else 'ON'), 'special', 'cache_check_rescrape'))
		if self.uncached_results: data.append(('Show [B]Uncached[/B] Only | [B]%d[/B] Results' % len(self.uncached_results), 'special', 'showuncached'))
		data.extend(qualities)
		data.extend(providers)
		data.extend([('Filter by [B]Title[/B]...', 'special', 'title'), ('Filter by [B]Info[/B]...', 'special', 'extraInfo')])
		self.filter_list = []
		threads = TaskPool().tasks_enumerate(builder, data, min(len(data), max_threads()))
		[i.join() for i in threads]
		self.filter_list.sort(key=lambda k: k[1])
		self.filter_list = [i[0] for i in self.filter_list]

	def set_properties(self):
		self.set_home_property('window_theme.sources', self.get_home_property('window_theme'))
		self.setProperty('window_format', self.window_format)
		self.setProperty('fanart', self.meta_get('fanart') or self.addon_fanart)
		self.setProperty('clearlogo', self.meta_get('clearlogo') or '')
		self.setProperty('title', self.meta_get('title'))
		self.setProperty('total_results', self.total_results)
		self.setProperty('filters_ignored', '| Filters Ignored' if self.filters_ignored else '')

	def set_poster(self):
		if self.window_id == 2000: self.set_image(200, self.poster)

	def context_menu(self, item):
		down_file_params, down_pack_params, browse_pack_params, add_magnet_to_cloud_params, uncached_download = None, None, None, None, None
		item_get = item.get
		item_id, name, magnet_url, info_hash = item_get('id', None), item_get('name'), item_get('url', 'None'), item_get('hash', 'None')
		provider_source, scrape_provider, cache_provider = item_get('source'), item_get('scrape_provider'), item_get('cache_provider', 'None')
		uncached = 'Uncached' in cache_provider
		source, meta_json = json.dumps(item), json.dumps(self.meta)
		choices = []
		choices_append = choices.append
		if not uncached and scrape_provider != 'folders':
			down_file_params = {'mode': 'downloader.runner', 'action': 'meta.single', 'name': self.meta.get('rootname', ''), 'source': source,
								'url': None, 'provider': scrape_provider, 'meta': meta_json}
		if 'package' in item and not uncached:
			down_pack_params = {'mode': 'downloader.runner', 'action': 'meta.pack', 'name': self.meta.get('rootname', ''), 'source': source, 'url': None,
								'provider': cache_provider, 'meta': meta_json, 'magnet_url': magnet_url, 'info_hash': info_hash}
		if provider_source == 'torrent':
			browse_pack_params = {'mode': 'debrid.browse_packs', 'provider': cache_provider, 'name': name,
								'magnet_url': magnet_url, 'info_hash': info_hash}
			add_magnet_to_cloud_params = {'mode': 'manual_add_magnet_to_cloud', 'provider': cache_provider, 'magnet_url': magnet_url}
		choices_append(('Info', 'results_info'))
		if add_magnet_to_cloud_params: choices_append(('Add to Cloud', add_magnet_to_cloud_params))
		if browse_pack_params: choices_append(('Browse', browse_pack_params))
		if down_pack_params: choices_append(('Download Pack', down_pack_params))
		if down_file_params: choices_append(('Download File', down_file_params))
		if provider_source == 'rd_cloud': choices_append(('Delete from RD Cloud', 'rd_cloud_delete'))
		list_items = [{'line1': i[0], 'icon': self.poster} for i in choices]
		kwargs = {'items': json.dumps(list_items)}
		choice = select_dialog([i[1] for i in choices], **kwargs)
		return choice

	def set_filter(self, filtered_list):
		self.filter_applied = True
		self.reset_window(self.window_id)
		self.add_items(self.window_id, filtered_list)
		self.setFocusId(self.window_id)
		self.setProperty('total_results', str(len(filtered_list)))
		self.setProperty('filter_applied', 'true')
		self.setProperty('filter_info', '| Press [B]BACK[/B] to Cancel')

	def clear_filter(self):
		self.filter_applied = False
		self.reset_window(self.window_id)
		self.add_items(self.window_id, self.item_list)
		self.setFocusId(self.window_id)
		self.select_item(self.filter_window_id, 0)
		self.setProperty('total_results', self.total_results)
		self.setProperty('filter_applied', 'false')
		self.setProperty('filter_info', '')

class SourcesPlayback(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, *args)
		self.meta = kwargs.get('meta')
		self.is_canceled, self.skip_resolve, self.resume_choice = False, False, None
		self.meta_get = self.meta.get
		self.addon_fanart = addon_fanart()
		self.enable_scraper()

	def run(self):
		self.doModal()
		self.clearProperties()
		self.clear_modals()

	def onClick(self, controlID):
		self.resume_choice = {10: 'resume', 11: 'start_over', 12: 'cancel'}[controlID]

	def onAction(self, action):
		if action in self.closing_actions: self.is_canceled = True
		elif action == self.right_action and self.window_mode == 'resolver': self.skip_resolve = True

	def iscanceled(self):
		return self.is_canceled

	def skip_resolved(self):
		status = self.skip_resolve
		self.skip_resolve = False
		return status

	def reset_is_cancelled(self):
		self.is_canceled = False

	def enable_scraper(self):
		self.window_mode = 'scraper'
		self.set_scraper_properties()

	def enable_resolver(self):
		self.window_mode = 'resolver'
		self.set_resolver_properties()

	def enable_resume(self, percent):
		self.window_mode = 'resume'
		self.set_resume_properties(percent)

	def busy_spinner(self, toggle='true'):
		self.setProperty('enable_busy_spinner', toggle)

	def set_scraper_properties(self):
		title, genre = self.meta_get('title'), self.meta_get('genre', '')
		fanart, clearlogo = self.meta_get('fanart') or self.addon_fanart, self.meta_get('clearlogo') or ''
		self.setProperty('window_mode', self.window_mode)
		self.setProperty('fanart', fanart)
		self.setProperty('clearlogo', clearlogo)
		self.setProperty('title', title)
		self.setProperty('genre', ', '.join(genre))

	def set_resolver_properties(self):
		if self.meta_get('media_type') == 'movie': self.text = self.meta_get('plot')
		else:
			if avoid_episode_spoilers() and int(self.meta_get('playcount', '0')) == 0: plot = self.meta_get('tvshow_plot') or '* Hidden to Prevent Spoilers *'
			else: plot = self.meta_get('plot', '') or self.meta_get('tvshow_plot', '')
			self.text = '[B]%02dx%02d - %s[/B][CR][CR]%s' % (self.meta_get('season'), self.meta_get('episode'), self.meta_get('ep_name', 'N/A').upper(), plot)
		self.setProperty('window_mode', self.window_mode)
		self.setProperty('text', self.text)

	def set_resume_properties(self, percent):
		self.setProperty('window_mode', self.window_mode)
		self.setProperty('resume_percent', percent)
		self.setFocusId(10)
		self.update_resumer()

	def update_scraper(self, results_sd, results_720p, results_1080p, results_4k, results_total, content='', percent=0):
		self.setProperty('results_4k', str(results_4k))
		self.setProperty('results_1080p', str(results_1080p))
		self.setProperty('results_720p', str(results_720p))
		self.setProperty('results_sd', str(results_sd))
		self.setProperty('results_total', str(results_total))
		self.setProperty('percent', str(percent))
		self.set_text(2001, content)

	def update_resolver(self, text='', percent=0):
		try: self.setProperty('percent', str(percent))
		except: pass
		if text: self.set_text(2002, text)

	def update_resumer(self):
		count = 0
		while self.resume_choice is None:
			percent = int((float(count)/10000)*100)
			if percent >= 100: self.resume_choice = 'resume'
			self.setProperty('percent', str(percent))
			count += 100
			self.sleep(100)

class SourcesInfo(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, *args)
		self.item = kwargs['item']
		self.item_get_property = self.item.getProperty
		self.set_properties()

	def run(self):
		self.doModal()

	def onAction(self, action):
		self.close()

	def set_properties(self):
		self.setProperty('name', self.item_get_property('name'))
		self.setProperty('source_type', self.item_get_property('source_type'))
		self.setProperty('source_site', self.item_get_property('source_site'))
		self.setProperty('size_label', self.item_get_property('size_label'))
		self.setProperty('extraInfo', self.item_get_property('extraInfo'))
		self.setProperty('highlight', self.item_get_property('highlight'))
		self.setProperty('hash', self.item_get_property('hash'))
		self.setProperty('provider', self.item_get_property('provider').lower())
		self.setProperty('quality', self.item_get_property('quality').lower())
		self.setProperty('provider_icon', self.item_get_property('provider_icon'))
		self.setProperty('quality_icon', self.item_get_property('quality_icon'))
