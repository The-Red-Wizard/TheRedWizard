# -*- coding: utf-8 -*-
import re
import json
import base64
import time
import requests
from threading import Thread
from urllib.parse import unquote, unquote_plus
from caches.settings_cache import get_setting
from modules.metadata import episodes_meta
from modules.settings import date_offset
from modules.kodi_utils import supported_media, get_property, set_property, notification
from modules.utils import adjust_premiered_date, get_datetime, jsondate_to_datetime, subtract_dates, chunks
# from modules.kodi_utils import logger

def extras():
	return ('sample', 'extra', 'extras', 'deleted', 'unused', 'footage', 'inside', 'blooper', 'bloopers',
			'making.of', 'feature', 'featurette', 'behind.the.scenes', 'trailer')

def unwanted_tags():
	return (
'tamilrockers.com', 'www.tamilrockers.com', 'www.tamilrockers.ws', 'www.tamilrockers.pl', 'www-tamilrockers-cl', 'www.tamilrockers.cl', 'www.tamilrockers.li',
'www.tamilrockerrs.pl', 'www.tamilmv.bid', 'www.tamilmv.biz', 'www.1tamilmv.org', 'gktorrent-bz', 'gktorrent-com', 'www.torrenting.com', 'www.torrenting.org',
'www-torrenting-com', 'www-torrenting-org', 'katmoviehd.pw', 'katmoviehd-pw', 'www.torrent9.nz', 'www-torrent9-uno', 'torrent9-cz', 'torrent9.cz',
'agusiq-torrents-pl', 'oxtorrent-bz', 'oxtorrent-com', 'oxtorrent.com', 'oxtorrent-sh', 'oxtorrent-vc', 'www.movcr.tv', 'movcr-com', 'www.movcr.to', '(imax)',
'imax', 'xtorrenty.org', 'nastoletni.wilkoak', 'www.scenetime.com', 'kst-vn', 'www.movierulz.vc', 'www-movierulz-ht', 'www.2movierulz.ac', 'www.2movierulz.ms',
'www.3movierulz.com', 'www.3movierulz.tv', 'www.3movierulz.ws', 'www.3movierulz.ms', 'www.7movierulz.pw', 'www.8movierulz.ws', 'mkvcinemas.live', 'www.bludv.tv',
'ramin.djawadi', 'extramovies.casa', 'extramovies.wiki', '13+', '18+', 'taht.oyunlar', 'crazy4tv.com', 'karibu', '989pa.com', 'best-torrents-net', '1-3-3-8.com',
'ssrmovies.club', 'va:', 'zgxybbs-fdns-uk', 'www.tamilblasters.mx', 'www.1tamilmv.work', 'www.xbay.me', 'crazy4tv-com', '(es)')

def audio_filter_choices():
	return (
('DOLBY DIGITAL', 'DD'), ('DOLBY DIGITAL PLUS', 'DD+'), ('DOLBY DIGITAL EX', 'DD-EX'), ('DOLBY ATMOS', 'ATMOS'), ('DOLBY TRUEHD', 'TRUEHD'), 
('DTS', 'DTS'), ('DTS-HD MASTER AUDIO', 'DTS-HD MA'), ('DTS-X', 'DTS-X'), ('DTS-HD', 'DTS-HD'), ('AAC', 'AAC'), ('OPUS', 'OPUS'), ('MP3', 'MP3'),
('8CH AUDIO', '8CH'), ('7CH AUDIO', '7CH'), ('6CH AUDIO', '6CH'), ('2CH AUDIO', '2CH'))

def source_filters():
	return (
('PACK', 'PACK'), ('DOLBY VISION', '[B]D/VISION[/B]'), ('HIGH DYNAMIC RANGE (HDR)', '[B]HDR[/B]'), ('IMAX', 'IMAX'), ('HYBRID', '[B]HYBRID[/B]'), ('AV1', '[B]AV1[/B]'),
('HEVC (X265)', '[B]HEVC[/B]'), ('REMUX', 'REMUX'), ('BLURAY', 'BLURAY'), ('AI ENHANCED/UPSCALED', '[B]AI ENHANCED/UPSCALED[/B]'), ('SDR', 'SDR'), ('3D', '[B]3D[/B]'),
('DOLBY ATMOS', 'ATMOS'), ('DOLBY TRUEHD', 'TRUEHD'), ('DOLBY DIGITAL EX', 'DD-EX'), ('DOLBY DIGITAL PLUS', 'DD+'), ('DOLBY DIGITAL', 'DD'),
('DTS-HD MASTER AUDIO', 'DTS-HD MA'), ('DTS-X', 'DTS-X'), ('DTS-HD', 'DTS-HD'), ('DTS', 'DTS'), ('AAC', 'AAC'), ('OPUS', 'OPUS'), ('MP3', 'MP3'), ('8CH AUDIO', '8CH'),
('7CH AUDIO', '7CH'), ('6CH AUDIO', '6CH'), ('2CH AUDIO', '2CH'), ('DVD SOURCE', 'DVD'), ('WEB SOURCE', 'WEB'), ('MULTIPLE LANGUAGES', 'MULTI-LANG'),
('SUBTITLES', 'SUBS'))

def include_exclude_filters():
	return {'hevc': 'HEVC', '3d': '3D', 'hdr': 'HDR', 'dv': 'D/VISION', 'av1': 'AV1', 'enhanced_upscaled': 'AI ENHANCED/UPSCALED', 'hybrid': 'HYBRID'}

def get_aliases_titles(aliases):
	try: result = [i['title'] for i in aliases]
	except: result = []
	return result

def make_alias_dict(meta, title):
	aliases = []
	alternative_titles = meta.get('alternative_titles', [])
	original_title = meta['original_title']
	cunt_codes = meta.get('country_codes', [])
	country_codes = set([i.replace('GB', 'UK') for i in cunt_codes])
	if alternative_titles: aliases = [{'title': i, 'country': ''} for i in alternative_titles]
	if original_title not in alternative_titles: aliases.append({'title': original_title, 'country': ''})
	if country_codes: aliases.extend([{'title': '%s %s' % (title, i), 'country': ''} for i in country_codes])
	return aliases

def internal_results(provider, sources):
	set_property('redlight.internal_results.%s' % provider, json.dumps(sources))

def normalize(title):
	import unicodedata
	try:
		title = ''.join(c for c in unicodedata.normalize('NFKD', title) if unicodedata.category(c) != 'Mn')
		return str(title)
	except: return title

def pack_enable_check(meta, season, episode):
	try:
		status = meta['extra_info']['status']
		if status in ('Ended', 'Canceled'): return True, True
		adjust_hours, current_date = date_offset(), get_datetime()
		episodes_data = episodes_meta(season, meta)
		unaired_episodes = [adjust_premiered_date(i['premiered'], adjust_hours)[0] for i in episodes_data]
		if None in unaired_episodes or any(i > current_date for i in unaired_episodes): return False, False
		else: return True, False
	except: pass
	return False, False

def clear_scrapers_cache(silent=False):
	from caches.base_cache import clear_cache
	for item in ('internal_scrapers', 'external_scrapers'): clear_cache(item, silent=True)
	if not silent: notification('Success')

def supported_video_extensions():
	supported_video_extensions = supported_media().split('|')
	return [i for i in supported_video_extensions if not i in ('','.zip','.rar','.iso')]

def seas_ep_filter(season, episode, release_title, split=False, return_match=False):
	str_season, str_episode = str(season), str(episode)
	season_fill, episode_fill = str_season.zfill(2), str_episode.zfill(2)
	str_ep_plus_1, str_ep_minus_1 = str(episode+1), str(episode-1)
	release_title = re.sub(r'[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
	string1 = r'(s<<S>>[.-]?e[p]?[.-]?<<E>>[.-])'
	string2 = r'(season[.-]?<<S>>[.-]?episode[.-]?<<E>>[.-])'#|([s]?<<S>>[x.]<<E>>[.-])'
	string3 = r'(s<<S>>e<<E1>>[.-]?e?<<E2>>[.-])'
	string4 = r'([.-]<<S>>[.-]?<<E>>[.-])'
	string5 = r'(episode[.-]?<<E>>[.-])'
	string6 = r'([.-]e[p]?[.-]?<<E>>[.-])'
	string7 = r'(^(?=.*\.e?0*<<E>>\.)(?:(?!((?:s|season)[.-]?\d+[.-x]?(?:ep?|episode)[.-]?\d+)|\d+x\d+).)*$)'
	string8 = r'([s]?<<S>>x<<E>>[.-])'
	string_list = []
	string_list_append = string_list.append
	string_list_append(string1.replace('<<S>>', season_fill).replace('<<E>>', episode_fill))
	string_list_append(string1.replace('<<S>>', str_season).replace('<<E>>', episode_fill))
	string_list_append(string1.replace('<<S>>', season_fill).replace('<<E>>', str_episode))
	string_list_append(string1.replace('<<S>>', str_season).replace('<<E>>', str_episode))
	string_list_append(string2.replace('<<S>>', season_fill).replace('<<E>>', episode_fill))
	string_list_append(string2.replace('<<S>>', str_season).replace('<<E>>', episode_fill))
	string_list_append(string2.replace('<<S>>', season_fill).replace('<<E>>', str_episode))
	string_list_append(string2.replace('<<S>>', str_season).replace('<<E>>', str_episode))
	string_list_append(string3.replace('<<S>>', season_fill).replace('<<E1>>', str_ep_minus_1.zfill(2)).replace('<<E2>>', episode_fill))
	string_list_append(string3.replace('<<S>>', season_fill).replace('<<E1>>', episode_fill).replace('<<E2>>', str_ep_plus_1.zfill(2)))
	string_list_append(string4.replace('<<S>>', season_fill).replace('<<E>>', episode_fill))
	string_list_append(string4.replace('<<S>>', str_season).replace('<<E>>', episode_fill))
	string_list_append(string5.replace('<<E>>', episode_fill))
	string_list_append(string5.replace('<<E>>', str_episode))
	string_list_append(string6.replace('<<E>>', episode_fill))
	string_list_append(string7.replace('<<E>>', episode_fill))
	string_list_append(string8.replace('<<S>>', season_fill).replace('<<E>>', episode_fill))
	string_list_append(string8.replace('<<S>>', str_season).replace('<<E>>', episode_fill))
	string_list_append(string8.replace('<<S>>', season_fill).replace('<<E>>', str_episode))
	string_list_append(string8.replace('<<S>>', str_season).replace('<<E>>', str_episode))
	final_string = '|'.join(string_list)
	reg_pattern = re.compile(final_string)
	if split: return release_title.split(re.search(reg_pattern, release_title).group(), 1)[1]
	if return_match: return re.search(reg_pattern, release_title).group()
	return bool(re.search(reg_pattern, release_title))

def find_season_in_release_title(release_title):
	release_title = re.sub(r'[^A-Za-z0-9-]+', '.', unquote(release_title).replace('\'', '')).lower()
	match = None
	regex_list = [r's(\d+)', r's\.(\d+)', r'(\d+)x', r'(\d+)\.x', r'season(\d+)', r'season\.(\d+)']
	for item in regex_list:
		try:
			match = re.search(item, release_title)
			if match:
				match = int(str(match.group(1)).lstrip('0'))
				break
		except: pass
	return match

def check_title(title, release_title, aliases, year, season, episode):
	try:
		all_titles = [title]
		if aliases: all_titles += aliases
		cleaned_titles = []
		cleaned_titles_append = cleaned_titles.append
		year = str(year)
		for i in all_titles:
			cleaned_titles_append(
				i.lower().replace('\'', '').replace(':', '').replace('!', '').replace('(', '').replace(')', '').replace('&', 'and').replace(' ', '.').replace(year, ''))
		release_title = strip_non_ascii_and_unprintable(release_title).lstrip('/ ').replace(' ', '.').replace(':', '.').lower()
		releasetitle_startswith = release_title.startswith
		unwanted = unwanted_tags()
		for i in unwanted:
			if releasetitle_startswith(i):
				i_startswith = i.startswith
				pattern = r'\%s' % i if i_startswith('[') or i_startswith('+') else r'%s' % i
				release_title = re.sub(r'^%s' % pattern, '', release_title, 1, re.I)
		release_title = release_title.lstrip('.-:/')
		release_title = re.sub(r'^\[.*?]', '', release_title, 1, re.I)
		release_title = release_title.lstrip('.-[](){}:/')
		if season:
			if season == 'pack': hdlr = ''
			else:
				try: hdlr = seas_ep_filter(season, episode, release_title, return_match=True)
				except: return False
		else: hdlr = year
		if hdlr:
			release_title = release_title.split(hdlr.lower())[0]
			release_title = release_title.replace(year, '').replace('(', '').replace(')', '').replace('&', 'and').rstrip('.-').rstrip('.').rstrip('-').replace(':', '')
			if not any(item in release_title for item in cleaned_titles): return False
			# if not any(release_title == i for i in cleaned_titles): return False
		else:
			release_title = release_title.replace(year, '').replace('(', '').replace(')', '').replace('&', 'and').rstrip('.-').rstrip('.').rstrip('-').replace(':', '')
			if not any(i in release_title for i in cleaned_titles): return False
		return True
	except: return True

def strip_non_ascii_and_unprintable(text):
	try:
		result = ''.join(char for char in text if char in printable)
		return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
	except: pass
	return text

def release_info_format(release_title):
	try:
		release_title = url_strip(release_title)
		release_title = release_title.lower().replace("'", "").lstrip('.').rstrip('.')
		title = '.%s.' % re.sub(r'[^a-z0-9-~]+', '.', release_title).replace('.-.', '.').replace('-.', '.').replace('.-', '.').replace('--', '.')
		return title
	except:
		return release_title.lower()

def clean_title(title):
	try:
		if not title: return
		title = title.lower()
		title = re.sub(r'&#(\d+);', '', title)
		title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
		title = title.replace('&quot;', '\"').replace('&amp;', '&')
		title = re.sub(r'\n|([\[({].+?[})\]])|([:;–\-"\',!_.?~$@])|\s', '', title)
	except: pass
	return title

def url_strip(url):
	try:
		url = unquote_plus(url)
		if 'magnet:' in url: url = url.split('&dn=')[1]
		url = url.lower().replace("'", "").lstrip('.').rstrip('.')
		title = re.sub(r'[^a-z0-9]+', ' ', url)
		if 'http' in title: return None
		if title == '': return None
		return title
	except: return None

def get_file_info(name_info=None, url=None, default_quality='SD'):
	title = None
	if name_info: title = name_info
	elif url: title = url_strip(url)
	if not title: return 'SD', ''
	quality = get_release_quality(title) or default_quality
	info = get_info(title)
	return quality, info

def get_release_quality(release_info):
	if any(i in release_info for i in ('.scr.', 'screener', 'dvdscr', 'dvd.scr', '.r5', '.r6')):
		return 'SCR'
	if any(i in release_info for i in ('.cam.', 'camrip', 'hdcam', '.hd.cam', 'hqcam', '.hq.cam', 'cam.rip', 'dvdcam')):
		return 'CAM'
	if any(i in release_info for i in ('.tc.', '.ts.', 'tsrip', 'hdts', 'hdtc', '.hd.tc', 'dvdts', 'telesync', 'tele.sync', 'telecine', 'tele.cine')):
		return 'TELE'
	if any(i in release_info for i in ('720', '720p', '720i', 'hd720', '720hd', 'hd720p', '72o', '72op')):
		return '720p'
	if any(i in release_info for i in ('1080', '1080p', '1080i', 'hd1080', '1080hd', 'hd1080p', 'm1080p', 'fullhd', 'full.hd', '1o8o', '1o8op',
		'108o', '108op', '1o80', '1o80p')): return '1080p'
	if any(i in release_info for i in ('.4k', 'hd4k', '4khd', '.uhd', 'ultrahd', 'ultra.hd', 'hd2160', '2160hd', '2160', '2160p', '216o', '216op')):
		return '4K'
	return None

def get_info(title):
	# thanks 123Venom and gaiaaaiaai, whom I knicked most of this code from. :)
	info = []
	info_append = info.append
	if any(i in title for i in ('.3d.', '.sbs.', '.hsbs', 'sidebyside', 'side.by.side', 'stereoscopic', '.tab.', '.htab.', 'topandbottom', 'top.and.bottom')):
		info_append('[B]3D[/B]')
	if '.sdr' in title:
		info_append('SDR')
	elif any(i in title for i in ('dolby.vision', 'dolbyvision', '.dovi.', '.dv.')):
		info_append('[B]D/VISION[/B]')
	elif any(i in title for i in ('2160p.bluray.hevc.truehd', '2160p.bluray.hevc.dts', '2160p.bluray.hevc.lpcm', '2160p.blu.ray.hevc.truehd', '2160p.blu.ray.hevc.dts',
		'2160p.uhd.bluray', '2160p.uhd.blu.ray', '2160p.us.bluray.hevc.truehd', '2160p.us.bluray.hevc.dts', '.hdr.', 'hdr10', 'hdr.10', 'uhd.bluray.2160p',
		'uhd.blu.ray.2160p')):
		info_append('[B]HDR[/B]')
	elif all(i in title for i in ('2160p', 'remux')):
		info_append('[B]HDR[/B]')
	if '[B]D/VISION[/B]' in info:
		if any(i in title for i in ('.hdr.', '.hdr10.', 'hdr.10')) or 'hybrid' in title:
			info_append('[B]HDR[/B]')
		if '[B]HDR[/B]' in info:
			info_append('[B]HYBRID[/B]')
	if any(i in title for i in ('avc', 'h264', 'h.264', 'x264', 'x.264')):
		info_append('AVC')
	elif '.av1.' in title:
		info_append('[B]AV1[/B]')
	elif any(i in title for i in ('h265', 'h.265', 'hevc', 'x265', 'x.265')):
		info_append('[B]HEVC[/B]')
	elif any(i in info for i in ('[B]HDR[/B]', '[B]D/VISION[/B]')):
		info_append('[B]HEVC[/B]')
	if any(i in title for i in ('.imax.', '.(imax).', '.(.imax.).')):
		info_append('IMAX')
	elif any(i in title for i in ('.enhanced.', '.upscaled.', '.enhance.', '.upscale.', '.ai.')):
		info_append('[B]AI ENHANCED/UPSCALED[/B]')
	if '.atvp' in title:
		info_append('APPLETV+')
	elif any(i in title for i in ('xvid', '.x.vid')):
		info_append('XVID')
	elif any(i in title for i in ('divx', 'div2', 'div3', 'div4')):
		info_append('DIVX')
	if any(i in title for i in ('remux', 'bdremux')):
		info_append('REMUX')
	if any(i in title for i in ('bluray', 'blu.ray', 'bdrip', 'bd.rip')):
		info_append('BLURAY')
	elif any(i in title for i in ('dvdrip', 'dvd.rip')):
		info_append('DVD')
	elif any(i in title for i in ('.web.', 'webdl', 'web.dl', 'web-dl', 'webrip', 'web.rip')):
		info_append('WEB')
	elif 'hdtv' in title:
		info_append('HDTV')
	elif 'pdtv' in title:
		info_append('PDTV')
	elif any(i in title for i in ('.hdrip', '.hd.rip')):
		info_append('HDRIP')
	if 'atmos' in title:
		info_append('ATMOS')
	if any(i in title for i in ('true.hd', 'truehd')):
		info_append('TRUEHD')
	if any(i in title for i in ('dolby.digital.plus', 'dolbydigital.plus', 'dolbydigitalplus', 'dd.plus.', 'ddplus', '.ddp.', 'ddp2', 'ddp5', 'ddp7', 'eac3', '.e.ac3')):
		info_append('DD+')
	elif any(i in title for i in ('.dd.ex.', 'ddex', 'dolby.ex.', 'dolby.digital.ex.', 'dolbydigital.ex.')):
		info_append('DD-EX')
	elif any(i in title for i in ('dd2.', 'dd5', 'dd7', 'dolby.digital', 'dolbydigital', '.ac3', '.ac.3.', '.dd.')):
		info_append('DD')
	if 'aac' in title:
		info_append('AAC')
	elif 'mp3' in title:
		info_append('MP3')
	elif '.flac.' in title:
		info_append('FLAC')
	elif 'opus' in title and not title.endswith('opus.'):
		info_append('OPUS')
	if any(i in title for i in ('.dts.x.', 'dtsx')):
		info_append('DTS-X')
	elif any(i in title for i in ('hd.ma', 'hdma')):
		info_append('DTS-HD MA')
	elif any(i in title for i in ('dts.hd.', 'dtshd')):
		info_append('DTS-HD')
	elif '.dts' in title:
		info_append('DTS')
	if any(i in title for i in ('ch8.', '8ch.', '7.1ch', '7.1.')):
		info_append('8CH')
	elif any(i in title for i in ('ch7.', '7ch.', '6.1ch', '6.1.')):
		info_append('7CH')
	elif any(i in title for i in ('ch6.', '6ch.', '5.1ch', '5.1.')):
		info_append('6CH')
	elif any(i in title for i in ('ch2', '2ch', '2.0ch', '2.0.', 'audio.2.0.', 'stereo')):
		info_append('2CH')
	if '.wmv' in title:
		info_append('WMV')
	elif any(i in title for i in ('.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.mp4', '.m4p', '.m4v', 'msmpeg', 'mpegurl')):
		info_append('MPEG')
	elif '.avi' in title:
		info_append('AVI')
	elif any(i in title for i in ('.mkv', 'matroska')):
		info_append('MKV')
	if any(i in title for i in ('hindi.eng', 'ara.eng', 'ces.eng', 'chi.eng', 'cze.eng', 'dan.eng', 'dut.eng', 'ell.eng', 'esl.eng', 'esp.eng', 'fin.eng', 'fra.eng',
		'fre.eng', 'frn.eng', 'gai.eng', 'ger.eng', 'gle.eng', 'gre.eng', 'gtm.eng', 'heb.eng', 'hin.eng', 'hun.eng', 'ind.eng', 'iri.eng', 'ita.eng', 'jap.eng',
		'jpn.eng', 'kor.eng', 'lat.eng', 'lebb.eng', 'lit.eng', 'nor.eng', 'pol.eng', 'por.eng', 'rus.eng', 'som.eng', 'spa.eng', 'sve.eng', 'swe.eng', 'tha.eng',
		'tur.eng', 'uae.eng', 'ukr.eng', 'vie.eng', 'zho.eng', 'dual.audio', 'multi')):
		info_append('MULTI-LANG')
	if any(i in title for i in ('1xbet', 'betwin')):
		info_append('ADS')
	if any(i in title for i in ('subita', 'subfrench', 'subspanish', 'subtitula', 'swesub', 'nl.subs', 'subbed')):
		info_append('SUBS')
	return ' | '.join(filter(None, info))

def get_cache_expiry(media_type, meta, season):
	try:
		current_date = get_datetime()
		if media_type == 'movie':
			premiered = jsondate_to_datetime(meta['premiered'], '%Y-%m-%d', remove_time=True)
			difference = subtract_dates(current_date, premiered)
			if difference == 0: single_expiry = 3
			elif difference <= 7: single_expiry = 24
			elif difference <= 14: single_expiry = 48
			elif difference <= 21: single_expiry = 72
			elif difference <= 30: single_expiry = 96
			elif difference <= 60: single_expiry = 168
			else: single_expiry = 336
			season_expiry, show_expiry = 0, 0
		else:
			recently_ended = False
			extra_info = meta['extra_info']
			ended = extra_info['status'] in ('Ended', 'Canceled')
			premiered = adjust_premiered_date(meta['premiered'], date_offset())[0]
			difference = subtract_dates(current_date, premiered)
			last_episode_to_air = jsondate_to_datetime(extra_info['last_episode_to_air']['air_date'], '%Y-%m-%d', remove_time=True)
			last_ep_difference = subtract_dates(current_date, last_episode_to_air)
			if ended and last_ep_difference <= 14: recently_ended = True
			if not ended or recently_ended:
				if difference == 0: single_expiry = 3
				elif difference <= 3: single_expiry = 24
				elif difference <= 7: single_expiry = 72
				else: single_expiry = 168
				if meta['total_seasons'] == season:
					if last_ep_difference <= 7: season_expiry = 72
					else: season_expiry = 240
				else: season_expiry = 720
				show_expiry = 240
			else: single_expiry, season_expiry, show_expiry = 240, 720, 720
	except: single_expiry, season_expiry, show_expiry = 72, 72, 240
	return single_expiry, season_expiry, show_expiry

def get_external_cache_status(debrid, unchecked_hashes, data, active_debrid):
	def _process(service, hashes):
		result = []
		if service in ('mediafusion', 'torrentio'):
			if service == 'mediafusion':
				base_link, name_test = 'https://mediafusion.elfhosted.com/%s=%s' % (debrid_name, token), '⚡'
				params = json.dumps({'enable_catalogs': False, 'max_streams_per_resolution': 99, 'torrent_sorting_priority':[], 'certification_filter': ['Disable'],
											'nudity_filter': ['Disable'], 'streaming_provider': {'token': token, 'service': debrid_name,
											'only_show_cached_streams': True}}).encode('utf-8')
				headers = {'encoded_user_data': base64.b64encode(params).decode('utf-8')}
			elif service == 'torrentio':
				base_link, name_test = 'https://torrentio.strem.fun/%s=%s' % (debrid_name, token), '[RD+]'
				headers = {'User-Agent': 'Mozilla/5.0'}
			try:
				if 'tvshowtitle' in data: url = '%s%s' % (base_link, '/stream/series/%s:%s:%s.json' % (imdb_id, data['season'], data['episode']))
				else: url = '%s%s' % (base_link, '/stream/movie/%s.json' % imdb_id)
				result = requests.get(url, headers=headers, timeout=9)
				result = result.json()['streams']
				if result:
					result = [re.search(r'\b\w{40}\b', i.get('url')) for i in result if name_test in i['name']]
					result = [i.group() for i in result if i]
			except: pass
		elif service == 'dmm':
			import ctypes, random
			def get_secret():
				def calc_value_alg(t, n, const):
					temp = t ^ n
					t = ctypes.c_long((temp * const)).value
					t4 = ctypes.c_long(t << 5).value
					t5 = ctypes.c_long((t & 0xFFFFFFFF) >> 27).value
					return t4 | t5
				def slice_hash(s, n):
					half = int(len(s) // 2)
					left_s, right_s = s[:half], s[half:]
					left_n, right_n = n[:half], n[half:]
					l = ''.join(ls + ln for ls, ln in zip(left_s, left_n))
					return l + right_n[::-1] + right_s[::-1]
				def generate_hash(e):
					t = ctypes.c_long(0xDEADBEEF ^ len(e)).value
					a = 1103547991 ^ len(e)
					for ch in e:
						n = ord(ch)
						t = calc_value_alg(t, n, 2654435761)
						a = calc_value_alg(a, n, 1597334677)
					t = ctypes.c_long(t + ctypes.c_long(a * 1566083941).value).value
					a = ctypes.c_long(a + ctypes.c_long(t * 2024237689).value).value
					return (ctypes.c_long(t ^ a).value & 0xFFFFFFFF)
				ran = random.randrange(10 ** 80)
				hex_str = f"{ran:064x}"[:8]
				timestamp = int(time.time())
				dmmProblemKey = f"{hex_str}-{timestamp}"
				s = generate_hash(dmmProblemKey)
				s = f"{s:x}"
				n = generate_hash("debridmediamanager.com%%fe7#td00rA3vHz%VmI-" + hex_str)
				n = f"{n:x}"
				solution = slice_hash(s, n)
				return dmmProblemKey, solution
			def fetch(hash_chunk):
				try:
					json_data = {'dmmProblemKey': dmmProblemKey, 'solution': solution, 'imdbId': imdb_id, 'hashes': hash_chunk}
					r = requests.post('https://debridmediamanager.com/api/availability/check', json=json_data, timeout=9).json()
					r = [i['hash'] for i in r['available'] if 'hash' in i]
					result_extend(r)
				except: pass
			result = []
			result_extend = result.extend
			dmmProblemKey, solution = get_secret()
			unchecked_hashes_chunks = list(chunks(unchecked_hashes, 100))
			threads = [Thread(target=fetch, args=(item,)) for item in unchecked_hashes_chunks]
			[i.start() for i in threads]
			[i.join() for i in threads]
		results.extend(result)
	try:
		results = []
		imdb_id = data['imdb']
		debrid_name, services, token = {'Real-Debrid': ('realdebrid', ['torrentio'], get_setting('redlight.rd.token')),
										'AllDebrid': ('alldebrid', ['mediafusion'], get_setting('redlight.ad.token'))}[debrid]
		threads = [Thread(target=_process, args=(item, unchecked_hashes)) for item in services]
		[i.start() for i in threads]
		[i.join() for i in threads]
		results = list(set(results))
	except: pass
	if debrid == 'Real-Debrid':
		try: _process('dmm', [i for i in unchecked_hashes if not i in results])
		except: pass
	return results