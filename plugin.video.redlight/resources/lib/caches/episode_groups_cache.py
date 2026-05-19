# -*- coding: utf-8 -*-
from caches.base_cache import connect_database
# from modules.kodi_utils import logger

class EpisodeGroupsCache:
	def get(self, tmdb_id):
		try: data = eval(connect_database('episode_groups_db').execute('SELECT data FROM groups_data WHERE tmdb_id = ?', (str(tmdb_id),)).fetchone()[0])
		except: data = {}
		return data

	def set(self, tmdb_id, data):
		connect_database('episode_groups_db').execute('INSERT OR REPLACE INTO groups_data VALUES (?, ?)', (str(tmdb_id), repr(data)))

	def delete(self, tmdb_id):
		dbcon = connect_database('episode_groups_db')
		dbcon.execute('DELETE FROM groups_data where tmdb_id=?', (str(tmdb_id),))
		dbcon.execute('VACUUM')

	def clear_cache(self):
		dbcon = connect_database('episode_groups_db')
		dbcon.execute('DELETE FROM groups_data')
		dbcon.execute('VACUUM')

episode_groups_cache = EpisodeGroupsCache()
