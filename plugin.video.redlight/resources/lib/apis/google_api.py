# -*- coding: utf-8 -*-
from caches.settings_cache import get_setting
from modules.utils import extract_json_object
# from modules.kodi_utils import logger

# GOOGLE_MODELS = ('gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-1b-it', 'gemma-3-4b-it', 'gemini-3-flash-preview')

def models():
	return ('gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemma-3-27b-it', 'gemma-3-12b-it', 'gemma-3-1b-it', 'gemma-3-4b-it', 'gemini-3-flash-preview')

def similar_prompt():
	return '''
Recommend EXACTLY LIMIT_HERE MEDIA_TYPE_HERE based on

MEDIA_TYPE: MEDIA_TYPE_HERE
TITLE: TITLE_HERE
YEAR: YEAR_HERE
PLOT: PLOT_HERE
GENRES: GENRES_HERE
KEYWORDS: KEYWORDS_HERE

If MEDIA_TYPE is "Movie" recommend ONLY movies otherwise recommend ONLY TV series / mini-series.
Respond ONLY with one JSON array in this exact shape. No other text.

{
  "recommendations": [
	{
	  "title": "Title 1",
	  "year": 2000,
	  "type": "Movie"  // or "Show"
	}
  ]
}

If a title would contain double quotes, replace them with single quotes (').
Don't include year in title.
'''.strip()

def similar_parse(data):
	candidates = data.get('candidates') or []
	if not candidates: return {}
	parts = (candidates[0].get('content') or {}).get('parts') or []
	content = ''.join(part.get('text', '') for part in parts).strip()
	if not content: return {}
	content = extract_json_object(content)
	return content

def make_similar_prompt(media_type, meta, limit):
	meta_get = meta.get
	title, year = meta_get('title').strip(), meta_get('year', '')
	plot, genre = meta_get('plot', '').strip(), ','.join([i for i in meta_get('genre') if i]) if meta_get('genre') else 'unknown'
	keywords = ','.join([i['name'] for i in meta_get('keywords', {}).get('keywords')]) if meta_get('keywords', {}).get('keywords') else ''
	prompt = similar_prompt()
	prompt = prompt.replace('MEDIA_TYPE_HERE', media_type).replace('TITLE_HERE', title).replace('YEAR_HERE', year)
	prompt = prompt.replace('PLOT_HERE', plot).replace('GENRES_HERE', genre).replace('KEYWORDS_HERE', keywords)
	prompt = prompt.replace('LIMIT_HERE', str(limit))
	return prompt

def model_info(model_id, media_type, meta, limit):
	return {'similar':
{'headers': {'Content-Type': 'application/json', 'x-goog-api-key': get_api()},
'url': 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % model_id,
'payload': {'contents': [{'role': 'user', 'parts': [{'text': make_similar_prompt(media_type, meta, limit)}]}]},
'parse': similar_parse}
}

def model_present(model_id):
	return model_id in models()

def get_api():
	return get_setting('redlight.google_api')
