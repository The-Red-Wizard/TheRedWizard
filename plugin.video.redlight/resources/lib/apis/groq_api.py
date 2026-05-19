# -*- coding: utf-8 -*-
from caches.settings_cache import get_setting
from modules.utils import extract_json_object
# from modules.kodi_utils import logger

# GROQ_MODELS = ('llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'meta-llama/llama-4-maverick-17b-128e-instruct', 'openai/gpt-oss-120b', 'moonshotai/kimi-k2-instruct')

def models():
	return ('llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'openai/gpt-oss-120b')

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
	content = data.get('choices', [{}])[0].get('message', {}).get('content', '') or ''
	if not content: return {}
	return extract_json_object(content)

def model_info(model_id, media_type, meta, limit):
	return {'similar':
{'headers': {'Authorization': 'Bearer %s' % get_api(), 'Content-Type': 'application/json'},
'url': 'https://api.groq.com/openai/v1/chat/completions',
'payload': {'model': model_id, 'messages': [{'role': 'user', 'content': make_similar_prompt(media_type, meta, limit)}], 'temperature': 0.2,
'response_format': {'type': 'json_object'}, 'max_tokens': 900}, 'parse': similar_parse}
}

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

def model_present(model_id):
	return model_id in models()

def get_api():
	return get_setting('redlight.groq_api')
