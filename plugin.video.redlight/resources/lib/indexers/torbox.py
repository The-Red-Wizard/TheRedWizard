import sys
from apis.torbox_api import TorBox
from modules.source_utils import supported_video_extensions
from modules.utils import clean_file_name, normalize
from modules import kodi_utils
# from modules.kodi_utils import logger


def _api_error_text(result, fallback='Error'):
	if not isinstance(result, dict): return fallback
	# TorBox returns: { success, error, detail, data }
	err = result.get('error') or result.get('detail') or fallback
	if isinstance(err, (list, dict)): err = str(err)
	return str(err)


def tb_cloud():
	def _builder():
		for count, item in enumerate(folders, 1):
			try:
				cm = []
				cm_append = cm.append
				media_type = item['media_type']
				label_type = {'torrent': 'TORRENT', 'usenet': 'USENET', 'webdl': 'WEB DL'}.get(media_type, 'FOLDER')
				display = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, label_type, clean_file_name(normalize(item['name'])).upper())
				url_params = {'mode': 'torbox.browse_tb_cloud', 'folder_id': item['id'], 'media_type': media_type}
				delete_params = {'mode': 'torbox.delete', 'folder_id': item['id'], 'media_type': media_type}
				cm_append(('[B]Delete Folder[/B]', 'RunPlugin(%s)' % kodi_utils.build_url(delete_params)))
				url = kodi_utils.build_url(url_params)
				listitem = kodi_utils.make_listitem()
				listitem.setLabel(display)
				listitem.addContextMenuItems(cm)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
				yield (url, listitem, True)
			except Exception:
				pass
	icon, fanart = kodi_utils.get_icon('torbox'), kodi_utils.get_addon_fanart()
	torrents_folders = TorBox.user_cloud() or {'data': []}
	usenets_folders = TorBox.user_cloud_usenet() or {'data': []}
	webdl_folders = TorBox.user_cloud_webdl() or {'data': []}
	t_data = torrents_folders.get('data') or []
	u_data = usenets_folders.get('data') or []
	w_data = webdl_folders.get('data') or []
	folders_torrents = [{**i, 'media_type': 'torrent'} for i in t_data if i.get('download_finished')]
	folders_usenets = [{**i, 'media_type': 'usenet'} for i in u_data if i.get('download_finished')]
	folders_webdl = [{**i, 'media_type': 'webdl'} for i in w_data if i.get('download_finished')]
	folders = folders_torrents + folders_usenets + folders_webdl
	folders.sort(key=lambda k: k.get('updated_at', ''), reverse=True)
	handle = int(sys.argv[1])
	kodi_utils.add_items(handle, list(_builder()))
	kodi_utils.set_content(handle, 'files')
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.premium')


def browse_tb_cloud(folder_id, media_type):
	def _builder():
		for count, item in enumerate(video_files, 1):
			try:
				cm = []
				name = clean_file_name(item['short_name']).upper()
				size = float(int(item['size'])) / 1073741824
				display = '%02d | [B]FILE[/B] | %.2f GB | [I]%s [/I]' % (count, size, name)
				url_link = '%d,%d' % (int(folder_id), item['id'])
				url_params = {'mode': 'torbox.resolve_tb', 'play': 'true', 'url': url_link, 'media_type': item['media_type']}
				down_file_params = {'mode': 'downloader.runner', 'name': name, 'url': url_link, 'media_type': item['media_type'], 'action': 'cloud.torbox', 'image': icon}
				cm.append(('[B]Download File[/B]', 'RunPlugin(%s)' % kodi_utils.build_url(down_file_params)))
				url = kodi_utils.build_url(url_params)
				listitem = kodi_utils.make_listitem()
				listitem.setLabel(display)
				listitem.addContextMenuItems(cm)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
				listitem.setInfo('video', {})
				yield (url, listitem, False)
			except Exception:
				pass
	if media_type == 'torrent': files = TorBox.user_cloud_info(folder_id)
	elif media_type == 'webdl': files = TorBox.user_cloud_info_webdl(folder_id)
	else: files = TorBox.user_cloud_info_usenet(folder_id)
	if not files or not files.get('success') or not isinstance(files.get('data'), dict):
		kodi_utils.notification('TorBox: %s' % _api_error_text(files, 'Failed to load folder'))
		handle = int(sys.argv[1])
		kodi_utils.end_directory(handle)
		return
	data_files = (files.get('data') or {}).get('files') or []
	video_files = [{**i, 'media_type': media_type} for i in data_files if i.get('short_name', '').lower().endswith(tuple(supported_video_extensions()))]
	icon, fanart = kodi_utils.get_icon('torbox'), kodi_utils.get_addon_fanart()
	handle = int(sys.argv[1])
	kodi_utils.add_items(handle, list(_builder()))
	kodi_utils.set_content(handle, 'files')
	kodi_utils.end_directory(handle)
	kodi_utils.set_view_mode('view.premium')


def tb_delete(folder_id, media_type):
	if not kodi_utils.confirm_dialog(): return
	if media_type == 'torrent': result = TorBox.delete_torrent(folder_id)
	elif media_type == 'webdl': result = TorBox.delete_webdl(folder_id)
	else: result = TorBox.delete_usenet(folder_id)
	if not result or not result.get('success'):
		return kodi_utils.notification('TorBox: %s' % _api_error_text(result, 'Delete failed'), 4000)
	TorBox.clear_cache()
	kodi_utils.notification('TorBox: Deleted', 2500)
	kodi_utils.execute_builtin('Container.Refresh')


def resolve_tb(params):
	file_id, media_type = params['url'], params['media_type']
	if media_type == 'torrent': resolved_link = TorBox.unrestrict_link(file_id)
	elif media_type == 'webdl': resolved_link = TorBox.unrestrict_webdl(file_id)
	else: resolved_link = TorBox.unrestrict_usenet(file_id)
	if not resolved_link:
		kodi_utils.notification('TorBox: Unable to resolve link', 4000)
		return None
	if params.get('play', 'false') != 'true': return resolved_link
	from modules.player import RedLightPlayer
	RedLightPlayer().run(resolved_link, 'video')


def tb_send_webdl():
	url = kodi_utils.kodi_dialog().input('Paste URL to send to TorBox WebDL:').strip()
	if not url: return
	if not (url.startswith('http://') or url.startswith('https://') or url.startswith('magnet:')):
		return kodi_utils.ok_dialog(text='Invalid URL. Must start with http://, https:// or magnet:')
	kodi_utils.show_busy_dialog()
	try:
		if url.startswith('magnet:'):
			result = TorBox.add_magnet(url)
			kind = 'Torrent'
		else:
			result = TorBox.add_webdl(url)
			kind = 'WebDL'
	except Exception:
		result, kind = None, '?'
	kodi_utils.hide_busy_dialog()
	if result and result.get('success'):
		TorBox.clear_cache()
		detail = result.get('detail') or 'Submitted'
		kodi_utils.notification('TorBox %s: %s' % (kind, detail), 4000)
		kodi_utils.execute_builtin('Container.Refresh')
	else:
		kodi_utils.ok_dialog(text='TorBox: %s' % _api_error_text(result, 'Failed to submit to TorBox'))


def tb_account_info():
	try:
		kodi_utils.show_busy_dialog()
		plans = {0: 'Free plan', 1: 'Essential plan', 2: 'Pro plan', 3: 'Standard plan'}
		account_info = TorBox.account_info()
		if not account_info or not account_info.get('success'):
			kodi_utils.hide_busy_dialog()
			return kodi_utils.ok_dialog(text='TorBox: %s' % _api_error_text(account_info, 'Unable to load account info'))
		account_info = account_info['data']
		body = []
		append = body.append
		append('[B]Email[/B]: %s' % account_info.get('email', ''))
		append('[B]Customer[/B]: %s' % account_info.get('customer', ''))
		append('[B]Plan[/B]: %s' % plans.get(account_info.get('plan'), 'Unknown'))
		append('[B]Expires[/B]: %s' % account_info.get('premium_expires_at', ''))
		append('[B]Downloaded[/B]: {:,}'.format(account_info.get('total_downloaded', 0)))
		kodi_utils.hide_busy_dialog()
		return kodi_utils.show_text('TorBox'.upper(), '\n\n'.join(body), font_size='large')
	except Exception:
		kodi_utils.hide_busy_dialog()
