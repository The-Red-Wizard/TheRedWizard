# -*- coding: utf-8 -*-
import time
import requests
from datetime import datetime, timezone
from threading import Thread
from urllib.parse import urlencode
from caches.settings_cache import get_setting, set_setting
from caches.main_cache import cache_object
from modules.source_utils import supported_video_extensions, seas_ep_filter, extras
from modules.utils import copy2clip, make_qrcode
from modules.kodi_utils import make_session, ok_dialog, notification, confirm_dialog, progress_dialog, sleep
# from modules.kodi_utils import logger

base_url = 'https://api.torbox.app/v1/api/'
session = make_session(base_url)


def _to_int(value, default=0):
	try: return int(str(value).strip())
	except Exception: return default


def _device_auth_url(app_name, user_code):
	return 'https://torbox.app/oauth/device?%s' % urlencode({'app': app_name, 'code': user_code})


def _extract_device_token(response):
	if not response or not response.get('success'):
		return None
	data = response.get('data')
	if isinstance(data, str) and data.strip():
		return data.strip()
	if isinstance(data, dict):
		for key in ('token', 'api_token', 'api_key', 'access_token'):
			value = data.get(key)
			if value:
				return str(value).strip()
	return None


def _device_auth_poll_pending(response):
	if not response:
		return True
	if response.get('success'):
		return not _extract_device_token(response)
	error = (response.get('error') or '').upper()
	if error in ('ITEM_NOT_FOUND', 'DEVICE_CODE_EXPIRED', 'DEVICE_CODE_INVALID', 'INVALID_DEVICE_CODE'):
		return False
	return True


class TorBoxAPI:
	def __init__(self):
		self.token = get_setting('redlight.tb.token')

	def _safe_json(self, response):
		try: return response.json()
		except Exception: return None

	def _get(self, url, data=None):
		if self.token in ('empty_setting', '', None): return None
		try:
			headers = {'Authorization': 'Bearer %s' % self.token}
			response = session.get(base_url + url, params=data or {}, headers=headers, timeout=20)
			return self._safe_json(response)
		except Exception: return None

	def _post(self, url, params=None, json=None, data=None, files=None):
		if self.token in ('empty_setting', '', None) and 'token' not in url: return None
		try:
			headers = {'Authorization': 'Bearer %s' % self.token}
			response = session.post(base_url + url, params=params, json=json, data=data, files=files, headers=headers, timeout=30)
			return self._safe_json(response)
		except Exception: return None

	def add_headers_to_url(self, url):
		return url + '|' + urlencode({'User-Agent': 'Mozilla/5.0'})

	def account_info(self):
		return self._get('user/me')

	# ----------- USER CLOUD LISTS -----------
	def user_cloud(self):
		string = 'tb_user_cloud'
		url = 'torrents/mylist'
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_usenet(self):
		string = 'tb_user_cloud_usenet'
		url = 'usenet/mylist'
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_webdl(self):
		string = 'tb_user_cloud_webdl'
		url = 'webdl/mylist'
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_info(self, request_id=''):
		string = 'tb_user_cloud_%s' % request_id
		url = 'torrents/mylist?id=%s' % request_id
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_info_usenet(self, request_id=''):
		string = 'tb_user_cloud_usenet_%s' % request_id
		url = 'usenet/mylist?id=%s' % request_id
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_info_webdl(self, request_id=''):
		string = 'tb_user_cloud_webdl_%s' % request_id
		url = 'webdl/mylist?id=%s' % request_id
		return cache_object(self._get, string, url, False, 0.03)

	def user_cloud_clear(self):
		if not confirm_dialog(): return
		data = {'all': True, 'operation': 'delete'}
		self._post('torrents/controltorrent', json=data)
		self._post('usenet/controlusenetdownload', json=data)
		self._post('webdl/controlwebdownload', json=data)
		self.clear_cache()

	# ----------- INFO -----------
	def torrent_info(self, request_id=''):
		return self._get('torrents/mylist', data={'id': request_id})

	def usenet_info(self, request_id=''):
		return self._get('usenet/mylist', data={'id': request_id})

	def webdl_info(self, request_id=''):
		return self._get('webdl/mylist', data={'id': request_id})

	# ----------- DELETE -----------
	# TorBox requires the *_id field to be a JSON integer. Cast defensively.
	def delete_torrent(self, request_id=''):
		data = {'torrent_id': _to_int(request_id), 'operation': 'delete'}
		return self._post('torrents/controltorrent', json=data)

	def delete_usenet(self, request_id=''):
		data = {'usenet_id': _to_int(request_id), 'operation': 'delete'}
		return self._post('usenet/controlusenetdownload', json=data)

	def delete_webdl(self, request_id=''):
		data = {'webdl_id': _to_int(request_id), 'operation': 'delete'}
		return self._post('webdl/controlwebdownload', json=data)

	# ----------- UNRESTRICT (request download URL) -----------
	def unrestrict_link(self, file_id):
		try:
			torrent_id, file_id = file_id.split(',')
			params = {'token': self.token, 'torrent_id': _to_int(torrent_id), 'file_id': _to_int(file_id)}
			r = self._get('torrents/requestdl', data=params)
			if r and r.get('success'): return r.get('data')
			return None
		except Exception: return None

	def unrestrict_usenet(self, file_id):
		try:
			usenet_id, file_id = file_id.split(',')
			params = {'token': self.token, 'usenet_id': _to_int(usenet_id), 'file_id': _to_int(file_id)}
			r = self._get('usenet/requestdl', data=params)
			if r and r.get('success'): return r.get('data')
			return None
		except Exception: return None

	def unrestrict_webdl(self, file_id):
		try:
			web_id, file_id = file_id.split(',')
			params = {'token': self.token, 'web_id': _to_int(web_id), 'file_id': _to_int(file_id)}
			r = self._get('webdl/requestdl', data=params)
			if r and r.get('success'): return r.get('data')
			return None
		except Exception: return None

	# ----------- CREATE TRANSFERS -----------
	def add_magnet(self, magnet):
		# TorBox expects multipart-style form fields; lowercase booleans.
		data = {'magnet': magnet, 'seed': '3', 'allow_zip': 'false'}
		return self._post('torrents/createtorrent', data=data)

	def add_webdl(self, link):
		data = {'link': link}
		return self._post('webdl/createwebdownload', data=data)

	# ----------- CACHED CHECK -----------
	def check_cache_single(self, _hash):
		return self._get('torrents/checkcached', data={'hash': _hash, 'format': 'list'})

	def check_cache(self, hashlist):
		return self._post('torrents/checkcached', params={'format': 'list'}, json={'hashes': hashlist})

	def check_cache_webdl(self, hashlist):
		return self._post('webdl/checkcached', params={'format': 'list'}, json={'hashes': hashlist})

	def check_cache_usenet(self, hashlist):
		return self._post('usenet/checkcached', params={'format': 'list'}, json={'hashes': hashlist})

	def create_transfer(self, magnet_url):
		result = self.add_magnet(magnet_url)
		if not result or not result.get('success'): return ''
		return (result.get('data') or {}).get('torrent_id', '')

	def create_webdl_transfer(self, link):
		result = self.add_webdl(link)
		if not result or not result.get('success'): return ''
		return (result.get('data') or {}).get('webdownload_id', '')

	# ----------- RESOLVE -----------
	def resolve_magnet(self, magnet_url, info_hash, store_to_cloud, title, season, episode):
		torrent_id = None
		try:
			extensions = supported_video_extensions()
			extras_filter = extras()
			extras_filtering_list = tuple(i for i in extras_filter if i not in title.lower())
			torrent = self.add_magnet(magnet_url)
			if not torrent or not torrent.get('success'): return None
			torrent_id = torrent['data']['torrent_id']
			torrent_files = self.torrent_info(torrent_id)
			files = torrent_files['data']['files']
			selected_files = [{'url': '%d,%d' % (int(torrent_id), item['id']), 'filename': item['short_name'], 'size': item['size']}
				for item in files if item['short_name'].lower().endswith(tuple(extensions))]
			if not selected_files: return None
			if season:
				selected_files = [i for i in selected_files if seas_ep_filter(season, episode, i['filename'])]
			else:
				if self._m2ts_check(selected_files): return None
				selected_files = [i for i in selected_files if not any(x in i['filename'] for x in extras_filtering_list)]
				selected_files.sort(key=lambda k: k['size'], reverse=True)
			if not selected_files: return None
			file_key = selected_files[0]['url']
			file_url = self.unrestrict_link(file_key)
			if not store_to_cloud: Thread(target=self.delete_torrent, args=(torrent_id,)).start()
			return file_url
		except Exception:
			if torrent_id: self.delete_torrent(torrent_id)
			return None

	def display_magnet_pack(self, magnet_url, info_hash):
		torrent_id = None
		try:
			extensions = supported_video_extensions()
			torrent = self.add_magnet(magnet_url)
			if not torrent or not torrent.get('success'): return None
			torrent_id = torrent['data']['torrent_id']
			torrent_files = self.torrent_info(torrent_id)
			files = torrent_files['data']['files']
			pack_files = [{'link': '%d,%d' % (int(torrent_id), item['id']), 'filename': item['short_name'], 'size': item['size']}
				for item in files if item['short_name'].lower().endswith(tuple(extensions))]
			Thread(target=self.delete_torrent, args=(torrent_id,)).start()
			return pack_files or None
		except Exception:
			if torrent_id: self.delete_torrent(torrent_id)
			return None

	def _m2ts_check(self, folder_items):
		for item in folder_items:
			if item['filename'].endswith('.m2ts'): return True
		return False

	# ----------- AUTH -----------
	def auth(self):
		self.token = ''
		app_name = 'Red Light'
		try:
			response = requests.get(base_url + 'user/auth/device/start', params={'app': app_name}, timeout=20).json()
		except Exception:
			return ok_dialog(text='Unable to start TorBox authorization')
		if not response.get('success'):
			return ok_dialog(text=response.get('detail') or 'Unable to start TorBox authorization')
		data = response.get('data') or {}
		device_code = data.get('device_code')
		user_code = data.get('code')
		if not device_code or not user_code:
			return ok_dialog(text='Invalid TorBox authorization response')
		auth_url = _device_auth_url(app_name, user_code)
		qr_code = make_qrcode(auth_url) or ''
		copy2clip(auth_url)
		p_dialog_insert = '[CR]Full link copied to clipboard[CR]OR visit: [B]torbox.app/oauth/device[/B][CR]AND Enter this Code: [B]%s[/B]' % user_code
		content = 'Please Scan the QR Code%s[CR]' % p_dialog_insert
		progressDialog = progress_dialog('TorBox Authorize', qr_code)
		progressDialog.update(content, 0)
		sleep_interval = int(data.get('interval') or 5)
		try:
			expires_at = data.get('expires_at', '').replace('Z', '+00:00')
			exp = datetime.fromisoformat(expires_at)
			if exp.tzinfo is None:
				exp = exp.replace(tzinfo=timezone.utc)
			expires_in = max(120, int((exp - datetime.now(timezone.utc)).total_seconds()) + 30)
		except Exception:
			expires_in = 900
		poll_url = base_url + 'user/auth/device/token'
		poll_body = {'device_code': device_code, 'code': user_code}
		start, time_passed = time.time(), 0
		sleep(2000)
		while not progressDialog.iscanceled() and time_passed < expires_in and not self.token:
			sleep(1000 * sleep_interval)
			time_passed = time.time() - start
			try:
				poll = requests.post(poll_url, json=poll_body, timeout=20).json()
			except Exception:
				progressDialog.update(content, int(100 * time_passed / float(expires_in)))
				continue
			api_token = _extract_device_token(poll)
			if api_token:
				self.token = api_token
				break
			if not _device_auth_poll_pending(poll):
				break
			progressDialog.update(content, int(100 * time_passed / float(expires_in)))
		try: progressDialog.close()
		except: pass
		if not self.token:
			return
		try:
			set_setting('tb.token', self.token)
			r = self.account_info()
			if not r or not r.get('success'): raise Exception('invalid account')
			set_setting('tb.enabled', 'true')
			ok_dialog(text='Success')
		except Exception:
			set_setting('tb.token', 'empty_setting')
			set_setting('tb.enabled', 'false')
			ok_dialog(text='An Error Occurred')

	def revoke(self):
		if not confirm_dialog(): return
		set_setting('tb.token', 'empty_setting')
		set_setting('tb.enabled', 'false')
		notification('TorBox Authorization Reset', 3000)

	def clear_cache(self, clear_hashes=True):
		try:
			from caches.debrid_cache import debrid_cache
			from caches.base_cache import connect_database
			dbcon = connect_database('maincache_db')
			# USER CLOUD
			try:
				dbcon.execute("""DELETE FROM maincache WHERE id=?""", ('tb_user_cloud',))
				dbcon.execute("""DELETE FROM maincache WHERE id=?""", ('tb_user_cloud_usenet',))
				dbcon.execute("""DELETE FROM maincache WHERE id=?""", ('tb_user_cloud_webdl',))
				dbcon.execute("""DELETE FROM maincache WHERE id LIKE ?""", ('tb_user_cloud%',))
				user_cloud_success = True
			except Exception:
				user_cloud_success = False
			# HASH CACHED STATUS
			if clear_hashes:
				try:
					debrid_cache.clear_debrid_results('tb')
					hash_cache_status_success = True
				except Exception:
					hash_cache_status_success = False
			else:
				hash_cache_status_success = True
		except Exception:
			return False
		if False in (user_cloud_success, hash_cache_status_success): return False
		return True


TorBox = TorBoxAPI()
