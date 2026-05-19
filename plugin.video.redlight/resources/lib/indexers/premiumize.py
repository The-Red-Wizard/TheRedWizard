# -*- coding: utf-8 -*-
import re
import sys
import math
from datetime import datetime
from apis.premiumize_api import Premiumize
from modules.source_utils import supported_video_extensions
from modules.utils import clean_file_name, normalize
from modules import kodi_utils
# logger = kodi_utils.logger

def pm_cloud(folder_id=None, folder_name=None):
	def _builder():
		for count, item in enumerate(cloud_files, 1):
			try:
				cm = []
				cm_append = cm.append
				file_type = item['type']
				name = clean_file_name(item['name']).upper()
				rename_params = {'mode': 'premiumize.rename', 'file_type': file_type, 'id': item['id'], 'name': item['name']}
				delete_params = {'mode': 'premiumize.delete', 'id': item['id']}
				listitem = kodi_utils.make_listitem()
				if file_type == 'folder':
					is_folder = True
					display = '%02d | [B]FOLDER[/B] | [I]%s [/I]' % (count, name)
					url_params = {'mode': 'premiumize.pm_cloud', 'id': item['id'], 'folder_name': normalize(item['name']), 'name': item['name']}
					delete_params['file_type'] = 'folder'
				else:
					is_folder = False
					url_link, size = item['link'], item['size']
					if url_link.startswith('/'): url_link = 'https' + url_link
					display_size = float(int(size))/1073741824
					display = '%02d | [B]FILE[/B] | %.2f GB | [I]%s [/I]' % (count, display_size, name)
					url_params = {'mode': 'playback.video', 'url': url_link, 'obj': 'video'}
					down_file_params = {'mode': 'downloader.runner', 'name': item['name'], 'url': url_link, 'action': 'cloud.premiumize', 'image': icon}
					delete_params['file_type'] = 'item'
					cm_append(('[B]Download File[/B]', 'RunPlugin(%s)' % kodi_utils.build_url(down_file_params)))
				cm_append(('[B]Rename %s[/B]' % file_type.capitalize(),'RunPlugin(%s)' % kodi_utils.build_url(rename_params)))
				cm_append(('[B]Delete %s[/B]' % file_type.capitalize(),'RunPlugin(%s)' % kodi_utils.build_url(delete_params)))
				url = kodi_utils.build_url(url_params)
				listitem.setLabel(display)
				listitem.addContextMenuItems(cm)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				yield (url, listitem, is_folder)
			except: pass
	icon, fanart = kodi_utils.get_icon('premiumize'), kodi_utils.get_addon_fanart()
	try:
		cloud_files = Premiumize.user_cloud(folder_id)['content']
		cloud_files = [i for i in cloud_files if ('link' in i and i['link'].lower().endswith(tuple(supported_video_extensions()))) or i['type'] == 'folder']
		cloud_files.sort(key=lambda k: k['name'])
		cloud_files.sort(key=lambda k: k['type'], reverse=True)
	except: cloud_files = []
	handle = int(sys.argv[1])
	kodi_utils.add_items(handle, list(_builder()))
	kodi_utils.set_content(handle, 'files')
	kodi_utils.end_directory(handle, cacheToDisc=False)
	kodi_utils.set_view_mode('view.premium')

def pm_transfers():
	def _builder():
		for count, item in enumerate(transfer_files, 1):
			try:
				cm = []
				file_id, status, progress, name = item['file_id'], item['status'], item['progress'], clean_file_name(item['name']).upper()
				file_type = 'folder' if file_id is None else 'file'
				if status == 'finished': progress = 100
				else:
					try: progress = re.findall(r'\.{0,1}(\d+)', str(progress))[0][:2]
					except: progress = ''
				if file_type == 'folder':
					is_folder = True if status == 'finished' else False
					display = '%02d | %s%% | [B]FOLDER[/B] | [I]%s [/I]' % (count, str(progress), name)
					url_params = {'mode': 'premiumize.pm_cloud', 'id': item['folder_id'], 'folder_name': normalize(item['name'])}
				else:
					is_folder = False
					details = Premiumize.get_item_details(file_id)
					url_link, size = details['link'], details['size']
					if url_link.startswith('/'): url_link = 'https' + url_link
					display_size = float(int(size))/1073741824
					display = '%02d | %s%% | [B]FILE[/B] | %.2f GB | [I]%s [/I]' % (count, str(progress), display_size, name)
					url_params = {'mode': 'playback.video', 'url': url_link, 'obj': 'video'}
					down_file_params = {'mode': 'downloader.runner', 'name': item['name'], 'url': url_link, 'media_type': 'cloud.premiumize', 'image': icon}
					cm.append(('[B]Download File[/B]','RunPlugin(%s)' % kodi_utils.build_url(down_file_params)))
				url = kodi_utils.build_url(url_params)
				listitem = kodi_utils.make_listitem()
				listitem.setLabel(display)
				listitem.addContextMenuItems(cm)
				listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanart, 'banner': icon})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				yield (url, listitem, is_folder)
			except: pass
	icon, fanart = kodi_utils.get_icon('premiumize'), kodi_utils.get_addon_fanart()
	try: transfer_files = Premiumize.transfers_list()['transfers']
	except: transfer_files = []
	handle = int(sys.argv[1])
	kodi_utils.add_items(handle, list(_builder()))
	kodi_utils.set_content(handle, 'files')
	kodi_utils.end_directory(handle, cacheToDisc=False)
	kodi_utils.set_view_mode('view.premium')

def pm_rename(file_type, file_id, current_name):
	new_name = kodi_utils.kodi_dialog().input('RedLight', defaultt=current_name)
	if not new_name: return
	result = Premiumize.rename_cache_item(file_type, file_id, new_name)
	if result == 'success':
		Premiumize.clear_cache()
		execute_builtin('Container.Refresh')
	else:
		return kodi_utils.ok_dialog(text='Error')

def pm_delete(file_type, file_id):
	if not kodi_utils.confirm_dialog(): return
	result = Premiumize.delete_object(file_type, file_id)
	if result == 'success':
		Premiumize.clear_cache()
		execute_builtin('Container.Refresh')
	else:
		return kodi_utils.ok_dialog(text='Error')

def pm_account_info():
	try:
		kodi_utils.show_busy_dialog()
		account_info = Premiumize.account_info()
		customer_id = account_info['customer_id']
		expires = datetime.fromtimestamp(account_info['premium_until'])
		days_remaining = (expires - datetime.today()).days
		points_used = int(math.floor(float(account_info['space_used']) / 1073741824.0))
		space_used = float(int(account_info['space_used']))/1073741824
		percentage_used = str(round(float(account_info['limit_used']) * 100.0, 1))
		body = []
		append = body.append
		append('[B]Customer ID:[/B] %s' % customer_id)
		append('[B]Expires:[/B] %s' % expires)
		append('[B]Days Remaining:[/B] %s' % days_remaining)
		append('[B]Points Used:[/B] %.f' % points_used)
		append('[B]Space Used:[/B] %.2f' % space_used)
		append('[B]Fair Use (Percentage Used):[/B] %s%%' % percentage_used)
		kodi_utils.hide_busy_dialog()
		return kodi_utils.show_text('PREMIUMIZE', '\n\n'.join(body), font_size='large')
	except: kodi_utils.hide_busy_dialog()


def active_days():
	try:
		account_info = Premiumize.account_info()
		expires = datetime.fromtimestamp(account_info['premium_until'])
		days_remaining = (expires - datetime.today()).days
	except: days_remaining = 0
	return days_remaining