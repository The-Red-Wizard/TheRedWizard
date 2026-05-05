# -*- coding: utf-8 -*-

import re
import requests

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import cleantitle
from resources.lib.modules import log_utils

DOM = client_utils.parseDOM
CLEAN = client_utils.remove_codes


def bing(search_query, parse=False):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://www.bing.com'}
        search_url = 'https://www.bing.com/search?q=%s' % search_query
        #log_utils.log('bing search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('bing search_html: \n' + repr(search_html))
        if parse:
            results = DOM(search_html, 'li', attrs={'class': 'b_algo'})
            results = [(DOM(i, 'cite'), DOM(i, 'h2')) for i in results]
            results = [(i[0][0], i[1][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0]
            results = [(CLEAN(i[0]), CLEAN(i[1])) for i in results]
            #log_utils.log('bing results: \n' + repr(results))
            return results
        return search_html
    except:
        log_utils.log('bing', 1)
        return


def duckduckgo(search_query):
    try:
        if not search_query:
            return
        search_data = {'q': search_query}
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://duckduckgo.com'}
        #https://lite.duckduckgo.com/lite
        search_url = 'https://html.duckduckgo.com/html/'
        search_html = requests.post(search_url, headers=search_headers, data=search_data, verify=False).content
        #log_utils.log('duckduckgo search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('duckduckgo', 1)
        return


def ecosia(search_query, parse=False):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://www.ecosia.org'}
        search_url = 'https://www.ecosia.org/search?q=%s' % search_query
        #log_utils.log('ecosia search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('ecosia search_html: \n' + repr(search_html))
        if parse:
            results = DOM(search_html, 'div', attrs={'class': 'result__title'})
            results = [(DOM(i, 'a', ret='href'), DOM(i, 'h2', attrs={'class': 'result-title__heading'})) for i in results]
            results = [(i[0][0], i[1][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0]
            results = [(CLEAN(i[0]), CLEAN(i[1])) for i in results]
            #log_utils.log('ecosia results: \n' + repr(results))
            return results
        return search_html
    except:
        log_utils.log('ecosia', 1)
        return


def google(search_query):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://www.google.com'}
        search_url = 'https://www.google.com/search?q=%s' % search_query
        #log_utils.log('google search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('google search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('google', 1)
        return


def startpage(search_query):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://www.startpage.com'}
        #https://www.startpage.com/sp/search
        search_url = 'https://www.startpage.com/do/search?q=%s' % search_query
        #log_utils.log('startpage search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('startpage search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('startpage', 1)
        return


def swisscows(search_query):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://swisscows.com'}
        search_url = 'https://swisscows.com/en/web?query=%s' % search_query
        #log_utils.log('swisscows search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('swisscows search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('swisscows', 1)
        return


def yahoo(search_query):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://search.yahoo.com'}
        search_url = 'https://search.yahoo.com/search?p=%s' % search_query
        #log_utils.log('yahoo search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('yahoo search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('yahoo', 1)
        return


def yandex(search_query):
    try:
        if not search_query:
            return
        search_headers = {'User-Agent': client.UserAgent, 'Referer': 'https://yandex.com'}
        search_url = 'https://yandex.com/search/?text=%s' % search_query
        #log_utils.log('yandex search_url: \n' + repr(search_url))
        search_html = client.scrapePage(search_url, headers=search_headers).text
        #log_utils.log('yandex search_html: \n' + repr(search_html))
        return search_html
    except:
        log_utils.log('yandex', 1)
        return


def make_search_query(domain, title, imdb=None, year=None, season=None, episode=None, domainprefix='&sites='):
    try:
        if not domain:
            return
        search_title = imdb if not imdb == None else cleantitle.get_plus(title)
        search_term = '%s+%s' % (search_title, year) if not year == None else search_title
        if not (season and episode) == None:
            season = '%02d' % int(season)
            episode = '%02d' % int(episode)
            search_query = '%s+s%se%s+%s%s' % (search_term, str(season), str(episode), domainprefix, domain)
        elif not season == None:
            season = '%02d' % int(season)
            search_query = '%s+Season+%s+%s%s' % (search_term, str(season), domainprefix, domain)
        else:
            search_query = '%s+%s%s' % (search_term, domainprefix, domain)
        return search_query
    except:
        log_utils.log('make_search_query', 1)
        return


