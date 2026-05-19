# -*- coding: utf-8 -*-
from apis.premiumize_api import Premiumize
from modules import source_utils
from modules.utils import clean_file_name, normalize
from modules.settings import enabled_debrids_check, filter_by_name
# from modules.kodi_utils import logger

class source:
	def __init__(self):
		self.scrape_provider = 'pm_cloud'
		self.sources, self.scrape_results = [], []
		self.extensions = source_utils.supported_video_extensions()

	def results(self, info):
		try:
			if not enabled_debrids_check('pm'): return source_utils.internal_results(self.scrape_provider, self.sources)
			filter_title = filter_by_name(self.scrape_provider)
			self.media_type, title, self.year, self.season, self.episode = info.get('media_type'), info.get('title'), int(info.get('year')), info.get('season'), info.get('episode')
			self.folder_query = source_utils.clean_title(normalize(title))
			self._scrape_cloud()
			if not self.scrape_results: return source_utils.internal_results(self.scrape_provider, self.sources)
			aliases = source_utils.get_aliases_titles(info.get('aliases', []))
			def _process():
				for item in self.scrape_results:
					try:
						file_name = normalize(item['name'])
						if filter_title and not source_utils.check_title(title, file_name, aliases, self.year, self.season, self.episode): continue
						display_name = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						path, file_dl = item['path'], item['id']
						size = round(float(item['size'])/1073741824, 2)
						video_quality, details = source_utils.get_file_info(name_info=source_utils.release_info_format(file_name))
						source_item = {'name': file_name, 'display_name': display_name, 'quality': video_quality, 'size': size, 'size_label': '%.2f GB' % size,
									'debrid': self.scrape_provider, 'extraInfo': details, 'url_dl': file_dl, 'id': file_dl, 'downloads': False, 'direct': True,
									'source': self.scrape_provider, 'scrape_provider': self.scrape_provider}
						yield source_item
					except: pass
			self.sources = list(_process())
		except Exception as e:
			from modules.kodi_utils import logger
			logger('premiumize scraper Exception', str(e))
		source_utils.internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _scrape_cloud(self):
		try:
			cloud_files = Premiumize.user_cloud_all()['files']
			cloud_files = [i for i in cloud_files if i['path'].lower().endswith(tuple(self.extensions))]
			cloud_files.sort(key=lambda k: k['name'])
		except: return self.sources
		append = self.scrape_results.append
		year_query_list = self._year_query_list()
		for item in cloud_files:
			normalized = normalize(item['name'])
			folder_name = source_utils.clean_title(normalized)
			if not self.folder_query in folder_name: continue
			if self.media_type == 'movie':
				if not any(x in normalized for x in year_query_list): continue
			elif not source_utils.seas_ep_filter(self.season, self.episode, normalized): continue
			append(item)

	def _year_query_list(self):
		return (str(self.year), str(self.year+1), str(self.year-1))
