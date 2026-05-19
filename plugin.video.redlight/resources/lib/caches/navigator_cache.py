# -*- coding: utf-8 -*-
from caches.base_cache import connect_database
from modules.kodi_utils import get_property, set_property, clear_property
# from modules.kodi_utils import logger

class NavigatorCache:
	root_list = [
	{'name': 'Movies', 'mode': 'navigator.main', 'action': 'MovieList', 'iconImage': 'movies'},
	{'name': 'TV Shows', 'mode': 'navigator.main', 'action': 'TVShowList', 'iconImage': 'tv'},
	{'name': 'Anime', 'mode': 'navigator.main', 'action': 'AnimeList', 'iconImage': 'anime'},
	{'name': 'People', 'mode': 'navigator.people', 'iconImage': 'empty_person'},
	{'name': 'Search', 'mode': 'navigator.search', 'iconImage': 'search'},
	{'name': 'Discover', 'mode': 'navigator.discover', 'iconImage': 'discover'},
	{'name': 'Random Lists', 'mode': 'navigator.random_lists', 'iconImage': 'random'},
	{'name': 'My Lists', 'mode': 'navigator.my_content', 'iconImage': 'lists'},
	{'name': 'My Services', 'mode': 'navigator.premium', 'iconImage': 'premium'},
	{'name': 'Favorites', 'mode': 'navigator.favorites', 'iconImage': 'favorites'},
	{'name': 'Downloads', 'mode': 'navigator.downloads', 'iconImage': 'downloads'},
	{'name': 'Tools', 'mode': 'navigator.tools', 'iconImage': 'settings2'}
				]
	movie_list = [
	{'name': 'Trending', 'mode': 'build_movie_list', 'action': 'trakt_movies_trending', 'random_support': 'true', 'iconImage': 'trending'},
	{'name': 'Trending Recent', 'mode': 'build_movie_list', 'action': 'trakt_movies_trending_recent', 'random_support': 'true', 'iconImage': 'trending_recent'},
	{'name': 'Popular', 'mode': 'build_movie_list', 'action': 'tmdb_movies_popular', 'random_support': 'true', 'iconImage': 'popular'},
	{'name': 'Popular Today', 'mode': 'build_movie_list', 'action': 'tmdb_movies_popular_today', 'random_support': 'true', 'iconImage': 'popular_today'},
	{'name': 'Premieres', 'mode': 'build_movie_list', 'action': 'tmdb_movies_premieres', 'random_support': 'true', 'iconImage': 'fresh'},
	{'name': 'Latest Releases', 'mode': 'build_movie_list', 'action': 'tmdb_movies_latest_releases', 'random_support': 'true', 'iconImage': 'dvd'},
	{'name': 'Most Watched', 'mode': 'build_movie_list', 'action': 'trakt_movies_most_watched', 'random_support': 'true', 'iconImage': 'most_watched'},
	{'name': 'Most Favorited', 'mode': 'build_movie_list', 'action': 'trakt_movies_most_favorited', 'random_support': 'true', 'iconImage': 'favorites'},
	{'name': 'Top 10 Box Office', 'mode': 'build_movie_list', 'action': 'trakt_movies_top10_boxoffice', 'iconImage': 'box_office'},
	{'name': 'Blockbusters', 'mode': 'build_movie_list', 'action': 'tmdb_movies_blockbusters', 'random_support': 'true', 'iconImage': 'most_voted'},
	{'name': 'In Theaters', 'mode': 'build_movie_list', 'action': 'tmdb_movies_in_theaters', 'random_support': 'true', 'iconImage': 'intheatres'},
	{'name': 'Up Coming', 'mode': 'build_movie_list', 'action': 'tmdb_movies_upcoming', 'random_support': 'true', 'iconImage': 'lists'},
	{'name': 'Oscar Winners', 'mode': 'build_movie_list', 'action': 'tmdb_movies_oscar_winners', 'random_support': 'true', 'iconImage': 'oscar_winners'},
	{'name': 'Genres', 'mode': 'navigator.genres', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'genres'},
	{'name': 'Providers', 'mode': 'navigator.providers', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'providers'},
	{'name': 'Languages', 'mode': 'navigator.languages', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'languages'},
	{'name': 'Years', 'mode': 'navigator.years', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'calender'},
	{'name': 'Decades', 'mode': 'navigator.decades', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'calendar_decades'},
	{'name': 'Certifications', 'mode': 'navigator.certifications', 'menu_type': 'movie', 'random_support': 'true', 'iconImage': 'certifications'},
	{'name': 'Because You Watched...', 'iconImage': 'because_you_watched', 'mode': 'navigator.because_you_watched', 'menu_type': 'movie'},
	{'name': 'Watched', 'mode': 'build_movie_list', 'action': 'watched_movies', 'iconImage': 'watched_1'},
	{'name': 'Recently Watched', 'mode': 'build_movie_list', 'action': 'recent_watched_movies', 'iconImage': 'watched_recent'},
	{'name': 'In Progress', 'mode': 'build_movie_list', 'action': 'in_progress_movies', 'iconImage': 'player'}
				]
	tvshow_list = [
	{'name': 'Trending', 'mode': 'build_tvshow_list', 'action': 'trakt_tv_trending', 'random_support': 'true', 'iconImage': 'trending'},
	{'name': 'Trending Recent', 'mode': 'build_tvshow_list', 'action': 'trakt_tv_trending_recent', 'random_support': 'true', 'iconImage': 'trending_recent'},
	{'name': 'Popular', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_popular', 'random_support': 'true', 'iconImage': 'popular'},
	{'name': 'Popular Today', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_popular_today', 'random_support': 'true', 'iconImage': 'popular_today'},
	{'name': 'Premieres', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_premieres', 'random_support': 'true', 'iconImage': 'fresh'},
	{'name': 'Most Watched', 'mode': 'build_tvshow_list', 'action': 'trakt_tv_most_watched', 'random_support': 'true', 'iconImage': 'most_watched'},
	{'name': 'Most Favorited', 'mode': 'build_tvshow_list', 'action': 'trakt_tv_most_favorited', 'random_support': 'true', 'iconImage': 'favorites'},
	{'name': 'Airing Today', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_airing_today', 'random_support': 'true', 'iconImage': 'live'},
	{'name': 'On the Air', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_on_the_air', 'random_support': 'true', 'iconImage': 'ontheair'},
	{'name': 'Up Coming', 'mode': 'build_tvshow_list', 'action': 'tmdb_tv_upcoming', 'random_support': 'true', 'iconImage': 'lists'},
	{'name': 'Genres', 'mode': 'navigator.genres', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'genres'},
	{'name': 'Providers', 'mode': 'navigator.providers', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'providers'},
	{'name': 'Networks', 'mode': 'navigator.networks', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'networks'},
	{'name': 'Languages', 'mode': 'navigator.languages', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'languages'},
	{'name': 'Years', 'mode': 'navigator.years', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'calender'},
	{'name': 'Decades', 'mode': 'navigator.decades', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'calendar_decades'},
	{'name': 'Certifications', 'mode': 'navigator.certifications', 'menu_type': 'tvshow', 'random_support': 'true', 'iconImage': 'certifications'},
	{'name': 'Because You Watched...', 'mode': 'navigator.because_you_watched', 'menu_type': 'tvshow', 'iconImage': 'because_you_watched'},
	{'name': 'Watched', 'mode': 'build_tvshow_list', 'action': 'watched_tvshows', 'iconImage': 'watched_1'},
	{'name': 'Recently Watched', 'mode': 'build_tvshow_list', 'action': 'recent_watched_tvshows', 'iconImage': 'watched_recent'},
	{'name': 'In Progress', 'mode': 'build_tvshow_list', 'action': 'in_progress_tvshows', 'iconImage': 'in_progress_tvshow'},
	{'name': 'Recently Watched Episodes', 'mode': 'build_recently_watched_episode', 'iconImage': 'watched_recent'},
	{'name': 'In Progress Episodes', 'mode': 'build_in_progress_episode', 'iconImage': 'player'},
	{'name': 'Next Episodes', 'mode': 'build_next_episode', 'iconImage': 'next_episodes'}
				]
	anime_list = [
	{'name': 'Anime Trending', 'mode': 'build_tvshow_list', 'action': 'trakt_anime_trending', 'random_support': 'true', 'iconImage': 'trending'},
	{'name': 'Anime Trending Recent', 'mode': 'build_tvshow_list', 'action': 'trakt_anime_trending_recent', 'random_support': 'true', 'iconImage': 'trending_recent'},
	{'name': 'Anime Popular', 'mode': 'build_tvshow_list', 'action': 'tmdb_anime_popular', 'random_support': 'true', 'iconImage': 'popular'},
	{'name': 'Anime Popular Recent', 'mode': 'build_tvshow_list', 'action': 'tmdb_anime_popular_recent', 'random_support': 'true', 'iconImage': 'popular_today'},
	{'name': 'Anime Premieres', 'mode': 'build_tvshow_list', 'action': 'tmdb_anime_premieres', 'random_support': 'true', 'iconImage': 'fresh'},
	{'name': 'Anime Most Watched', 'mode': 'build_tvshow_list', 'action': 'trakt_anime_most_watched', 'random_support': 'true', 'iconImage': 'most_watched'},
	{'name': 'Anime Most Favorited', 'mode': 'build_tvshow_list', 'action': 'trakt_anime_most_favorited', 'random_support': 'true', 'iconImage': 'favorites'},
	{'name': 'Anime On the Air', 'mode': 'build_tvshow_list', 'action': 'tmdb_anime_on_the_air', 'random_support': 'true', 'iconImage': 'ontheair'},
	{'name': 'Anime Upcoming', 'mode': 'build_tvshow_list', 'action': 'tmdb_anime_upcoming', 'random_support': 'true', 'iconImage': 'lists'},
	{'name': 'Anime Genres', 'mode': 'navigator.genres', 'menu_type': 'anime', 'random_support': 'true', 'iconImage': 'genres'},
	{'name': 'Anime Providers', 'mode': 'navigator.providers', 'menu_type': 'anime', 'random_support': 'true', 'iconImage': 'providers'},
	{'name': 'Anime Years', 'mode': 'navigator.years', 'menu_type': 'anime', 'random_support': 'true', 'iconImage': 'calender'},
	{'name': 'Anime Decades', 'mode': 'navigator.decades', 'menu_type': 'anime', 'random_support': 'true', 'iconImage': 'calendar_decades'},
	{'name': 'Anime Certifications', 'mode': 'navigator.certifications', 'menu_type': 'anime', 'random_support': 'true', 'iconImage': 'certifications'},
	{'name': 'Anime Watched', 'mode': 'build_tvshow_list', 'action': 'watched_tvshows', 'is_anime_list': 'true', 'iconImage': 'watched_1'},
	{'name': 'Anime Recently Watched', 'mode': 'build_tvshow_list', 'action': 'recent_watched_tvshows', 'is_anime_list': 'true', 'iconImage': 'watched_recent'},
	{'name': 'Anime In Progress', 'mode': 'build_tvshow_list', 'action': 'in_progress_tvshows', 'is_anime_list': 'true', 'iconImage': 'in_progress_tvshow'},
	{'name': 'Anime Recently Watched Episodes', 'mode': 'build_recently_watched_episode', 'is_anime_list': 'true', 'iconImage': 'watched_recent'},
	{'name': 'Anime In Progress Episodes', 'mode': 'build_in_progress_episode', 'is_anime_list': 'true', 'iconImage': 'player'},
	{'name': 'Anime Next Episodes', 'mode': 'build_next_episode', 'iconImage': 'next_episodes', 'is_anime_list': 'true'}
					]

	main_menus = {'RootList': root_list, 'MovieList': movie_list, 'TVShowList': tvshow_list, 'AnimeList': anime_list}
	
	def get_main_lists(self, list_name):
		default_contents = self.get_memory_cache(list_name, 'default')
		if not default_contents:
			default_contents = self.get_list(list_name, 'default')
			if default_contents == None:
				self.rebuild_database()
				return self.get_main_lists(list_name)
			try: edited_contents = self.get_list(list_name, 'edited')
			except: edited_contents = None
		else:
			edited_contents = self.get_memory_cache(list_name, 'edited')
		return default_contents, edited_contents

	def get_list(self, list_name, list_type):
		contents = None
		try:
			dbcon = connect_database('navigator_db')
			contents = eval(dbcon.execute('SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?', (list_name, list_type)).fetchone()[0])
			self.set_memory_cache(list_name, list_type, contents)
		except: pass
		return contents

	def set_list(self, list_name, list_type, list_contents):
		dbcon = connect_database('navigator_db')
		dbcon.execute('INSERT OR REPLACE INTO navigator VALUES (?, ?, ?)', (list_name, list_type, repr(list_contents)))
		self.set_memory_cache(list_name, list_type, list_contents)

	def delete_list(self, list_name, list_type):
		dbcon = connect_database('navigator_db')
		dbcon.execute('DELETE FROM navigator WHERE list_name=? and list_type=?', (list_name, list_type))
		self.delete_memory_cache(list_name, list_type)
		dbcon.execute('VACUUM')
	
	def get_memory_cache(self, list_name, list_type):
		try: return eval(get_property(self._get_list_prop(list_type) % list_name))
		except: return None
	
	def set_memory_cache(self, list_name, list_type, list_contents):
		set_property(self._get_list_prop(list_type) % list_name, repr(list_contents))

	def delete_memory_cache(self, list_name, list_type):
		clear_property(self._get_list_prop(list_type) % list_name)

	def get_shortcut_folders(self):
		try:
			dbcon = connect_database('navigator_db')
			folders = dbcon.execute('SELECT list_name, list_contents FROM navigator WHERE list_type = ?', ('shortcut_folder',)).fetchall()
			folders = sorted([(str(i[0]), eval(i[1])) for i in folders], key=lambda s: s[0].lower())
		except: folders = []
		return folders

	def get_shortcut_folder_contents(self, list_name):
		try:
			dbcon = connect_database('navigator_db')
			contents = eval(dbcon.execute('SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?', (list_name, 'shortcut_folder')).fetchone()[0])
		except: contents = []
		return contents

	def currently_used_list(self, list_name):
		try: used_list = self.get_memory_cache(list_name, 'edited') or self.get_memory_cache(list_name, 'default') \
						or self.get_list(list_name, 'edited') or self.get_list(list_name, 'default')
		except: used_list = []
		if not used_list:
			self.rebuild_database()
			used_list = NavigatorCache.main_menus[list_name]
		return used_list

	def rebuild_database(self):
		dbcon = connect_database('navigator_db')
		main_items = NavigatorCache.main_menus.items()
		for list_name, list_contents in main_items: self.set_list(list_name, 'default', list_contents)

	def _get_list_prop(self, list_type):
		return {'default': 'redlight_%s_default', 'edited': 'redlight_%s_edited', 'shortcut_folder': 'redlight_%s_shortcut_folder'}[list_type]
	
	def random_movie_lists(self):
		m_list = NavigatorCache.movie_list
		movie_random_converts = {'navigator.genres': 'tmdb_movies_genres', 'navigator.providers': 'tmdb_movies_providers',  'navigator.languages': 'tmdb_movies_languages',
								'navigator.years': 'tmdb_movies_year', 'navigator.decades': 'tmdb_movies_decade', 'navigator.certifications': 'tmdb_movies_certifications'}
		return [dict(i, **{'mode': 'random.build_movie_list', 'action': i.get('action') or movie_random_converts[i['mode']],
							'random': 'true', 'name': 'Movies Random %s' % i['name'], 'menu_type': 'movie'}) for i in m_list if 'random_support' in i]
	
	def random_tvshow_lists(self):
		t_list = NavigatorCache.tvshow_list
		tvshow_random_converts = {'navigator.genres': 'tmdb_tv_genres', 'navigator.providers': 'tmdb_tv_providers', 'navigator.networks': 'tmdb_tv_networks',
								'navigator.languages': 'tmdb_tv_languages', 'navigator.years': 'tmdb_tv_year', 'navigator.decades': 'tmdb_tv_decade',
								'navigator.certifications': 'trakt_tv_certifications'}
		return [dict(i, **{'mode': 'random.build_tvshow_list', 'action': i.get('action') or tvshow_random_converts[i['mode']],
							'random': 'true', 'name': 'TV Shows Random %s' % i['name'], 'menu_type': 'tvshow'}) for i in t_list if 'random_support' in i]
	
	def random_anime_lists(self):
		a_list = NavigatorCache.anime_list
		anime_random_converts = {'navigator.genres': 'tmdb_anime_genres', 'navigator.providers': 'tmdb_anime_providers', 'navigator.years': 'tmdb_anime_year',
								'navigator.decades': 'tmdb_anime_decade', 'navigator.certifications': 'trakt_anime_certifications'}
		return [dict(i, **{'mode': 'random.build_tvshow_list', 'action': i.get('action') or anime_random_converts[i['mode']],
							'random': 'true', 'name': i['name'].replace('Anime', 'Anime Random'), 'menu_type': 'tvshow'}) for i in a_list if 'random_support' in i]

	def random_because_you_watched_lists(self):
		return [
			{'mode': 'random.build_movie_list', 'action': 'because_you_watched', 'name': 'Random Because You Watched Movies', 'iconImage': 'movies', 'random': 'true'},
			{'mode': 'random.build_tvshow_list', 'action': 'because_you_watched', 'name': 'Random Because You Watched TV Shows', 'iconImage': 'tv', 'random': 'true'},
				]
	
	def random_tmdb_lists(self):
		return [
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'watchlist', 'media_type': 'movie', 'name': 'Random TMDb Movie Watchlist', 'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'watchlist', 'media_type': 'tv', 'name': 'Random TMDb TV Show Watchlist', 'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'favorites', 'media_type': 'movie', 'name': 'Random TMDb Movie Favorites', 'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'favorites', 'media_type': 'tv', 'name': 'Random TMDb TV Show Favorites', 'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'recommendations', 'media_type': 'movie', 'name': 'Random TMDb Movie Recommendations',
			'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'random.build_tmdb_lists_contents', 'list_id': 'recommendations', 'media_type': 'tv', 'name': 'Random TMDb TV Show Recommendations',
			'iconImage': 'tmdb', 'random': 'true'},
			{'mode': 'tmdblist.get_tmdb_lists', 'name': 'Random Shuffled TMDb My Lists (All)', 'iconImage': 'tmdb', 'random': 'true', 'shuffle': 'true'},
			{'mode': 'random.build_tmdb_lists', 'name': 'Random TMDb My Lists (Single)', 'iconImage': 'tmdb', 'random': 'true'}
				]
	
	def random_personal_lists(self):
		return [
			{'mode': 'personal_lists.get_personal_lists', 'name': 'Random Shuffled Personal Lists (All)', 'iconImage': 'lists', 'random': 'true', 'shuffle': 'true'},
			{'mode': 'random.build_personal_lists', 'name': 'Random Personal Lists (Single)', 'iconImage': 'lists', 'random': 'true'}
				]

	def random_trakt_lists_personal(self):
		return [
			{'mode': 'random.build_movie_list', 'action': 'trakt_collection_lists', 'name': 'Random Trakt Movie Collection', 'iconImage': 'movies', 'random': 'true'},
			{'mode': 'random.build_tvshow_list', 'action': 'trakt_collection_lists', 'name': 'Random Trakt TV Show Collection', 'iconImage': 'tv', 'random': 'true'},
			{'mode': 'random.build_movie_list', 'action': 'trakt_watchlist_lists', 'name': 'Random Trakt Movie Watchlist', 'iconImage': 'movies', 'random': 'true'},
			{'mode': 'random.build_tvshow_list', 'action': 'trakt_watchlist_lists', 'name': 'Random Trakt TV Show Watchlist', 'iconImage': 'tv', 'random': 'true'},
			{'mode': 'random.build_movie_list', 'action': 'trakt_recommendations', 'new_page': 'movies', 'name': 'Random Trakt Recommended Movies',
			'iconImage': 'movies', 'random': 'true'},
			{'mode': 'random.build_tvshow_list', 'action': 'trakt_recommendations', 'new_page': 'shows', 'name': 'Random Trakt Recommended TV Shows',
			'iconImage': 'tv', 'random': 'true'},
			{'mode': 'trakt.list.get_trakt_lists', 'list_type': 'my_lists', 'name': 'Random Shuffled Trakt My Lists (All)',
			'iconImage': 'trakt', 'random': 'true', 'shuffle': 'true'},
			{'mode': 'random.build_trakt_lists', 'list_type': 'my_lists', 'name': 'Random Trakt My Lists (Single)', 'iconImage': 'trakt', 'random': 'true'},
			{'mode': 'trakt.list.get_trakt_lists', 'list_type': 'liked_lists', 'name': 'Random Shuffled Trakt Liked Lists (All)',
			'iconImage': 'trakt', 'random': 'true', 'shuffle': 'true'},
			{'mode': 'random.build_trakt_lists', 'list_type': 'liked_lists', 'name': 'Random Trakt Liked Lists (Single)', 'iconImage': 'trakt', 'random': 'true'},
				]

	def random_trakt_lists_public(self):
		return [
			{'mode': 'trakt.list.get_trakt_user_lists', 'list_type': 'trending', 'category_name': 'Random Trending User Lists', 'name': 'Random Trending User Lists (All)',
			'iconImage': 'trakt', 'random': 'true'},
			{'mode': 'random.build_trakt_lists', 'list_type': 'trending', 'category_name': 'Random Trending User Lists', 'name': 'Random Trending User Lists (Single)',
			'iconImage': 'trakt', 'random': 'true'},
			{'mode': 'trakt.list.get_trakt_user_lists', 'list_type': 'popular', 'category_name': 'Random Popular User Lists', 'name': 'Random Popular User Lists (All)',
			'iconImage': 'trakt', 'random': 'true'},
			{'mode': 'random.build_trakt_lists', 'list_type': 'popular', 'category_name': 'Random Popular User Lists', 'name': 'Random Popular User Lists (Single)',
			'iconImage': 'trakt', 'random': 'true'}
				]

navigator_cache = NavigatorCache()
