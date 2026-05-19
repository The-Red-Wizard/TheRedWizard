# -*- coding: utf-8 -*-
from caches.base_cache import BaseCache, get_timestamp
from modules.kodi_utils import logger

class TMDbListsCache(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, 'tmdb_lists_db', 'tmdb_lists')

	def clear_all_lists(self):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('DELETE FROM tmdb_lists WHERE id = ?', ('get_user_lists',))
			dbcon.execute('VACUUM')
			return True
		except: return False

	def clear_list(self, list_id):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('DELETE FROM tmdb_lists WHERE id = ?', ('get_list_details_%s' % list_id,))
			dbcon.execute('VACUUM')
			return True
		except: return False

	def clear_watchfavrecs(self, list_id, media_type):
		try:
			string = 'get_watchfavrecs_list_details_%s_%s' % (list_id, media_type)
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('DELETE FROM tmdb_lists WHERE id = ?', (string,))
			dbcon.execute('VACUUM')
			return True
		except: return False

	def clear_all(self):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('DELETE FROM tmdb_lists WHERE id = ?', ('get_user_lists',))
			dbcon.execute('DELETE FROM tmdb_lists WHERE id LIKE %s' % "'get_list_details_%'")
			dbcon.execute('DELETE FROM tmdb_lists WHERE id LIKE %s' % "'get_watchfavrecs_list_details_%'")
			dbcon.execute('VACUUM')
			return True
		except: return False

	def clean_database(self):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('DELETE from tmdb_lists WHERE CAST(expires AS INT) <= ?', (get_timestamp(),))
			dbcon.execute('VACUUM')
			return True
		except: return False

	def set_sort_order(self, list_id, sort_order):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			dbcon.execute('INSERT OR REPLACE INTO tmdb_lists VALUES (?, ?, ?)', ('sort_order_%s' % list_id, sort_order, 0))
			return True
		except: return False

	def get_sort_orders(self):
		try:
			dbcon = self.manual_connect('tmdb_lists_db')
			cache_data = dbcon.execute('SELECT id, data FROM tmdb_lists WHERE id LIKE %s' % "'sort_order_%'").fetchall()
			cache_data = dict([(int(i[0].replace('sort_order_', '')), i[1]) for i in cache_data])
			return cache_data
		except: return {}

tmdb_lists_cache = TMDbListsCache()

def tmdb_lists_cache_object(function, string, args, json=False, expiration=24):
	cache = tmdb_lists_cache.get(string)
	if cache is not None: return cache
	if isinstance(args, list): args = tuple(args)
	else: args = (args,)
	if json: result = function(*args).json()
	else: result = function(*args)
	tmdb_lists_cache.set(string, result, expiration=expiration)
	return result