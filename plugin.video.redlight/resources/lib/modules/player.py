# -*- coding: utf-8 -*-
import xbmc
import json
from threading import Thread
from apis.trakt_api import make_trakt_slug
from caches.settings_cache import get_setting
from modules import kodi_utils as ku, settings as st, watched_status as ws
# logger = ku.logger

class RedLightPlayer(xbmc.Player):
	def __init__ (self):
		xbmc.Player.__init__(self)

	def run(self, url=None, obj=None):
		ku.hide_busy_dialog()
		self.clear_playback_properties()
		if not url: return self.run_error()
		try: return self.play_video(url, obj)
		except: return self.run_error()

	def play_video(self, url, obj):
		self.set_constants(url, obj)
		ku.volume_checker()
		self.play(self.url, self.make_listing())
		if not self.is_generic:
			self.check_playback_start()
			if self.playback_successful: self.monitor()
			else:
				self.sources_object.playback_successful = self.playback_successful
				self.sources_object.cancel_all_playback = self.cancel_all_playback
				if self.cancel_all_playback: self.kill_dialog()
				self.stop()
			try: del self.kodi_monitor
			except: pass

	def check_playback_start(self):
		resolve_percent = 0
		while self.playback_successful is None:
			ku.hide_busy_dialog()
			if not self.sources_object.progress_dialog: self.playback_successful = True
			elif self.sources_object.progress_dialog.skip_resolved(): self.playback_successful = False
			elif self.sources_object.progress_dialog.iscanceled() or self.kodi_monitor.abortRequested(): self.cancel_all_playback, self.playback_successful = True, False
			elif resolve_percent >= 100: self.playback_successful = False
			elif ku.get_visibility('Window.IsTopMost(okdialog)'):
				ku.execute_builtin('SendClick(okdialog, 11)')
				self.playback_successful = False
			elif self.isPlayingVideo():
				try:
					if self.getTotalTime() not in ('0.0', '', 0.0, None) and ku.get_visibility('Window.IsActive(fullscreenvideo)'): self.playback_successful = True
				except: pass
			resolve_percent = round(resolve_percent + 26.0/100, 1)
			self.sources_object.progress_dialog.update_resolver(percent=resolve_percent)
			ku.sleep(50)

	def playback_close_dialogs(self):
		self.sources_object.playback_successful = True
		self.kill_dialog()
		ku.sleep(200)
		ku.close_all_dialog()

	def monitor(self):
		try:
			ensure_dialog_dead, total_check_time = False, 0
			if self.media_type == 'episode':
				play_random_continual = self.sources_object.random_continual
				play_random = self.sources_object.random
				disable_autoplay_next_episode = self.sources_object.disable_autoplay_next_episode
				if disable_autoplay_next_episode: ku.notification('Scrape with Custom Values - Autoplay Next Episode Cancelled', 4500)
				if any((play_random_continual, play_random, disable_autoplay_next_episode)): self.autoplay_nextep, self.autoscrape_nextep = False, False
				else: self.autoplay_nextep, self.autoscrape_nextep = self.sources_object.autoplay_nextep, self.sources_object.autoscrape_nextep
			else:
				show_stinger, stinger_use_chapters, stingers_percentage_fallback = st.stingers_show(), st.stingers_use_chapters(), st.stingers_percentage()
				play_random_continual, self.autoplay_nextep, self.autoscrape_nextep = False, False, False
			while total_check_time <= 30 and not ku.get_visibility('Window.IsActive(fullscreenvideo)'):
				ku.sleep(100)
				total_check_time += 0.10
			ku.hide_busy_dialog()
			ku.sleep(1000)
			if st.auto_enable_subs(): self.showSubtitles(True)
			while self.isPlayingVideo():
				try:
					if not ensure_dialog_dead:
						ensure_dialog_dead = True
						self.playback_close_dialogs()
					ku.sleep(1000)
					try: self.total_time, self.curr_time = self.getTotalTime(), self.getTime()
					except: ku.sleep(250); continue
					self.current_point = round(float(self.curr_time/self.total_time * 100), 1)
					if self.current_point >= 90:
						if play_random_continual: self.run_random_continual(); break
						if not self.media_marked: self.media_watched_marker()
					if self.media_type == 'episode':
						if self.autoplay_nextep or self.autoscrape_nextep:
							if not self.nextep_info_gathered: self.info_next_ep()
							if round(self.total_time - self.curr_time) <= self.start_prep: self.run_next_ep(); break
					elif show_stinger and not self.movie_stingers_run: 
						final_chapter = (self.final_chapter(75) or stingers_percentage_fallback) if stinger_use_chapters else stingers_percentage_fallback
						if self.current_point >= final_chapter: self.run_movie_stingers()
				except: pass
			ku.hide_busy_dialog()
			if not self.media_marked: self.media_watched_marker()
			self.clear_playback_properties()
		except:
			ku.hide_busy_dialog()
			self.sources_object.playback_successful = False
			self.sources_object.cancel_all_playback = True
			return self.kill_dialog()

	def make_listing(self):
		listitem = ku.make_listitem()
		listitem.setPath(self.url)
		listitem.setContentLookup(False)
		if self.is_generic:
			info_tag = listitem.getVideoInfoTag(True)
			info_tag.setMediaType('video')
			info_tag.setFilenameAndPath(self.url)
		else:
			self.tmdb_id, self.imdb_id, self.tvdb_id = self.meta_get('tmdb_id', ''), self.meta_get('imdb_id', ''), self.meta_get('tvdb_id', '')
			self.media_type, self.title, self.year = self.meta_get('media_type'), self.meta_get('title'), self.meta_get('year')
			self.season, self.episode = self.meta_get('season', ''), self.meta_get('episode', '')
			poster = self.meta_get('poster') or ku.get_icon('box_office')
			fanart = self.meta_get('fanart') or ku.get_addon_fanart()
			clearlogo = self.meta_get('clearlogo') or ''
			duration, genre, trailer, mpaa = self.meta_get('duration'), self.meta_get('genre', ''), self.meta_get('trailer'), self.meta_get('mpaa')
			rating, votes = self.meta_get('rating'), self.meta_get('votes')
			premiered, studio, tagline = self.meta_get('premiered'), self.meta_get('studio', ''), self.meta_get('tagline')
			director, writer, country = self.meta_get('director', ''), self.meta_get('writer', ''), self.meta_get('country', '')
			cast = self.meta_get('short_cast', []) or self.meta_get('cast', []) or []
			listitem.setLabel(self.title)
			if self.media_type == 'movie':
				plot = self.meta_get('plot')
				listitem.setArt({'poster': poster, 'fanart': fanart, 'icon': poster, 'clearlogo': clearlogo})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setMediaType('movie'), info_tag.setTitle(self.title), info_tag.setOriginalTitle(self.meta_get('original_title')), info_tag.setPlot(plot)
				info_tag.setYear(int(self.year)), info_tag.setRating(rating), info_tag.setVotes(votes), info_tag.setMpaa(mpaa)
				info_tag.setDuration(duration), info_tag.setCountries(country), info_tag.setTrailer(trailer), info_tag.setPremiered(premiered)
				info_tag.setTagLine(tagline), info_tag.setStudios(studio), info_tag.setIMDBNumber(self.imdb_id), info_tag.setGenres(genre)
				info_tag.setWriters(writer), info_tag.setDirectors(director), info_tag.setUniqueIDs({'imdb': self.imdb_id, 'tmdb': str(self.tmdb_id)})
				info_tag.setCast([ku.kodi_actor()(name=item['name'], role=item['role'], thumbnail=item['thumbnail']) for item in cast])
			else:
				if st.avoid_episode_spoilers() and int(self.meta_get('playcount', '0')) == 0: plot = self.meta_get('tvshow_plot') or '* Hidden to Prevent Spoilers *'
				else: plot = self.meta_get('plot') or self.meta_get('tvshow_plot')
				listitem.setArt({'poster': poster, 'fanart': fanart, 'icon': poster, 'clearlogo': clearlogo, 'tvshow.poster': poster, 'tvshow.clearlogo': clearlogo})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setMediaType('episode'), info_tag.setTitle(self.meta_get('ep_name')), info_tag.setOriginalTitle(self.meta_get('original_title'))
				info_tag.setTvShowTitle(self.title), info_tag.setTvShowStatus(self.meta_get('status')), info_tag.setSeason(self.season), info_tag.setEpisode(self.episode)
				info_tag.setPlot(plot), info_tag.setYear(int(self.year)), info_tag.setRating(rating), info_tag.setVotes(votes)
				info_tag.setMpaa(mpaa), info_tag.setDuration(duration), info_tag.setTrailer(trailer), info_tag.setFirstAired(premiered)
				info_tag.setStudios(studio), info_tag.setIMDBNumber(self.imdb_id), info_tag.setGenres(genre), info_tag.setWriters(writer)
				info_tag.setDirectors(director), info_tag.setUniqueIDs({'imdb': self.imdb_id, 'tmdb': str(self.tmdb_id), 'tvdb': str(self.tvdb_id)})
				info_tag.setCast([ku.kodi_actor()(name=item['name'], role=item['role'], thumbnail=item['thumbnail']) for item in cast])
				info_tag.setFilenameAndPath(self.url)
			self.set_resume_point(listitem)
			self.set_playback_properties()
		return listitem

	def media_watched_marker(self, force_watched=False):
		self.media_marked = True
		try:
			if self.current_point >= 90 or force_watched:
				watched_function = ws.mark_movie if self.media_type == 'movie' else ws.mark_episode
				watched_params = {'action': 'mark_as_watched', 'tmdb_id': self.tmdb_id, 'title': self.title, 'year': self.year, 'season': self.season, 'episode': self.episode,
									'tvdb_id': self.tvdb_id, 'from_playback': 'true'}
				Thread(target=self.run_media_progress, args=(watched_function, watched_params)).start()
			else:
				ku.clear_property('redlight.random_episode_history')
				if self.current_point >= 5:
					progress_params = {'media_type': self.media_type, 'tmdb_id': self.tmdb_id, 'curr_time': self.curr_time, 'total_time': self.total_time,
									'title': self.title, 'season': self.season, 'episode': self.episode, 'from_playback': 'true'}
					Thread(target=self.run_media_progress, args=(ws.set_bookmark, progress_params)).start()
		except: pass

	def run_media_progress(self, function, params):
		try: function(params)
		except: pass

	def run_next_ep(self):
		from modules.episode_tools import EpisodeTools
		if not self.media_marked: self.media_watched_marker(force_watched=True)
		EpisodeTools(self.meta, self.nextep_settings).auto_nextep()

	def run_random_continual(self):
		from modules.episode_tools import EpisodeTools
		if not self.media_marked: self.media_watched_marker(force_watched=True)
		EpisodeTools(self.meta).play_random_continual(False)

	def run_movie_stingers(self):
		self.movie_stingers_run = True
		stinger_keys = self.meta.get('stinger_keys', None)
		if not stinger_keys:
			try:
				keywords = self.meta.get('keywords', [])
				stinger_keys = [i['name'] for i in keywords['keywords'] if i['name'] in ('duringcreditsstinger', 'aftercreditsstinger')]
				self.meta['stinger_keys'] = stinger_keys
			except: pass
		if stinger_keys:
			from windows.base_window import open_window
			Thread(target=lambda: open_window(('windows.playback_notifications', 'StingersNotification'), 'playback_notifications.xml', meta=self.meta)).start()

	def set_resume_point(self, listitem):
		if self.playback_percent > 0.0: listitem.setProperty('StartPercent', str(self.playback_percent))

	def info_next_ep(self):
		self.nextep_info_gathered = True
		try:
			play_type = 'autoplay_nextep' if self.autoplay_nextep else 'autoscrape_nextep'
			nextep_settings = st.auto_nextep_settings(play_type)
			watching_check = nextep_settings['watching_check']
			still_watching_check = 15 if self.meta_get('watch_count') == watching_check else 0
			final_chapter = self.final_chapter(90) if nextep_settings['use_chapters'] else None
			percentage = 100 - final_chapter if final_chapter else nextep_settings['window_percentage']
			window_time = round((percentage/100) * self.total_time) + still_watching_check
			use_window = nextep_settings['alert_method'] == 0
			default_action = nextep_settings['default_action']
			self.start_prep = nextep_settings['scraper_time'] + window_time
			self.nextep_settings = {'use_window': use_window, 'window_time': window_time, 'default_action': default_action, 'play_type': play_type, 'watching_check': watching_check}
		except: pass

	def final_chapter(self, threshhold):
		try:
			final_chapter = float(ku.get_infolabel('Player.Chapters').split(',')[-1])
			if final_chapter >= threshhold: return final_chapter
		except: pass
		return None

	def kill_dialog(self):
		try: self.sources_object._kill_progress_dialog()
		except: ku.close_all_dialog()

	def set_constants(self, url, obj):
		self.url = url
		self.sources_object = obj
		self.is_generic = self.sources_object == 'video'
		if not self.is_generic:
			self.meta = self.sources_object.meta
			self.meta_get, self.kodi_monitor, self.playback_percent = self.meta.get, ku.kodi_monitor(), self.sources_object.playback_percent or 0.0
			self.playing_filename = self.sources_object.playing_filename
			self.media_marked, self.nextep_info_gathered, self.movie_stingers_run = False, False, False
			self.playback_successful, self.cancel_all_playback = None, False
			self.playing_item = self.sources_object.playing_item

	def set_playback_properties(self):
		try:
			trakt_ids = {'tmdb': self.tmdb_id, 'imdb': self.imdb_id, 'slug': make_trakt_slug(self.title)}
			if self.media_type == 'episode': trakt_ids['tvdb'] = self.tvdb_id
			ku.set_property('script.trakt.ids', json.dumps(trakt_ids))
			if self.playing_filename: ku.set_property('subs.player_filename', self.playing_filename)
		except: pass

	def clear_playback_properties(self):
		ku.clear_property('redlight.window_stack')
		ku.clear_property('script.trakt.ids')
		ku.clear_property('subs.player_filename')

	def run_error(self):
		try: self.sources_object.playback_successful = False
		except: pass
		self.clear_playback_properties()
		ku.notification('Playback Failed', 3500)
		return False
