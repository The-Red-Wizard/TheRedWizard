# -*- coding: utf-8 -*-
import sys
from datetime import datetime
from urllib.parse import unquote, urlencode, quote
from modules.settings import easynews_playback_method
from modules.utils import jsondate_to_datetime
from apis.easynews_api import EasyNews
from indexers.images import Images
from modules import kodi_utils
from modules.utils import clean_file_name
# logger = kodi_utils.logger

def search_easynews_image(key_id=None):
	return Images().run({'mode': 'easynews_image_results', 'key_id': unquote(key_id), 'page_no': 1})

def search_easynews(params):
	handle = int(sys.argv[1])
	key_id = params.get('key_id') or params.get('query')
	search_name = clean_file_name(unquote(key_id))
	try:
		files = EasyNews.search(search_name)
		easynews_file_browser(files, handle)
	except: pass
	kodi_utils.set_content(handle, 'files')
	kodi_utils.end_directory(handle, cacheToDisc=False)
	kodi_utils.set_view_mode('view.premium')

def easynews_file_browser(files, handle):
	def _builder():
		for count, item in enumerate(files, 1):
			try:
				cm = []
				item_get = item.get
				width = item_get('width', 0)
				if width > 1920: display_res = '4K'
				elif 1280 < width <= 1920: display_res = '1080P'
				elif 720 < width <= 1280: display_res = '720P'
				else: display_res = 'SD'
				name = clean_file_name(item_get('name')).upper()
				url_dl = item_get('url_dl')
				down_url = item_get('down_url', url_dl)
				size = str(round(float(int(item_get('rawSize')))/1048576000, 1))
				length = item_get('runtime', '0')
				display = '%02d | [B]%s[/B] | [B]%sGB | %sMINS | [/B][I]%s [/I]' % (count, display_res, size, length, name)
				url_params = {'mode': 'easynews.resolve_easynews', 'action': 'cloud.easynews_direct', 'name': name, 'url': down_url,
								'url_dl': url_dl, 'image': icon, 'play': 'true'}
				url = kodi_utils.build_url(url_params)
				down_file_params = {'mode': 'downloader.runner', 'name': name, 'url': down_url, 'action': 'cloud.easynews_direct', 'image': icon}
				cm.append(('[B]Download File[/B]', 'RunPlugin(%s)' % kodi_utils.build_url(down_file_params)))
				listitem = kodi_utils.make_listitem()
				listitem.setLabel(display)
				listitem.addContextMenuItems(cm)
				thumbnail = item_get('thumbnail', icon)
				listitem.setArt({'icon': thumbnail, 'poster': thumbnail, 'thumb': thumbnail, 'fanart': fanart, 'banner': icon})
				info_tag = listitem.getVideoInfoTag(True)
				info_tag.setPlot(' ')
				yield (url, listitem, False)
			except: pass
	icon = kodi_utils.get_icon('easynews')
	fanart = kodi_utils.get_addon_fanart()
	kodi_utils.add_items(handle, list(_builder()))

def resolve_easynews(params):
	direct_play = params.get('play', 'false') == 'true'
	query = 'direct_play' if direct_play else 'non_seek'
	use_non_seekable = easynews_playback_method(query)
	resolved_link = EasyNews.resolve_easynews(params['url_dl'], use_non_seekable)
	if not direct_play: return resolved_link
	from modules.player import RedLightPlayer
	RedLightPlayer().run(resolved_link, 'video')

def account_info(params):
	try:
		kodi_utils.show_busy_dialog()
		account_info, usage_info = EasyNews.account()
		if not account_info or not usage_info: return kodi_utils.ok_dialog(text='Error')
		body = []
		append = body.append
		expires = jsondate_to_datetime(account_info[2], '%Y-%m-%d')
		days_remaining = (expires - datetime.today()).days
		append('[B]Account:[/B] %s' % account_info[1])
		append('[B]Username:[/B] %s' % account_info[0])
		append('[B]Status:[/B] %s' % account_info[3])
		append('[B]Expires:[/B] %s' % expires)
		append('[B]Days Remaining:[/B] %s' % days_remaining)
		append('[B]Current Subscription:[/B] %s' % usage_info[2])
		append('[B]Data Used:[/B] %s' % usage_info[0].replace('Gigs', 'GB'))
		append('[B]Data Remaining:[/B] %s' % usage_info[1].replace('Gigs', 'GB'))
		kodi_utils.hide_busy_dialog()
		return kodi_utils.show_text('EASYNEWS', '\n\n'.join(body), font_size='large')
	except: kodi_utils.hide_busy_dialog()

def active_days():
	try:
		account_info = EasyNews.account_info()
		expires = jsondate_to_datetime(account_info[2], '%Y-%m-%d')
		days_remaining = (expires - datetime.today()).days
	except: days_remaining = 0
	return days_remaining
