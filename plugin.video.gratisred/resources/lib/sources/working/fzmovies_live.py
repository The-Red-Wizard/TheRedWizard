# -*- coding: utf-8 -*-

import re

from six.moves.urllib_parse import parse_qs, urlencode, urlparse

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
from resources.lib.modules import log_utils

DOM = client_utils.parseDOM

class source:
    def __init__(self):
        self.results = []
        self.domains = ['fzmovies.live']
        self.base_link = 'https://www.fzmovies.live'
        self.search_link = '/advancedsearch.php?'
        self.headers = client.dnt_headers
        self.notes = 'for Movies only'


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        url = {'imdb': imdb, 'tmdb': tmdb, 'title': title, 'localtitle': localtitle, 'aliases': aliases, 'year': year}
        url = urlencode(url)
        return url


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url = {'imdb': imdb, 'tmdb': tmdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
        url = urlencode(url)
        return url


    def episode(self, url, imdb, tmdb, tvdb, title, premiered, season, episode):
        if not url:
            return
        url = parse_qs(url)
        url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
        url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
        url = urlencode(url)
        return url


    def sources(self, url, hostDict):
        try:
            if not url:
                return self.results
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            aliases = eval(data['aliases'])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            title_imdb = data['imdb']
            # season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            check_term = f'{title}' if 'tvshowtitle' in data else title

            params = {
                'category': 'Hollywood',
                'year': data['year'],
                'year2': data['year'],
                'moviename': title
            }

            search_url = f"{self.base_link}{self.search_link}{urlencode(params)}"

            if 'tvshowtitle' in data:    # this is a Movie site ONLY
                return

            self.cookie = client.request(self.base_link, output='cookie', timeout='10')
            results = client.scrapePage(search_url, headers=self.headers, cookie=self.cookie).text
            pattern = fr'(?i)\b\w+\b'  #  any word
            results = DOM(results, 'div', attrs={'class': 'mainbox'})

            if not results:
                return

            results2 = [i for i in results if title_imdb in i]   # IMDB value is what we're looking for

            if not results2:
                return

            result_url = DOM(results2, 'a', ret='href', attrs={'id': pattern})
            result_url = list(dict.fromkeys(result_url))  # remove dups
            result_url = result_url[0] if result_url else None

            if not result_url:
                return

            if not result_url.startswith(('http', '/')):
                result_url = f'{self.base_link}/{result_url}'

            results2 = client.scrapePage(result_url, headers=self.headers, cookie=self.cookie).text
            pattern2 = r'(d.*?link[0-9]?)'
            results3 = DOM(results2, 'a', ret='href', attrs={'id': pattern2})
            results4 = DOM(results2, 'a', attrs={'id': pattern2})
            results5 = list(zip(results3, results4))
            results5 = list(dict.fromkeys(results5))  # remove dups
            links = []
            infos = []

            for link, info in results5:
                if not link.startswith(('http', '/')):
                    link = f'{self.base_link}/{link}'
                response8 = client.request(link, headers=self.headers, cookie=self.cookie, timeout=20)
                file_links = DOM(response8, 'a', attrs={'id': pattern2}, ret='href')
                links.extend(file_links)  # add the links
                infos.extend([info] * len(file_links))  # add the same info to each of the file_links found.

            result_links = list(zip(links, infos))
            result_links = list(dict.fromkeys(result_links))  # remove dups
            links = []
            infos = []

            for link, info in result_links:
                if not link.startswith(('http', '/')):
                    link = f'{self.base_link}/{link}'

                response9 = client.request(link, headers=self.headers, cookie=self.cookie, timeout=20)
                file_links = DOM(response9, 'a', attrs={'id': pattern2}, ret='href')
                links.extend(file_links)
                infos.extend([info] * len(file_links))

            final_links = list(zip(links, infos))
            final_links = list(dict.fromkeys(final_links))  # remove dups
            links = []
            infos = []
            pattern5 = r'(download[0-9]?)'

            for link, info in final_links:
                if not link.startswith(('http', '/')):
                    link = f'{self.base_link}/{link}'
                response10 = client.request(link, headers=self.headers, cookie=self.cookie, timeout=20)
                file_links = DOM(response10, 'input', attrs={'name': pattern5}, ret='value')
                links.extend(file_links)
                infos.extend([info] * len(file_links))
            final_links2 = list(zip(links, infos))
            final_links2 = list(dict.fromkeys(final_links2))  # remove dups

            for link, info in final_links2:
                info = '720p' if 'webm' in info.lower() else info
                item = scrape_sources.make_direct_item(hostDict, link, host='Direct', info=info, referer=None, prep=True)
                if item:
                    self.results.append(item)                
            return self.results
            
        except:
            return self.results


    def resolve(self, url):
        resp = client.request(url, headers=self.headers, output='file_size')
        if not resp:
            url = None
        if resp == 0:
            url = None
        return url