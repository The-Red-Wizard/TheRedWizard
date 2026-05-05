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
        self.domains = ['downloads-anymovies.co', 'downloads-anymovies.com']
        self.base_link = 'https://www.downloads-anymovies.co'
        self.search_link = '/search.php?zoom_query=%s+%s'
        self.notes = 'looks like the search has blockage now.'


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
            search_title = cleantitle.get_plus(title)
            search_url = self.base_link + self.search_link % (search_title, year)
            search_html = client.scrapePage(search_url).text
            try:
                r = client_utils.parseDOM(search_html, 'div', attrs={'class': 'result_title'})
                r = zip(client_utils.parseDOM(r, 'a', ret='href'), client_utils.parseDOM(r, 'a'))
                r = [(i[0], re.findall(r'(?:Watch|)(.+?)\((\d+)', i[1])) for i in r]
                r = [(i[0], i[1][0]) for i in r if len(i[1]) > 0]
                page_url = [i[0] for i in r if cleantitle.match_alias(i[1][0], aliases) and cleantitle.match_year(i[1][1], year)][0]
            except:
                page_url = self.base_link + '/added_movies/%s-%s-watch-full-movie-online-free.html' % (cleantitle.geturl(title), year)
            page_html = client.scrapePage(page_url).text
            links = client_utils.parseDOM(page_html, 'a', attrs={'target': '_blank'}, ret='href')
            for link in links:
                try:
                    if any(x in link for x in ['report-error.html', 'statcounter.com']):
                        continue
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


