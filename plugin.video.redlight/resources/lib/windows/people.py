# -*- coding: utf-8 -*-
from threading import Thread
from windows.base_window import BaseDialog, window_manager, window_player
from apis.tmdb_api import tmdb_people_info, tmdb_people_full_info
from apis.imdb_api import imdb_people_trivia
from indexers import dialogs
from indexers.images import Images
from modules.kodi_utils import addon_fanart, execute_builtin, notification, show_busy_dialog, hide_busy_dialog, get_icon
from modules.settings import extras_enable_scrollbars, tmdb_api_key, easynews_authorized, mpaa_region, rpdb_info
from modules.utils import calculate_age, get_datetime, remove_accents
# from modules.kodi_utils import logger


class People(BaseDialog):
	more_from_movies_id, more_from_tvshows_id, trivia_id, more_from_director_id = 2050, 2051, 2052, 2053
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, *args)
		self.control_id = None
		self.current_year = get_datetime(string=True).split('-')[0]
		self.Images = Images().run
		self.set_starting_constants(kwargs)
		self.make_person_data()
		self.set_properties()
		self.empty_poster = get_icon('box_office')
		self.tasks = (self.set_infoline1, self.make_trivia, self.make_movies, self.make_tvshows, self.make_director)

	def onInit(self):
		self.set_home_property('window_loaded', 'true')
		for i in self.tasks: Thread(target=i).start()
		self.set_default_focus()
		if self.starting_position:
			try: self.set_returning_focus(*self.starting_position)
			except: self.set_default_focus()

	def set_default_focus(self):
		try: self.setFocusId(10)
		except: self.close()

	def set_returning_focus(self, window_id, focus, sleep_time=700):
		try:
			self.sleep(sleep_time)
			self.setFocusId(window_id)
			self.select_item(window_id, focus)
		except: self.set_default_focus()

	def run(self):
		self.doModal()
		self.clearProperties()
		self.clear_home_property('window_theme.people')
		self.clear_home_property('window_theme.highlight.people')

	def onClick(self, controlID):
		self.control_id = None
		if controlID in (10, 11, 12, 13, 50):
			if controlID == 10:
				self.Images({'mode': 'tmdb_people_image_results', 'actor_name': self.person_name, 'actor_id': self.person_id, 'actor_image': self.person_image})
			elif controlID == 11:
				self.Images({'mode': 'tmdb_people_tagged_image_results', 'actor_name': self.person_name, 'actor_id': self.person_id})
			elif controlID == 12:
				self.Images({'mode': 'easynews_image_results', 'key_id': self.person_name, 'page_no': 1})
			elif controlID == 13:
				title = '%s|%s|%s' % (self.person_name, self.person_thumb, self.person_image)
				dialogs.favorites_manager_choice({'media_type': 'people', 'tmdb_id': str(self.person_id), 'title': title, 'refresh': 'false'})
			else:
				self.show_text_media(text=self.person_biography)
		else: self.control_id = controlID

	def onAction(self, action):
		if action in self.closing_actions: return window_manager(self)
		if action == self.info_action:
			focus_id = self.getFocusId()
			if not focus_id in (People.more_from_movies_id, People.more_from_tvshows_id, People.more_from_director_id): return
			show_busy_dialog()
			from modules.metadata import movie_meta, tvshow_meta
			chosen_listitem = self.get_listitem(focus_id)
			media_type = 'movie' if focus_id in (People.more_from_movies_id, People.more_from_director_id) else 'tvshow'
			function = movie_meta if media_type == 'movie' else tvshow_meta
			meta = function('tmdb_id', chosen_listitem.getProperty('tmdb_id'), tmdb_api_key(), mpaa_region(), get_datetime())
			hide_busy_dialog()
			self.show_extrainfo(meta)
		if not self.control_id: return
		if action in self.selection_actions:
			chosen_listitem = self.get_listitem(self.control_id)
			chosen_var = chosen_listitem.getProperty(self.item_action_dict[self.control_id])
			if self.control_id in (People.more_from_movies_id, People.more_from_tvshows_id, People.more_from_director_id):
				if self.control_id in (People.more_from_movies_id, People.more_from_director_id): media_type = 'movie'
				else: media_type = 'tvshow'
				self.set_current_params()
				self.new_params = {'mode': 'extras_menu_choice', 'tmdb_id': chosen_var, 'media_type': media_type, 'is_external': self.is_external, 'stacked': 'true'}
				return window_manager(self)
			elif self.control_id == People.trivia_id:
				end_index = self.show_text_media(text=self.get_attribute(self, chosen_var), current_index=self.get_position(self.control_id))
				self.select_item(self.control_id, end_index)

	def set_infoline1(self):
		gender, age = self.person_gender or None, '%syo' % self.person_age if self.person_age else None
		birthday = self.person_birthday
		if birthday and self.person_deathday: birthday += '  [B]-[/B]  %s' % self.person_deathday
		self.set_label(2001, '[B]  •  [/B]'.join([i for i in (gender, age, birthday) if i]))

	def make_movies(self):
		self.make_more_from('movie')

	def make_tvshows(self):
		self.make_more_from('tvshow')

	def make_director(self):
		self.make_more_from('director')

	def show_extrainfo(self, meta):
		text = '[B]  •  [/B]'.join([i for i in (meta.get('year'), str(round(meta.get('rating'), 1)) if meta.get('rating') not in (0, 0.0, None) else None,
								meta.get('mpaa')) if i]) + '[CR][CR]%s' % meta.get('plot')
		poster = meta.get('poster', self.empty_poster)
		return self.show_text_media(text=text, poster=poster)

	def make_person_data(self):
		compare_name = remove_accents(self.key_id)
		if self.key_id not in (None, 'None', ''):
			try:
				data = tmdb_people_info(self.key_id)['results']
				data = [i for i in data if remove_accents(i['name']) == compare_name]
				data = sorted(data, key=lambda k: k.get('popularity', 0.0), reverse=True)
				if len(data) > 1:
					for item in data:
						if self.reference_tmdb_id not in (None, 'None', ''):
							known_for = item.get('known_for', [])
							if known_for:
								known_for_tmdb_ids = [str(i['id']) for i in known_for]
								if self.reference_tmdb_id in known_for_tmdb_ids:
									self.person_id = item['id']
									break
				if not self.person_id:
					try: self.person_id = data[0]['id']
					except: pass
			except: self.person_id = self.actor_id
		else: self.person_id = self.actor_id
		if not self.person_id:
			notification('No Results')
			return self.close()
		person_info = tmdb_people_full_info(self.person_id)
		self.person_imdb_id = person_info['imdb_id']
		self.person_name = person_info['name']
		self.imdb_id = person_info['imdb_id']
		image_path = person_info['profile_path']
		if image_path:
			self.person_thumb = 'https://image.tmdb.org/t/p/%s%s' % ('w185', image_path)
			self.person_image = 'https://image.tmdb.org/t/p/%s%s' % ('h632', image_path)
		else:
			self.person_thumb = self.person_image = get_icon('empty_person')
		try: self.person_gender = {0: '', 1: 'Female', 2: 'Male', 3: ''}[person_info.get('gender')]
		except: self.person_gender = ''
		self.person_place_of_birth = person_info.get('place_of_birth', '') or ''
		self.person_biography = person_info.get('biography', '') or ''
		self.person_birthday = person_info.get('birthday', '') or ''
		self.person_deathday = person_info.get('deathday', '') or ''
		if self.person_deathday: self.person_age = calculate_age(self.person_birthday, '%Y-%m-%d', self.person_deathday)
		elif self.person_birthday: self.person_age = calculate_age(self.person_birthday, '%Y-%m-%d')
		else: self.person_age = ''
		try:
			more_from_data = person_info['combined_credits']
			acting_data = more_from_data['cast']
			directing_data = more_from_data['crew']
			self.movie_data = [i for i in acting_data if i['media_type'] == 'movie']
			self.tvshow_data = [i for i in acting_data if i['media_type'] == 'tv']
			self.director_data = [i for i in directing_data if i['job'].lower() == 'director']
		except: self.movie_data, self.tvshow_data, self.director_data = [], [], []

	def make_more_from(self, media_type):
		roles_exclude = ('himself', 'herself', 'self', 'narrator', 'voice', 'voice (voice)')
		try:
			if media_type == 'movie':
				list_type, _id, data, date_key = media_type, People.more_from_movies_id, self.movie_data, 'release_date'
				try: data = [i for i in data if not 99 in i['genre_ids'] and not i['character'].lower() in roles_exclude]
				except: pass
			elif media_type == 'tvshow':
				list_type, _id, data, date_key = media_type, People.more_from_tvshows_id, self.tvshow_data, 'first_air_date'
				try: data = [i for i in data if not any(x in (10763, 10764, 10767) for x in i['genre_ids']) and not i['character'].lower() in roles_exclude]
				except: pass
			else: list_type, _id, data, date_key = 'movie', People.more_from_director_id, self.director_data, 'release_date'
			data = self.sort_items_by_release(data, date_key)
			item_list = list(self.make_tmdb_listitems(data, list_type))
			self.setProperty('more_from_%s.number' % media_type, 'x%s' % len(item_list))
			self.item_action_dict[_id] = 'tmdb_id'
			self.add_items(_id, item_list)
		except: pass

	def make_trivia(self):
		if not self.person_imdb_id: return
		def builder():
			for item in self.all_trivia:
				try:
					listitem = self.make_listitem()
					listitem.setProperties({'text': item, 'content_list': 'all_trivia'})
					yield listitem
				except: pass
		try:
			self.all_trivia = imdb_people_trivia(self.person_imdb_id)
			item_list = list(builder())
			self.setProperty('imdb_trivia.number', 'x%s' % len(item_list))
			self.item_action_dict[People.trivia_id] = 'content_list'
			self.add_items(People.trivia_id, item_list)
		except: pass

	def make_tmdb_listitems(self, data, media_type):
		used_ids = []
		append = used_ids.append
		name_key = 'title' if media_type == 'movie' else 'name'
		release_key = 'release_date' if media_type == 'movie' else 'first_air_date'
		for item in data:
			try:
				tmdb_id = item['id']
				if tmdb_id in used_ids: continue
				listitem = self.make_listitem()
				year = self.get_release_year(item[release_key])
				poster = 'https://image.tmdb.org/t/p/%s%s' % ('w300', item['poster_path']) if item['poster_path'] else ''
				if self.rpdb_api_key and poster:
					media = 'movie' if media_type == 'movie' else 'series'
					try: poster = 'https://api.ratingposterdb.com/%s/tmdb/poster-default/%s-%s.jpg?fallback=true' % (self.rpdb_api_key, media, str(item['id'])) + self.rpdb_format
					except: pass
				elif not poster: poster = self.empty_poster
				listitem.setProperties({'name': item[name_key], 'release_date': year, 'vote_average': '%.1f' % item['vote_average'], 'thumbnail': poster, 'tmdb_id': str(tmdb_id)})
				append(tmdb_id)
				yield listitem
			except: pass

	def get_release_year(self, release_data):
		try:
			if release_data in ('', None): release_data = 'N/A'
			else: release_data = release_data.split('-')[0]
		except: pass
		return release_data

	def sort_items_by_release(self, data, key):
		blank = [i for i in data if not i.get(key, None)]
		data = [i for i in data if not i in blank]
		future = sorted([i for i in data if i[key].split('-')[0] > self.current_year], key=lambda x: x[key], reverse=True)
		present = sorted([i for i in data if i[key] and i not in future], key=lambda x: x[key], reverse=True)
		return present + future + blank

	def show_text_media(self, text='', poster=None, current_index=None):
		return self.open_window(('windows.extras', 'ShowTextMedia'), 'textviewer_media.xml', text=text, poster=poster or self.person_image, current_index=current_index)

	def set_current_params(self, set_starting_position=True):
		self.current_params = {'mode': 'person_data_dialog', 'key_id': self.key_id, 'actor_name': self.person_name, 'actor_image': self.person_image, 'stacked': 'true',
								'actor_id': self.person_id, 'reference_tmdb_id': self.reference_tmdb_id, 'is_external': self.is_external}
		if set_starting_position: self.current_params['starting_position'] = [self.control_id, self.get_position(self.control_id)]

	def set_starting_constants(self, kwargs):
		self.item_action_dict = {}
		self.current_params, self.new_params = {}, {}
		self.person_id = None
		self.is_external = kwargs.get('is_external', 'false').lower()
		self.key_id = kwargs.get('key_id', '') or kwargs.get('query', '')
		self.actor_id = kwargs.get('actor_id', '')
		self.reference_tmdb_id = str(kwargs.get('reference_tmdb_id', ''))
		self.starting_position = kwargs.get('starting_position', None)
		self.enable_scrollbars = extras_enable_scrollbars()
		rpdb_information = rpdb_info('extras')
		self.rpdb_api_key, self.rpdb_format = rpdb_information['rpdb_api_key'], rpdb_information['rpdb_format']

	def set_properties(self):
		self.set_home_property('window_theme.people', self.get_home_property('window_theme'))
		self.setProperty('name', self.person_name)
		self.setProperty('id', str(self.person_id))
		self.setProperty('image', self.person_image)
		self.setProperty('fanart', addon_fanart())
		self.setProperty('gender', self.person_gender)
		self.setProperty('place_of_birth', self.person_place_of_birth)
		self.setProperty('biography', self.person_biography)
		self.setProperty('birthday', self.person_birthday)
		self.setProperty('deathday', self.person_deathday)
		self.setProperty('age', str(self.person_age))
		self.setProperty('enable_scrollbars', self.enable_scrollbars)
		self.setProperty('easynews_authorized', 'true' if easynews_authorized() else 'false')
