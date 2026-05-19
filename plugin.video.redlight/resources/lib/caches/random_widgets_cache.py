# -*- coding: utf-8 -*-
from caches.base_cache import BaseCache, get_timestamp
# from modules.kodi_utils import logger

class RandomWidgets(BaseCache):
	def __init__(self):
		BaseCache.__init__(self, 'random_widgets_db', 'random_widgets')

	def clean_database(self):
		try:
			dbcon = self.manual_connect('random_widgets_db')
			dbcon.execute('DELETE from data WHERE CAST(expires AS INT) <= ?', (get_timestamp(),))
			dbcon.execute('VACUUM')
			return True
		except: return False