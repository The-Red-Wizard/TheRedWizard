# -*- coding: utf-8 -*-
from caches.base_cache import BaseCache, get_timestamp
from modules.settings import lists_cache_duraton
# from modules.kodi_utils import logger

class ListsCache(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, 'lists_db', 'lists')

	def delete_all_lists(self):
		try:
			dbcon = self.manual_connect('lists_db')
			dbcon.execute('DELETE FROM lists WHERE id NOT LIKE %s' % "'ai_%'")
			dbcon.execute('VACUUM')
			return True
		except: return False

	def delete_all_ai_lists(self):
		try:
			dbcon = self.manual_connect('lists_db')
			dbcon.execute('DELETE FROM lists WHERE id LIKE %s' % "'ai_%'")
			dbcon.execute('VACUUM')
			return True
		except: return False

	def clean_database(self):
		try:
			dbcon = self.manual_connect('lists_db')
			dbcon.execute('DELETE from lists WHERE CAST(expires AS INT) <= ?', (get_timestamp(),))
			dbcon.execute('VACUUM')
			return True
		except: return False

lists_cache = ListsCache()

def lists_cache_object(function, string, args, json=False, expiration=None):
	cache = lists_cache.get(string)
	if cache is not None: return cache
	if isinstance(args, list): args = tuple(args)
	else: args = (args,)
	if json: result = function(*args).json()
	else: result = function(*args)
	if result in ([], {}, '[]', '{}', '', None): expiration = 0.3
	else: expiration = expiration or lists_cache_duraton()
	lists_cache.set(string, result, expiration=expiration)
	return result