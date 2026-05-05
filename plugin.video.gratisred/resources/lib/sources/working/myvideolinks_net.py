# -*- coding: utf-8 -*-

import re
from six.moves.urllib_parse import parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['top.myvideolinks.net', 'new.myvid.one', 'beta.myvid.one', 'get.myvideolinks.net',
            'dl.myvideolinks.net', 'new.myvideolinks.net', 'to.myvideolinks.net', 'go.myvideolinks.net',
            'net.myvideolinks.net', 'forums.myvideolinks.net', 'myvideolinks.net', 'ina.myvideolinks.net'
        ]
        self.base_link = 'https://myvideolinks.org'
        self.search_link = '/?s=%s'


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        url = {'imdb': imdb, 'title': title, 'year': year}
        url = urlencode(url)
        return url


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url = {'imdb': imdb, 'tvshowtitle': tvshowtitle, 'year': year}
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
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
            search = '%s %s' % (title, hdlr) if 'tvshowtitle' in data else data['imdb']
            search_url = self.base_link + self.search_link % cleantitle.get_plus(search)
            search_html = client.scrapePage(search_url).text
            search_result = client_utils.parseDOM(search_html, 'article')
            search_result = [(client_utils.parseDOM(i, 'a', ret='href')[0], client_utils.parseDOM(i, 'a')[0], re.findall(r'imdb.com/title/(.+?)/">', i)[0]) for i in search_result]
            try:
                result_urls = [i[0] for i in search_result if search in i[2]]
            except:
                result_urls = [i[0] for i in search_result if (title.lower() and hdlr.lower() in i[1].lower())]
            for result_url in result_urls:
                try:
                    page_html = client.scrapePage(result_url).text
                    page_links = client_utils.parseDOM(page_html, 'a', attrs={'class': 'autohyperlink'}, ret='href')
                    page_links += client_utils.parseDOM(page_html, 'iframe', ret='src')
                    for link in page_links:
                        try:
                            if any(i in link for i in (['imdb.com', 'youtube.com', 'turbobit.net', 'streamzz.to'] or self.domains)):
                                continue
                            for source in scrape_sources.process(hostDict, link, info=result_url):
                                if scrape_sources.check_host_limit(source['source'], self.results):
                                    continue
                                self.results.append(source)
                        except:
                            #log_utils.log('sources', 1)
                            pass
                except:
                    #log_utils.log('sources', 1)
                    pass
            return self.results
        except:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        return url


