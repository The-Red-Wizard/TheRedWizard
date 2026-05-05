# -*- coding: utf-8 -*-

from six.moves.urllib_parse import parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils

DOM = client_utils.parseDOM


class source:
    def __init__(self):
        self.results = []
        self.domains = ['tvseries.video']
        self.base_link = 'https://www.tvseries.video'
        self.search_link = '/search?q=%s'
        self.notes = 'Sources seem to be all holders like 2embed which fail to work on my end.'


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
        url = urlencode(url)
        return url


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url = {'imdb': imdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
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
            season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            search_url = self.base_link + self.search_link % cleantitle.get_plus(title)
            type_check = 'Series' if 'tvshowtitle' in data else 'Movies'
            headers = {'User-Agent': client.UserAgent, 'Referer': self.base_link}  
            html = client.scrapePage(search_url, headers=headers).text   # headers added
            r = DOM(html, 'div', attrs={'class': r'.+?content'})
            r = [(DOM(i, 'a', ret='href'), DOM(i, 'span', attrs={'class': 'card-title'}), DOM(i, 'span', attrs={'class': 'viddate'}), DOM(i, 'span', attrs={'class': 'vidtype'})) for i in r]
            r = [(i[0][0], i[1][0], i[2][0], i[3][0]) for i in r if len(i[0]) > 0 and len(i[1]) > 0 and len(i[2]) > 0 and len(i[3]) > 0]
            if 'tvshowtitle' in data:
                url = [i[0] for i in r if cleantitle.match_alias(i[1], aliases) and cleantitle.match_year(i[2], year, data['year']) and i[3] == type_check][0]
                url = self.base_link + url
                sepi = '/season-%s-episode-%s-' % (season, episode)
                r = client.scrapePage(url, headers=headers).text   # headers added
                r = DOM(r, 'div', attrs={'class': 'eplist'})[0]
                r = DOM(r, 'a', ret='href')
                url = [i for i in r if sepi in i][0]
            else:
                url = [i[0] for i in r if cleantitle.match_alias(i[1], aliases) and cleantitle.match_year(i[2], year) and i[3] == type_check][0]
            url = self.base_link + url
            html = client.scrapePage(url, headers=headers).text   # headers added
            links = []
            links += DOM(html, 'div', ret='data-vid')
            links += DOM(html, 'a', ret='data-vid1')
            for link in links:
                try:
                    if link.startswith('/vsp2/'):
                        continue # Blocked for now till i figure it out lol.
                        #link = self.base_link + link
                        #r = client.scrapePage(link).text
                        #log_utils.log('/vsp2/ .url: '+repr(r.url))
                        #log_utils.log('/vsp2/ .text: '+repr(r.text))
                    #else:
                    for source in scrape_sources.process(hostDict, link):
                        if scrape_sources.check_host_limit(source['source'], self.results):
                            continue
                        self.results.append(source)
                except:
                    #log_utils.log('sources', 1)
                    pass
            return self.results
        except:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        return url


