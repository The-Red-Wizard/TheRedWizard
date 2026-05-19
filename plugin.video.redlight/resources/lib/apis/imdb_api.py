# -*- coding: utf-8 -*-
import re
import json
import requests
from html import unescape
from caches.base_cache import connect_database
from caches.main_cache import cache_object
from caches.settings_cache import get_setting
from modules.dom_parser import parseDOM
from modules.kodi_utils import sleep
from modules.utils import remove_accents, replace_html_codes, normalize
# from modules.kodi_utils import logger

GQL_URL  = 'https://graphql.imdb.com/'
GQL_HEADERS = {
	'Content-Type': 'application/json',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
	'Accept': 'application/json', 'Origin': 'https://www.imdb.com', 'Referer': 'https://www.imdb.com/',
	'x-imdb-client-name': 'imdb-web-next-localized', 'x-imdb-user-language': 'en-US', 'x-imdb-user-country': 'US'}

def _clean(text):
	if not text: return ''
	text = text.replace('<br/><br/>', '\n').replace('<br/>', '\n').replace('<br>', '\n')
	text = re.sub(r'<a[^>]*>', '', text).replace('</a>', '')
	text = re.sub(r'<[^>]+>', '', text)
	text = replace_html_codes(text)
	text = remove_accents(text)
	return text.strip()

def imdb_extras(imdb_id):
	string = 'imdb_extras_%s' % imdb_id
	params = {'action': 'imdb_extras', 'imdb_id': imdb_id}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_more_like_this(imdb_id):
	string = 'imdb_more_like_this_%s' % imdb_id
	params = {'action': 'imdb_more_like_this', 'imdb_id': imdb_id}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_people_id(actor_name):
	name = actor_name.lower()
	string = 'imdb_people_id_%s' % name
	url, url_backup = 'https://sg.media-imdb.com/suggests/%s/%s.json' % (name[0], name.replace(' ', '%20')), 'https://www.imdb.com/search/name/?name=%s' % name
	params = {'url': url, 'action': 'imdb_people_id', 'name': name, 'url_backup': url_backup}
	return cache_object(get_imdb, string, params, False, 8736)[0]

def imdb_people_trivia(imdb_id):
	string = 'imdb_people_trivia_%s' % imdb_id
	params = {'action': 'imdb_people_trivia', 'imdb_id': imdb_id}
	return cache_object(get_imdb, string, params, False, 168)[0]

def imdb_year_check(imdb_id):
	url = 'https://v2.sg.media-imdb.com/suggestion/t/%s.json' % imdb_id
	string = 'imdb_year_check%s' % imdb_id
	params = {'url': url, 'imdb_id': imdb_id, 'action': 'imdb_year_check'}
	return cache_object(get_imdb, string, params, False, 720)[0]

def get_imdb(params):
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
					'Accept-Language':'en-us,en;q=0.5'}
	imdb_list = []
	action = params.get('action')
	imdb_id = params.get('imdb_id', '')
	next_page = None
	if action == 'imdb_extras':
		trivia, blunders, reviews, parentsguide = [], [], [], []
		data = {'query': imdb_extras_query % imdb_id}
		result = requests.post(GQL_URL, json=data, headers=GQL_HEADERS, timeout=10)
		result = result.json().get('data', {}).get('title', {})
		try:
			count = 1
			for i in sorted(result['reviews']['edges'], key=lambda k: k['node']['submissionDate'], reverse=True):
				try:
					content = unescape(_clean(i['node']['text']['originalText']['plaidHtml']))
					if not content: continue
					try: spoiler = i['node']['spoiler']
					except: spoiler = False
					try:
						rating = i['node']['authorRating']
						rating = str(rating) if rating is not None else '-'
					except: rating = '-'
					try: title = i['node']['summary']['originalText']
					except: title = '-----'
					try: date = i['node']['submissionDate']
					except: date = '-----'
					review = '[B]%02d. [I]%s/10 - %s - %s[/I][/B][CR][CR]%s' % (count, rating, date, title, content)
					if spoiler: review = '[B][COLOR red][CONTAINS SPOILERS][/COLOR][CR][/B]' + review
					count += 1
					reviews.append(review)
				except: pass
		except: pass
		try:
			count = 1
			for i in sorted(result['trivia']['edges'], key=lambda k: k['node']['interestScore']['usersVoted'], reverse=True):
				try: trivia.append('[B]TRIVIA %02d.[/B][CR][CR]%s' % (count, unescape(_clean(i['node']['displayableArticle']['body']['plaidHtml']))))
				except: pass
				count += 1
		except: pass
		try:
			count = 1
			for i in sorted(result['goofs']['edges'], key=lambda k: k['node']['interestScore']['usersVoted'], reverse=True):
				try: blunders.append('[B]BLUNDERS %02d.[/B][CR][CR]%s' % (count, unescape(_clean(i['node']['displayableArticle']['body']['plaidHtml']))))
				except: pass
				count += 1
		except: pass
		try:
			title_converter = {'nudity': 'Sex & Nudity', 'violence': 'Violence & Gore', 'profanity': 'Profanity',
								'alcohol': 'Alcohol, Drugs & Smoking', 'frightening': 'Frightening & Intense Scenes'}
			for i in result['parentsGuide']['categories']:
				try:
					title = title_converter[i['category']['id'].lower()]
					ranking = i['severity']['id'].replace('Votes', '')
					try:
						listings = [unescape(_clean(x['node']['text']['plaidHtml'])) for x in i['guideItems']['edges']]
						content = '\n\n'.join(['%02d. %s' % (count, i) for count, i in enumerate(listings, 1)])
					except: content, listings = [], []
					total_count = len(listings)
					parentsguide.append({'title': title, 'ranking': ranking, 'content': content, 'total_count': total_count})
				except: pass
		except: pass
		imdb_list = {'reviews': reviews, 'trivia': trivia, 'blunders': blunders, 'parentsguide': parentsguide}
	elif action == 'imdb_people_trivia':
		def _process():
			for count, edge in enumerate(edges, 1):
				try:
					content = _clean(edge['node']['text']['plaidHtml'])
					content = '[B]TRIVIA %02d.[/B][CR][CR]%s' % (count, content)
					yield content
				except: pass
		try:
			payload = {'query': 'query($id:ID!){name(id:$id){trivia(first:50){edges{node{text{plaidHtml}}}}}}', 'variables': {'id': imdb_id}}
			result = requests.post(GQL_URL, json=payload, headers=GQL_HEADERS, timeout=10).json()
			edges = result['data']['name']['trivia']['edges']
		except: edges = []
		imdb_list = list(_process())
	elif action == 'imdb_more_like_this':
		def _process():
			for edge in edges:
				try:
					_id = edge['node']['id']
					if _id.startswith('tt'): yield (_id)
				except: pass
		try:
			payload = {'query': 'query($id:ID!){title(id:$id){moreLikeThisTitles(first:12){edges{node{id}}}}}', 'variables': {'id': imdb_id}}
			result = requests.post(GQL_URL, json=payload, headers=GQL_HEADERS, timeout=10).json()
			edges = result['data']['title']['moreLikeThisTitles']['edges']
		except: edges = []
		imdb_list = list(_process())
		imdb_list = [i for n, i in enumerate(imdb_list) if i not in imdb_list[n + 1:]]
	elif action == 'imdb_people_id':
		try:
			name = params['name']
			result = requests.get(params['url'], timeout=20)
			results = json.loads(re.sub(r'imdb\$(.+?)\(', '', result.text)[:-1])['d']
			imdb_list = [i['id'] for i in results if i['id'].startswith('nm') and i['l'].lower() == name][0]
		except: imdb_list = []
		if not imdb_list:
			try:
				result = requests.get(params['url_backup'], timeout=20, headers=headers)
				result = remove_accents(result.text)
				result = result.replace('\n', ' ')
				result = parseDOM(result, 'div', attrs={'class': 'lister-item-image'})[0]
				imdb_list = re.search(r'href="/name/(.+?)"', result, re.DOTALL).group(1)
			except: pass
	elif action == 'imdb_year_check':
		try:
			result = requests.get(params['url'], timeout=5).json()
			imdb_list = [str(i['y']) for i in result['d'] if i['id'] == imdb_id][0]
		except: pass
	return (imdb_list, next_page)

def clear_imdb_cache(silent=False):
	try:
		dbcon = connect_database('maincache_db')
		results = dbcon.execute("SELECT id FROM maincache WHERE id LIKE ?", ('imdb_%',)).fetchall()
		dbcon.execute("DELETE FROM maincache WHERE id LIKE ?", ('imdb_%',))
		return True
	except: return False

def refresh_imdb_meta_data(imdb_id):
	try:
		insert1, insert2 = '%%%s' % imdb_id, '%%%s_%%' % imdb_id
		dbcon = connect_database('maincache_db')
		dbcon.execute("DELETE FROM maincache WHERE id LIKE ?", (insert1,))
		dbcon.execute("DELETE FROM maincache WHERE id LIKE ?", (insert2,))
		return True
	except: return False

imdb_extras_query = '''\
query {
  title(id: "%s") {
    id
    titleText {
      text
    }
    trivia(first: 20) {
      edges {
        node {
          displayableArticle {
            body {
              plaidHtml
            }
          }
          interestScore {
            usersVoted
          }
        }
      }
    }
    goofs(first: 20) {
      edges {
        node {
          displayableArticle {
            body {
              plaidHtml
            }
          }
          interestScore {
            usersVoted
          }
        }
      }
    }
    reviews(first: 50) {
      edges {
        node {
          spoiler
          author {
            nickName
          }
          authorRating
          summary {
            originalText
          }
          text {
            originalText {
              plaidHtml
            }
          }
          submissionDate
        }
      }
    }
    parentsGuide {
      categories {
        category {
          id
        }
        guideItems(first: 10) {
          edges {
            node {
              isSpoiler
              text {
                plaidHtml
              }
            }
          }
        }
        severity {
          id
          votedFor
        }
      }
    }
  }
}'''
