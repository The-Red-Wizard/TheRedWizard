# -*- coding: utf-8 -*-

import re
import base64

from six import ensure_text
from six.moves.urllib_parse import parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['tvmovieflix.com']
        self.base_link = 'https://tvmovieflix.com'
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
            search_url = self.base_link + self.search_link % cleantitle.get_plus(title)
            html = client.scrapePage(search_url).text
            r = client_utils.parseDOM(html, 'div', attrs={'id': r'post-.*?'})
            r = [(client_utils.parseDOM(i, 'a', attrs={'class': 'title'}, ret='href'), client_utils.parseDOM(i, 'a', attrs={'class': 'title'}), re.findall(r'<span>(\d{4})</span>', i)) for i in r]
            r = [(i[0][0], i[1][0], i[2][0]) for i in r if len(i[0]) > 0 and len(i[1]) > 0 and len(i[2]) > 0]
            url = [i[0] for i in r if cleantitle.match_alias(i[1], aliases) and cleantitle.match_year(i[2], year)][0]
            page = client.scrapePage(url).text
            links = []
            try:
                results = client_utils.parseDOM(page, 'div', attrs={'id': 'manual'}, ret='onclick')
                for result in results:
                    links += re.findall(r'''loadEmbed\(['"]([^'"]+)['"]\)''', result, re.DOTALL | re.IGNORECASE)
            except:
                #log_utils.log('sources', 1)
                pass
            try:
                servers = re.findall(r'''var\s+Servers\s*=\s*\{([^\]]+)}''', page, re.DOTALL | re.IGNORECASE)[0]
                links += re.findall(r''':['"]([^'"]+)['"]''', servers, re.DOTALL | re.IGNORECASE)
            except:
                #log_utils.log('sources', 1)
                pass
            for link in links:
                try:
                    link = client_utils.replaceHTMLCodes(link)
                    if not (link.startswith('http') or link.startswith('//')):
                        continue
                    if any(x in link for x in self.domains):
                        if '/embed.php?' in link:
                            vhtml = client.scrapePage(link).text
                            vlink = re.compile(client_utils.regex_pattern6).findall(vhtml)[0]
                            vlink = base64.b64decode(vlink.replace("\/", "/"))
                            vlink = ensure_text(vlink, errors='ignore')
                            item = scrape_sources.make_direct_item(hostDict, vlink, host='Direct', info=None, referer=None, prep=True)
                            if item:
                                if not scrape_sources.check_host_limit(item['source'], self.results):
                                    self.results.append(item)
                        elif '/player.php?' in link:
                            link = client.request(link, timeout='6', output='geturl')
                        else:
                            continue
                    else:
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


