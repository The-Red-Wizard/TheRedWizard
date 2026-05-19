# -*- coding: utf-8 -*-
from caches.debrid_cache import debrid_cache
from apis.real_debrid_api import RealDebridAPI
from apis.premiumize_api import PremiumizeAPI
from apis.alldebrid_api import AllDebridAPI
from apis.torbox_api import TorBoxAPI
from modules.source_utils import get_external_cache_status
from modules.kodi_utils import show_busy_dialog, hide_busy_dialog, notification
from modules.settings import enabled_debrids_check
# from modules.kodi_utils import logger

def debrid_enabled():
	return [
	i[0] for i in [('Real-Debrid', 'rd'), ('Premiumize.me', 'pm'), ('AllDebrid', 'ad'), ('TorBox', 'tb')] if enabled_debrids_check(i[1])]

def debrid_for_ext_cache_check(enabled_debrid=None):
	if not enabled_debrid: enabled_debrid = debrid_enabled()
	return any(i in ['Real-Debrid', 'AllDebrid'] for i in enabled_debrid)

def manual_add_magnet_to_cloud(params):
	show_busy_dialog()
	debrid_list_modules = [('Real-Debrid', RealDebridAPI), ('Premiumize.me', PremiumizeAPI), ('AllDebrid', AllDebridAPI), ('TorBox', TorBoxAPI)]
	function = [i[1] for i in debrid_list_modules if i[0] == params['provider']][0]
	result = function().create_transfer(params['magnet_url'])
	function().clear_cache()
	hide_busy_dialog()
	if result == 'failed': notification('Failed')
	else: notification('Success')

def query_local_cache(hash_list):
	return debrid_cache.get_many(hash_list) or []

def add_to_local_cache(hash_list, debrid, expires=24):
	debrid_cache.set_many(hash_list, debrid, expires)

def cached_check(hash_list, cached_hashes, debrid):
	cached_list = [i[0] for i in cached_hashes if i[1] == debrid and i[2] == 'True']
	unchecked_list = [i for i in hash_list if not any([h for h in cached_hashes if h[0] == i and h[1] == debrid])]
	return cached_list, unchecked_list

def RD_check(hash_list, cached_hashes, data, active_debrid):
	expires = 24
	cached_hashes, unchecked_hashes = cached_check(hash_list, cached_hashes, 'rd')
	if unchecked_hashes:
		results = get_external_cache_status('Real-Debrid', unchecked_hashes, data, active_debrid)
		if results:
			cached_append = cached_hashes.append
			process_list = []
			process_append = process_list.append
			try:
				for h in unchecked_hashes:
					cached = 'False'
					if h in results:
						cached_append(h)
						cached = 'True'
					process_append((h, cached))
			except:
				for i in unchecked_hashes: process_append((i, 'False'))
		else: process_list, expires  = [(h, 'False') for h in unchecked_hashes], 2
		add_to_local_cache(process_list, 'rd', expires)
	return cached_hashes

def AD_check(hash_list, cached_hashes, data, active_debrid):
	expires = 24
	cached_hashes, unchecked_hashes = cached_check(hash_list, cached_hashes, 'ad')
	if unchecked_hashes:
		results = get_external_cache_status('AllDebrid', unchecked_hashes, data, active_debrid)
		if results:
			cached_append = cached_hashes.append
			process_list = []
			process_append = process_list.append
			try:
				for h in unchecked_hashes:
					cached = 'False'
					if h in results:
						cached_append(h)
						cached = 'True'
					process_append((h, cached))
			except:
				for i in unchecked_hashes: process_append((i, 'False'))
		else: process_list, expires  = [(h, 'False') for h in unchecked_hashes], 2
		add_to_local_cache(process_list, 'ad', expires)
	return cached_hashes

def PM_check(hash_list, cached_hashes):
	expires = 24
	cached_hashes, unchecked_hashes = cached_check(hash_list, cached_hashes, 'pm')
	if unchecked_hashes:
		results = PremiumizeAPI().check_cache(unchecked_hashes)
		if results:
			cached_append = cached_hashes.append
			process_list = []
			process_append = process_list.append
			try:
				results = results['response']
				for c, h in enumerate(unchecked_hashes):
					cached = 'False'
					try:
						if results[c] is True:
							cached_append(h)
							cached = 'True'
					except: pass
					process_append((h, cached))
			except:
				for i in unchecked_hashes: process_append((i, 'False'))
		else: process_list, expires  = [(h, 'False') for h in unchecked_hashes], 2
		add_to_local_cache(process_list, 'pm', expires)
	return cached_hashes

def TB_check(hash_list, cached_hashes):
	expires = 24
	cached_hashes, unchecked_hashes = cached_check(hash_list, cached_hashes, 'tb')
	if unchecked_hashes:
		results = TorBoxAPI().check_cache(unchecked_hashes)
		if results:
			cached_append = cached_hashes.append
			process_list = []
			process_append = process_list.append
			try:
				data = results['data']
				results = [i['hash'] for i in data]
				for h in unchecked_hashes:
					cached = 'False'
					if h in results:
						cached_append(h)
						cached = 'True'
					process_append((h, cached))
			except:
				for i in unchecked_hashes: process_append((i, 'False'))
		else: process_list, expires  = [(h, 'False') for h in unchecked_hashes], 2
		add_to_local_cache(process_list, 'tb', expires)
	return cached_hashes
