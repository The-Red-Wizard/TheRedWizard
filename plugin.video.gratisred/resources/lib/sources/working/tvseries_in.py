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
        self.domains = ['tvseries.in', 'mobiletvshows.site']
        self.base_link = 'https://www.tvseries.in'
        self.search_link = '/search.php?search={}&beginsearch=Search&vsearch=&by=series'
        self.headers = client.dnt_headers
        self.notes = 'for TV shows only, not perfect, but works. Still working on the movie site.'


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
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            aliases = eval(data['aliases'])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            check_term = f"{title}" if 'tvshowtitle' in data else title
            search_url = self.base_link + self.search_link.format(title)
            
            # this is a TV series site ONLY
            if not 'tvshowtitle' in data:
                return

            self.cookie = client.request(self.base_link, output='cookie', timeout='10')
            results = client.scrapePage(search_url, headers=self.headers).text
            pattern = fr"(?i)\b{check_term}\b"
            results = DOM(results, 'div', attrs={'id': pattern})

            if not results:
                return

            result_url = DOM(results, 'a', ret='href')
            result_url = result_url[0] if result_url else None

            if not result_url:
                return

            if not result_url.startswith(('http', '/')):
                result_url = f'{self.base_link}/{result_url}'

            results2 = client.scrapePage(result_url, headers=self.headers).text
            check_season = f'Season {season}'
            pattern2 = r'(?i)containsseason'
            results_season = DOM(results2, 'div', attrs={'itemprop': pattern2})
            results_season2 = DOM(results_season, 'div')
            results_season3 = [(DOM(i, 'a', ret='href'), DOM(i, 'span')) for i in results_season2]
            results_season3 = [(i[0][0], i[1][0]) for i in results_season3 if len(i[0]) > 0 and len(i[1]) > 0]  # FLATTEN
            result_url_season = [i[0] for i in results_season3 if check_season == i[1]]

            if not result_url_season:
                return

            result_url_season = result_url_season[0] if result_url_season else None

            if not result_url_season.startswith(('http', '/')):
                result_url = f'{self.base_link}/{result_url_season}'

            results3 = client.request(result_url, headers=self.headers)
            results3 = client_utils.clean_html(results3)
            check_episode = f'S{int(season):02}E{int(episode):02}'
            check_episode = check_episode.lower()
            pattern3 = r'mainbox\s*([0-9]?)'   #mainbox[digit]
            results7 = DOM(results3, 'div', attrs={'class': pattern3})   
            result_episodes = [i for i in results7 if check_episode in i.lower()]   # find S01E03 from list
            result_episodes2 = list(zip(DOM(result_episodes, 'a', ret='href'), DOM(result_episodes, 'a')))
            links = []
            infos = []
            pattern4 = r'(\w*link[0-9]?)'   # dlink2 or filelink9 or downloadlink or fileslink3

            for link, info in result_episodes2:
                if not link.startswith(('http', '/')):
                    link = f'{self.base_link}/{link}'

                response8 = client.request(link, headers=self.headers, cookie=self.cookie, timeout=20)
                response8 = client_utils.clean_html(response8)
                file_links = DOM(response8, 'a', attrs={'id': pattern4}, ret='href')
                links.extend(file_links)
                info = client_utils.remove_codes(info)
                infos.extend([info] * len(file_links))

            result_links = list(zip(links, infos))
            result_links = list(dict.fromkeys(result_links))  # remove dups
            links = []
            infos = []

            for link, info in result_links:
                if not link.startswith(('http', '/')):
                    link = f'{self.base_link}/{link}'

                response9 = client.request(link, headers=self.headers, cookie=self.cookie, timeout=30)
                file_links = DOM(response9, 'input', attrs={'name': pattern4}, ret='value')
                links.extend(file_links)
                infos.extend([info] * len(file_links))

            final_links = list(zip(links, infos))
            final_links = list(dict.fromkeys(final_links))  # remove dups   
        
            for link, info in final_links:
                info = '720p' if 'webm' in info.lower() else info
                item = scrape_sources.make_direct_item(hostDict, link, host='Direct', info=info, referer=None, prep=True)
                if item:
                    self.results.append(item)                
            return self.results
            
        except:
            return self.results



    def resolve(self, url):
        # log_utils.log('url =' + repr(url), 1)
        return url


