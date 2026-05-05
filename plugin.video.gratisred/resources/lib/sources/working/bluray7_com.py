# -*- coding: utf-8 -*-

import re
import requests

from six.moves.urllib_parse import parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['bluray7.com']
        self.base_link = 'https://bluray7.com'
        self.search_link = '/?s=%s'
        self.ajax_link = '/wp-admin/admin-ajax.php'


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
            self.session = requests.Session()
            self.cookie = client.request(self.base_link, output='cookie', timeout='5')
            html = client.request(search_url, cookie=self.cookie)
            items = client_utils.parseDOM(html, 'div', attrs={'class': 'result-item'})
            r = [(client_utils.parseDOM(i, 'a', ret='href'), client_utils.parseDOM(i, 'img', ret='alt')) for i in items]
            r = [(i[0][0], i[1][0]) for i in r if len(i[0]) > 0 and len(i[1]) > 0]
            r = [(i[0], re.findall(r'(.+?) [(](\d{4})[)]', i[1])) for i in r]
            r = [(i[0], i[1][0]) for i in r if len(i[1]) > 0]
            url = [i[0] for i in r if cleantitle.match_alias(i[1][0], aliases) and cleantitle.match_year(i[1][1], year)][0]
            html = client.request(url, cookie=self.cookie)
            try:
                qual = client_utils.parseDOM(html, 'strong', attrs={'class': 'quality'})[0]
            except:
                qual = ''
            customheaders = {
                'Host': self.domains[0],
                'Accept': '*/*',
                'Origin': self.base_link,
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': client.UserAgent,
                'Referer': url,
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            post_link = self.base_link + self.ajax_link
            try:
                results = re.compile(r'''data-type=['"](.+?)['"] data-post=['"](.+?)['"] data-nume=['"](\d+)['"]>''', re.DOTALL).findall(html)
                for data_type, data_post, data_nume in results:
                    try:
                        payload = {'action': 'doo_player_ajax', 'post': data_post, 'nume': data_nume, 'type': data_type}
                        r = self.session.post(post_link, headers=customheaders, data=payload)
                        i = r.json()
                        if not i['type'] == 'iframe':
                            continue
                        p = i['embed_url'].replace('\\', '')
                        for source in scrape_sources.process(hostDict, p, info=qual):
                            if scrape_sources.check_host_limit(source['source'], self.results):
                                continue
                            self.results.append(source)
                    except:
                        #log_utils.log('sources', 1)
                        pass
            except:
                #log_utils.log('sources', 1)
                pass
            try:
                tbody = client_utils.parseDOM(html, 'tbody')
                downloads = client_utils.parseDOM(tbody, 'a', ret='href')
                for download in downloads:
                    try:
                        html = client.request(download, cookie=self.cookie)
                        link = client_utils.parseDOM(html, 'a', attrs={'id': 'link'}, ret='href')[0]
                        for source in scrape_sources.process(hostDict, link, info=qual):
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


