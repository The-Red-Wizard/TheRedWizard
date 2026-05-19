# -*- coding: utf-8 -*-
import requests
from apis import google_api, groq_api
from apis.tmdb_api import tmdb_movies_search, tmdb_tv_search
from caches.base_cache import get_timestamp
from caches.lists_cache import lists_cache, lists_cache_object
from modules.metadata import movie_meta, tvshow_meta
from modules.kodi_utils import notification
from modules.utils import TaskPool, normalize, get_datetime, get_current_timestamp
from modules.settings import ai_model_order, ai_model_limit, max_threads, tmdb_api_key, mpaa_region
# from modules.kodi_utils import logger

# GOOGLE_MODELS = ('gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-1b-it', 'gemma-3-4b-it', 'gemini-3-flash-preview')
# GROQ_MODELS = ('llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'openai/gpt-oss-120b')

def ai_similar(media_info, dummy=None):
	def _fetch_similar(dummy):
		try:
			data = ai_similar_call(media_type, tmdb_id, meta, limit)
			data = data.get('recommendations') or data.get('recs') or []
			if not isinstance(data, list) or not data: return []
			recommendations = data[:limit]
			threads = TaskPool().tasks_enumerate(_process_results, recommendations, min(len(recommendations), max_threads()))
			[i.join() for i in threads]
			recommendations_list.sort(key=lambda k: k['order'])
			return {'results': recommendations_list, 'page': 1, 'total_pages': 1}
		except: return []
	def _process_results(count, item):
		title = item['title'].strip()
		if not title: return
		year = item['year']
		if not year: return
		try:
			year = int(str(year).strip())
			if 2100 < year < 1800: year = None
		except: year = None
		if item['type'] != media_type: return
		data = pick_best_tmdb_match(tmdb_simplified(title, media_type), title, year)
		if not data: return
		title, year, tmdb_id = data['title'], data['year'], data['tmdb_id']
		recommendations_list.append({'title': title, 'year': year, 'media_type': media_type, 'id': tmdb_id, 'order': count})
	recommendations_list = []
	media_type, tmdb_id = media_info.split('|')
	meta_function = movie_meta if media_type == 'movie' else tvshow_meta
	meta = meta_function('tmdb_id', tmdb_id, tmdb_api_key(), mpaa_region(), get_datetime(), get_current_timestamp())
	limit = ai_model_limit()
	media_type = "Movie" if media_type == 'movie' else "Show"
	string = 'ai_similar_%s_%s_%s' % (media_type, tmdb_id, limit)
	return lists_cache_object(_fetch_similar, string, 'foo', expiration=168)

def tmdb_simplified(title, media_type):
	function = tmdb_movies_search if media_type == 'Movie' else tmdb_tv_search
	try: data = function(title, 1)['results']
	except: return []
	results = []
	for item in data:
		year = None
		title = item['title' if media_type == 'Movie' else 'name']
		release_date = item['release_date' if media_type == 'Movie' else 'first_air_date']
		if not release_date: continue
		year = int(release_date.split('-')[0])
		results.append({'tmdb_id': item.get('id'), 'title': title, 'year': year})
	return results

def pick_best_tmdb_match(results, title, year):
	if not results: return None
	compare_title, compare_year = normalize(title), int(year) if year else None
	if compare_year is not None:
		for item in results:
			title = normalize(item['title'])
			year = item['year']
			if title == compare_title and year == compare_year: return item
			if title == compare_title and year is not None and abs(year - compare_year) == 1: return item
	return results[0]

def get_currently_active_model():
	model_id = None
	try:
		timeout_models = lists_cache.get('ai_model_failed') or []
		model_order = [i for i in ai_model_order() for x in [google_api, groq_api] if x.model_present(i) and x.get_api() not in (None, 'None', '', 'empty_setting')]
		if timeout_models:
			timeout_ended_models = [i for i in timeout_models if i['timeout_ends'] <= get_timestamp()]
			if timeout_ended_models:
				timeout_models = [i for i in timeout_models if i not in timeout_ended_models]
				lists_cache.set('ai_model_failed', timeout_models, 24*365)
		if timeout_models: model_id = next(i for i in model_order if i not in (x['model_id'] for x in timeout_models))
		else: model_id = model_order[0]
	except: pass
	return model_id

def set_currently_active_models(model_id, status_code):
	try:
		timeout_models = lists_cache.get('ai_model_failed') or []
		current_model_info = next((i for i in timeout_models if i['model_id'] == model_id), {})
		current_fails = current_model_info.get('fails', 0)
		timeout_models = [i for i in timeout_models if i != current_model_info]
		if status_code == 429 or current_fails == 2:
			fails, timeout_ends = 0, get_timestamp(24)
			notification('Disabling %s: Error Code %s' % (model_id, status_code))
		else: fails, timeout_ends = current_fails + 1, 0
		timeout_models.append({'model_id': model_id, 'fails': fails, 'timeout_ends': timeout_ends})
		lists_cache.set('ai_model_failed', timeout_models, 24*365)
		return True
	except: return False

def ai_similar_call(media_type, tmdb_id, meta, limit, timeout=30):
	model_id = get_currently_active_model()
	if not model_id: return {}
	try: model_info = next(i.model_info(model_id, media_type, meta, limit) for i in [google_api, groq_api] if i.model_present(model_id))
	except: return {}
	response = requests.post(model_info['similar']['url'], headers=model_info['similar']['headers'], json=model_info['similar']['payload'], timeout=timeout)
	headers = response.headers
	status_code = response.status_code
	if status_code != 200:
		if set_currently_active_models(model_id, status_code): return ai_similar_call(media_type, tmdb_id, meta, limit, timeout)
		return {}
	data = response.json()
	result = model_info['similar']['parse'](data)
	return result
