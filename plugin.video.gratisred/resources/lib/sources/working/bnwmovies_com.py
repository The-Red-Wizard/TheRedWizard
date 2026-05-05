# -*- coding: utf-8 -*-

from six.moves.urllib_parse import parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['bnwmovies.com']
        self.base_link = 'https://bnwmovies.com'
        self.search_link = '/?s=%s'


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
        url = urlencode(url)
        return url


    def sources(self, url, hostDict):
        try:
            if not url:
                return self.results
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            aliases = eval(data['aliases'])
            title = data['title']
            year = data['year']
            if int(year) > 1970:
                return self.results
            search_url = self.base_link + self.search_link % cleantitle.get_plus(title)
            search_html = client.scrapePage(search_url).text
            results = client_utils.parseDOM(search_html, 'div', attrs={'class': 'post'})
            result = [(client_utils.parseDOM(i, 'a', ret='href'), client_utils.parseDOM(i, 'a')) for i in results]
            result = [(i[0][0], i[1][0]) for i in result if len(i[0]) > 0 and len(i[1]) > 0]
            page_url = [i[0] for i in result if cleantitle.match_alias(i[1], aliases)][0]
            page_html = client.scrapePage(page_url).text
            links = client_utils.parseDOM(page_html, 'source', ret='src')
            for link in links:
                try:
                    item = scrape_sources.make_direct_item(hostDict, link, host=None, info=None, referer=page_url, prep=True)
                    if item:
                        if not scrape_sources.check_host_limit(item['source'], self.results):
                            self.results.append(item)
                except:
                    #log_utils.log('sources', 1)
                    pass
            return self.results
        except:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        return url


