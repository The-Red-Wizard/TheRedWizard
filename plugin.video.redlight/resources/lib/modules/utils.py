# -*- coding: utf-8 -*-
import re
import sys
import time
import random
import _strptime
import unicodedata
from html import unescape
from queue import SimpleQueue
from threading import Thread, activeCount
from importlib import import_module
from datetime import datetime, timedelta, date
from modules.settings import max_threads
from modules.kodi_utils import sleep, logger

class TaskPool:
	def __init__(self):
		self._queue = SimpleQueue()

	def _thread_target(self, queue, target):
		while not queue.empty():
			try: target(*queue.get())
			except Exception as e: logger('thread queue error', str(e))

	def tasks(self, _target, _list, _max_size=60):
		if not isinstance(_list[0], tuple): _list = [(i,) for i in _list]
		[self._queue.put(tag) for tag in _list]
		threads = [Thread(target=self._thread_target, args=(self._queue, _target)) for i in range(_max_size)]
		[i.start() for i in threads]
		return threads

	def tasks_enumerate(self, _target, _list, _max_size=60):
		[self._queue.put((p, tag)) for p, tag in enumerate(_list, 1)]
		threads = [Thread(target=self._thread_target, args=(self._queue, _target)) for i in range(_max_size)]
		[i.start() for i in threads]
		return threads

def make_thread_list(_target, _list):
	_max_threads = max_threads()
	for item in _list:
		while activeCount() > _max_threads: sleep(1)
		threaded_object = Thread(target=_target, args=(item,))
		threaded_object.start()
		yield threaded_object

def make_thread_list_enumerate(_target, _list):
	_max_threads = max_threads()
	for count, item in enumerate(_list):
		while activeCount() > _max_threads: sleep(1)
		threaded_object = Thread(target=_target, args=(count, item))
		threaded_object.start()
		yield threaded_object

def change_image_resolution(image, replace_res):
	return re.sub(r'(w185|w300|w342|w780|w1280|h632|original)', replace_res, image)

def append_module_to_syspath(location):
	from modules.kodi_utils import translate_path
	sys.path.append(translate_path(location))

def manual_function_import(location, function_name):
	return getattr(import_module(location), function_name)

def reload_module(location):
	from importlib import reload as rel_module
	return rel_module(manual_module_import(location))

def manual_module_import(location):
	return import_module(location)

def chunks(item_list, limit):
	"""
	Yield successive limit-sized chunks from item_list.
	"""
	for i in range(0, len(item_list), limit): yield item_list[i:i + limit]

def string_to_float(string, default_return):
	"""
	Remove all alpha from string and return a float.
	Returns float of "default_return" upon ValueError.
	"""
	try: return float(''.join(c for c in string if (c.isdigit() or c =='.')))
	except ValueError: return float(default_return)

def string_alphanum_to_num(string):
	"""
	Remove all alpha from string and return remaining string.
	Returns original string upon ValueError.
	"""
	try: return ''.join(c for c in string if c.isdigit())
	except ValueError: return string

def jsondate_to_datetime(jsondate_object, resformat, remove_time=False):
	if not jsondate_object: return None
	if remove_time: datetime_object = datetime_workaround(jsondate_object, resformat).date()
	else: datetime_object = datetime_workaround(jsondate_object, resformat)
	return datetime_object

def get_datetime(string=False, dt=False):
	d = datetime.now()
	if dt: return d
	if string: return d.strftime('%Y-%m-%d')
	return datetime.date(d)

def get_current_timestamp():
	return int(time.time())
	
def adjust_premiered_date(orig_date, adjust_hours):
	if not orig_date: return None, None
	orig_date += ' 20:00:00'
	datetime_object = jsondate_to_datetime(orig_date, '%Y-%m-%d %H:%M:%S')
	adjusted_datetime = datetime_object + timedelta(hours=adjust_hours)
	adjusted_string = adjusted_datetime.strftime('%Y-%m-%d')
	return adjusted_datetime.date(), adjusted_string

def make_day(today, date, date_format='%Y-%m-%d', use_words=True):
	if use_words:
		day_diff = (date - today).days
		if day_diff == -1: day = 'YESTERDAY'
		elif day_diff == 0: day = 'TODAY'
		elif day_diff == 1: day = 'TOMORROW'
		elif 1 < day_diff < 7: day = date.strftime('%A').upper()
		else:
			try: day = date.strftime(date_format)
			except ValueError: day = date.strftime('%Y-%m-%d')
	else:
		try: day = date.strftime(date_format)
		except ValueError: day = date.strftime('%Y-%m-%d')
	return day

def subtract_dates(date1, date2):
	return (date1 - date2).days
	return day

def datetime_workaround(data, str_format):
	try: datetime_object = datetime.strptime(data, str_format)
	except: datetime_object = datetime(*(time.strptime(data, str_format)[0:6]))
	return datetime_object

def date_difference(current_date, compare_date, difference_tolerance, allow_postive_difference=False):
	try:
		difference = subtract_dates(current_date, compare_date)
		if not allow_postive_difference and difference > 0: return False
		else: difference = abs(difference)
		if difference > difference_tolerance: return False
		return True
	except: return True

def calculate_age(born, str_format, died=None):
	''' born and died are str objects e.g. '1972-05-28' '''
	born = datetime_workaround(born, str_format)
	if not died: today = date.today()
	else: today = datetime_workaround(died, str_format)
	return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def batch_replace(s, replace_info):
	for r in replace_info:
		s = str(s).replace(r[0], r[1])
	return s

def clean_file_name(s, use_encoding=False, use_blanks=True):
	try:
		hex_entities = [['&#x26;', '&'], ['&#x27;', '\''], ['&#xC6;', 'AE'], ['&#xC7;', 'C'],
					['&#xF4;', 'o'], ['&#xE9;', 'e'], ['&#xEB;', 'e'], ['&#xED;', 'i'],
					['&#xEE;', 'i'], ['&#xA2;', 'c'], ['&#xE2;', 'a'], ['&#xEF;', 'i'],
					['&#xE1;', 'a'], ['&#xE8;', 'e'], ['%2E', '.'], ['&frac12;', '%BD'],
					['&#xBD;', '%BD'], ['&#xB3;', '%B3'], ['&#xB0;', '%B0'], ['&amp;', '&'],
					['&#xB7;', '.'], ['&#xE4;', 'A'], ['\xe2\x80\x99', '']]
		special_encoded = [['"', '%22'], ['*', '%2A'], ['/', '%2F'], [':', ','], ['<', '%3C'],
							['>', '%3E'], ['?', '%3F'], ['\\', '%5C'], ['|', '%7C']]
		
		special_blanks = [['"', ' '], ['/', ' '], [':', ''], ['<', ' '],
							['>', ' '], ['?', ' '], ['\\', ' '], ['|', ' '], ['%BD;', ' '],
							['%B3;', ' '], ['%B0;', ' '], ["'", ""], [' - ', ' '], ['.', ' '],
							['!', ''], [';', ''], [',', '']]
		s = batch_replace(s, hex_entities)
		if use_encoding: s = batch_replace(s, special_encoded)
		if use_blanks: s = batch_replace(s, special_blanks)
		s = s.strip()
	except: pass
	return s

def byteify(data, ignore_dicts=False):
	try:
		if isinstance(data, unicode): return data.encode('utf-8')
		if isinstance(data, list): return [byteify(item, ignore_dicts=True) for item in data]
		if isinstance(data, dict) and not ignore_dicts:
			iter_data = data.iteritems()
			return dict([(byteify(key, ignore_dicts=True), byteify(value, ignore_dicts=True)) for key, value in iter_data])
	except: pass
	return data

def normalize(txt):
	txt = re.sub(r'[^\x00-\x7f]',r'', txt)
	return txt

def safe_string(obj):
	try:
		try: return str(obj)
		except UnicodeEncodeError: return obj.encode('utf-8', 'ignore').decode('ascii', 'ignore')
		except: return ""
	except: return obj

def remove_accents(obj):
	try:
		try: obj = u'%s' % obj
		except: pass
		obj = ''.join(c for c in unicodedata.normalize('NFD', obj) if unicodedata.category(c) != 'Mn')
	except: pass
	return obj

def regex_from_to(text, from_string, to_string, excluding=True):
	if excluding: r = re.search(r"(?i)" + from_string + r"([\S\s]+?)" + to_string, text).group(1)
	else: r = re.search(r"(?i)(" + from_string + r"[\S\s]+?" + to_string + ")", text).group(1)
	return r

def regex_get_all(text, start_with, end_with):
	r = re.findall(r"(?i)(" + start_with + r"[\S\s]+?" + end_with + ")", text)
	return r

def replace_html_codes(txt):
	txt = re.sub(r"(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
	txt = unescape(txt)
	txt = txt.replace("<ul>", "\n")
	txt = txt.replace("</ul>", "\n")
	txt = txt.replace("<li>", "\n* ")
	txt = txt.replace("</li>", "")
	txt = txt.replace("<br/><br/>", "\n")
	txt = txt.replace("&quot;", "\"")
	txt = txt.replace("&amp;", "&")
	txt = txt.replace("[spoiler]", "")
	txt = txt.replace("[/spoiler]", "")
	return txt

def gen_md5(value):
	import hashlib
	try:
		md5_hash = hashlib.md5()
		md5_hash.update(str(value).encode('utf-8'))
		return md5_hash.hexdigest()
	except: return None

def gen_file_hash(file):
	import hashlib
	try:
		md5_hash = hashlib.md5()
		with open(file, 'rb') as afile:
			buf = afile.read()
			md5_hash.update(buf)
			return md5_hash.hexdigest()
	except: pass

def extract_json_object(raw_text):
	import json
	try:
		start = raw_text.find("{")
		end = raw_text.rfind("}")
		if start == -1 or end == -1 or end <= start: return {}
		json_str = raw_text[start:end + 1]
		return json.loads(json_str)
	except: return {}

def sec2time(sec, n_msec=3):
	''' Convert seconds to 'D days, HH:MM:SS.FFF' '''
	if hasattr(sec,'__len__'): return [sec2time(s) for s in sec]
	m, s = divmod(sec, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	if n_msec > 0: pattern = '%%02d:%%02d:%%0%d.%df' % (n_msec+3, n_msec)
	else: pattern = '%02d:%02d:%02d'
	if d == 0: return pattern % (h, m, s)
	return ('%d days, ' + pattern) % (d, h, m, s)

def released_key(item):
	if 'released' in item: return item['released'] or '2050-01-01'
	if 'first_aired' in item: return item['first_aired'] or '2050-01-01'
	return '2050-01-01'

def title_key(title, ignore_articles):
	if not ignore_articles: return title
	try:
		if title is None: title = ''
		articles = ['the', 'a', 'an']
		match = re.match(r'^((\w+)\s+)', title.lower())
		if match and match.group(2) in articles: offset = len(match.group(1))
		else: offset = 0
		return title[offset:]
	except: return title

def sort_for_article(_list, _key, ignore_articles):
	try:
		if not ignore_articles: _list.sort(key=lambda k: k.get(_key))
		else: _list.sort(key=lambda k: re.sub(r'(^the |^a |^an )', '', k.get(_key).lower()))
	except: pass
	return _list
	
def sort_list(sort_key, sort_direction, list_data, ignore_articles):
	try:
		reverse = sort_direction != 'asc'
		if sort_key == 'rank': return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
		if sort_key == 'added': return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
		if sort_key == 'title': return sorted(list_data, key=lambda x: title_key(x[x['type']].get('title'), ignore_articles), reverse=reverse)
		if sort_key == 'released': return sorted(list_data, key=lambda x: released_key(x[x['type']]), reverse=reverse)
		if sort_key == 'runtime': return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
		if sort_key == 'popularity': return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
		if sort_key == 'percentage': return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
		if sort_key == 'votes': return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
		if sort_key == 'random': return sorted(list_data, key=lambda k: random.random())
		return list_data
	except: return list_data

def paginate_list(item_list, page, limit=20, paginate_start=0):
	if paginate_start:
		item_list = item_list[paginate_start:]
		pages = list(chunks(item_list, limit))
		pages.insert(0, [])
	else: pages = list(chunks(item_list, limit))
	result = (pages[page - 1], len(pages))
	return result

def unzip(zip_location, destination_location, destination_check, show_busy=True):
	from zipfile import ZipFile
	from modules.kodi_utils import show_busy_dialog, hide_busy_dialog, path_exists
	if show_busy: show_busy_dialog()
	try:
		zipfile = ZipFile(zip_location)
		zipfile.extractall(path=destination_location)
		if path_exists(destination_check): status = True
		else: status = False
	except: status = False
	if show_busy: hide_busy_dialog()
	return status

def make_qrcode(url):
	if url == None: return
	import segno
	from hashlib import sha1
	from os import path
	from modules.kodi_utils import addon_profile
	try:
		qr_id = sha1(url.encode('utf-8')).hexdigest()[:12]
		art_path = path.join(addon_profile(), 'qr_%s.png' % qr_id)
		qrcode = segno.make(url, micro=False)
		qrcode.save(art_path, scale=20)
	except: return
	return art_path

def make_tinyurl(url):
	if not url:
		return ''
	import requests
	try:
		response = requests.get('https://tinyurl.com/api-create.php', params={'url': url}, timeout=15)
		if response.status_code != 200:
			return ''
		short_url = (response.text or '').strip()
		if short_url.lower().startswith('http'):
			return short_url
	except Exception:
		pass
	return ''

def copy2clip(txt):
	if not txt: return
	if sys.platform == "win32":
		try:
			from subprocess import Popen, PIPE
			p = Popen(['clip'], stdin=PIPE)
			p.communicate(input=txt.strip().encode('utf-8'))
			return p.returncode
		except: return
	if sys.platform == "darwin":
		try:
			from subprocess import Popen, PIPE
			p = Popen(['pbcopy'], stdin=PIPE)
			p.communicate(input=txt.strip().encode('utf-8'))
			return p.returncode
		except: return
	if sys.platform == "linux":
		try:
			from subprocess import Popen, PIPE
			p = Popen(['xsel', '-pi'], stdin=PIPE)
			p.communicate(input=txt.strip().encode('utf-8'))
			return p.returncode
		except: return

def image_from_db(image_url, delete=True):
	import os
	import sqlite3 as database
	from modules.kodi_utils import translate_path
	try:
		thumbs_folder = translate_path('special://thumbnails')
		dbfile = translate_path(os.path.join('special://database', 'Textures13.db'))
		if os.path.exists(dbfile):
			dbcon = database.connect(dbfile, isolation_level=None)
			dbcur = dbcon.cursor()
			dbcur.execute('''PRAGMA synchronous = OFF''')
			dbcur.execute('''PRAGMA journal_mode = OFF''')
		else: return notification('Failed')
		try: image_id, image_location = dbcur.execute("SELECT id, cachedurl FROM texture WHERE url = ?", (image_url,)).fetchone()
		except: return True
		path = os.path.join(thumbs_folder, image_location)
		if not delete: return path
		os.remove(path)
		dbcur.execute("DELETE FROM texture WHERE id=?", (image_id,))
		dbcur.execute("DELETE FROM sizes WHERE idtexture = ?", (image_id,))
		dbcur.execute("VACUUM")
		dbcon.commit()
		return True
	except: return False

def make_image(list_type, image_type, list_name, images, current_image):
	import os
	import shutil
	import urllib.request
	from PIL import Image
	from modules.kodi_utils import translate_path, addon_profile, make_directory, notification
	def _process(count, item):
		saved_path = translate_path(os.path.join(worker_image_folder, '%s_%02d.jpg' % (list_name, count + 1)))
		urllib.request.urlretrieve(item, saved_path)
		bg = Image.open(saved_path)
		bg.thumbnail(size_dimensions)
		new_img.paste(bg, placements[count])
	saved_final_image = None
	md5_image_name = gen_md5(list_name)
	try:
		profile_path = addon_profile()
		worker_image_folder = os.path.join(profile_path, 'images', '%s_worker' % list_type)
		final_image_folder = os.path.join(profile_path, 'images', '%s_%s' % (list_type, image_type))
		saved_final_image = os.path.join(final_image_folder, '%s_%s.jpg' % (md5_image_name, get_current_timestamp()))
		for location in (worker_image_folder, final_image_folder): make_directory(location)
		if image_type == 'poster': new_dimensions, size_dimensions, placements = (1000, 1500), (500, 750), ((0, 0), (500, 0), (0, 750), (500, 750))
		else: new_dimensions, size_dimensions, placements = (1280, 720), (640, 360), ((0, 0), (640, 0), (0, 360), (640, 360))
		new_img = Image.new('RGB', new_dimensions)
		threads = list(make_thread_list_enumerate(_process, images))
		[i.join() for i in threads]
		new_img.save(saved_final_image)
		try: shutil.rmtree(worker_image_folder)
		except: pass
		if current_image: os.remove(current_image)
	except: notification('Error Creating Image')
	return saved_final_image

def download_image(list_type, image_type, list_name, url, current_image):
	import os
	import shutil
	import urllib.request
	from modules.kodi_utils import addon_profile, make_directory, notification
	saved_final_image = None
	md5_image_name = gen_md5(list_name)
	try:
		profile_path = addon_profile()
		final_image_folder = os.path.join(profile_path, 'images', '%s_%s' % (list_type, image_type))
		saved_final_image = os.path.join(final_image_folder, '%s_%s.jpg' % (md5_image_name, get_current_timestamp()))
		make_directory(final_image_folder)
		urllib.request.urlretrieve(url, saved_final_image)
		if current_image: os.remove(current_image)
	except: notification('Error Creating Image')
	return saved_final_image
	
