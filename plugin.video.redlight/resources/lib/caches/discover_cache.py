# -*- coding: utf-8 -*-
from caches.base_cache import connect_database
# from modules.kodi_utils import logger

class DiscoverCache:
	def insert_one(self, _id, db_type, data):
		dbcon = connect_database('discover_db')
		dbcon.execute('INSERT OR REPLACE INTO discover VALUES (?, ?, ?)', (_id, db_type, data))

	def delete_one(self, _id):
		dbcon = connect_database('discover_db')
		dbcon.execute('DELETE FROM discover where id=?', (_id,))
		dbcon.execute('VACUUM')

	def get_all(self, db_type):
		dbcon = connect_database('discover_db')
		all_lists = reversed(dbcon.execute('SELECT * FROM discover WHERE db_type == ?', (db_type,)).fetchall())
		return [{'id': i[0], 'data': i[2]} for i in all_lists]

	def clear_cache(self, db_type):
		dbcon = connect_database('discover_db')
		dbcon.execute('DELETE FROM discover WHERE db_type=?', (db_type,))
		dbcon.execute('VACUUM')

discover_cache = DiscoverCache()
