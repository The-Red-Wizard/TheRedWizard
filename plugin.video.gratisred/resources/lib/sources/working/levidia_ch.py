
import re
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
        self.domains = ['levidia.ch']
        self.base_link = 'https://www.levidia.ch'
        self.search_link = '/search.php?q=%s'
        self.headers = client.dnt_headers
        self.notes = 'sim/dupe site to goojara.to & supernova.to i think.'


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
            url = self.base_link + self.search_link % cleantitle.get_utf8(title)
            #log_utils.log('search_url: '+repr(url))
            self.cookie = client.request(self.base_link, headers=self.headers, output='cookie', timeout='10')
            cookie_dict = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in self.cookie.split('; ')}
            r = client.request(url, headers=self.headers, cookie=self.cookie)
            r = DOM(r, 'div ', attrs={'class': 'mainlink'})
            #log_utils.log('r1: '+repr(r))
            r = list(zip(DOM(r, 'a', ret='href'), DOM(r, 'a')))
            #log_utils.log('r2: '+repr(r))
            r = [(url, client_utils.remove_tags(html)) for url, html in r]
            #log_utils.log('r3: '+repr(r))
            r = [(url, re.sub(r'\(\d{4}\)', '', html), re.findall(r'\((\d{4})\)', html)[0]) for url, html in r]
            #log_utils.log('r4: '+repr(r))
            r = [(i[0], i[1], i[2]) for i in r if len(i[0]) > 0 and len(i[1]) > 0 and len(i[2]) > 0]
            #log_utils.log('r5: '+repr(r))
            # goojara tv show year are incorrect, sometimes.
            # this will match ALIAS and YEAR
            try:
                result_url = next(i[0] for i in r if cleantitle.match_alias(i[1], aliases) and cleantitle.match_year(i[2], year, data['year']))
                #log_utils.log('result_url1: '+repr(result_url))
            except StopIteration:
                try:
                    year2 = data.get('year')
                    result_url = next(i[0] for i in r if cleantitle.match_alias(i[1], aliases) and cleantitle.match_year(i[2], year2))
                    #log_utils.log('result_url2: '+repr(result_url))
                except StopIteration:
                    result_url = next(i[0] for i in r if cleantitle.match_alias(i[1], aliases))
                    #log_utils.log('result_url3: '+repr(result_url))
            if not result_url:
                return
            if not result_url.startswith(self.base_link):
                if not result_url.startswith('/'):
                    result_url = '/' + result_url
                result_url = self.base_link + result_url
            #log_utils.log('first result_url: '+repr(result_url))
            if 'tvshowtitle' in data:
                r = client.request(result_url, headers=self.headers, cookie=self.cookie)
                r = DOM(r, 'a', ret='href')
                #log_utils.log('tvshow r: '+repr(r))
                check_episode = 's%se%s' %(season, episode)
                #log_utils.log('tvshow check_episode: '+repr(check_episode))
                found_url = [i for i in r if check_episode in i][0]
                #log_utils.log('tvshow found_url: '+repr(found_url))
                if not found_url.startswith(self.base_link):
                    if not found_url.startswith('/'):
                        found_url = '/' + found_url
                    result_url = self.base_link + found_url
                else:
                    result_url = found_url
            #log_utils.log('final result_url: '+repr(result_url))
            resp1 = client.scrapePage(result_url, headers=self.headers, cookie=self.cookie)
            r = resp1.text
            result_links = DOM(r, 'a', attrs={'target': '_blank'}, ret='href')
            #log_utils.log('result_links: ' + repr(result_links))
            #log_utils.log('len(result_links): ' + repr(len(result_links)))
            gg = cookie_dict
            response_content = resp1.content.decode(encoding='utf-8', errors='strict')
            match = re.findall(r"_3chk\(['\"](.+?)['\"],['\"](.+?)['\"]\)", response_content, re.DOTALL)
            ck, ck2 = match[0] if match else (None, None)
            gg[ck] = ck2
            cookie_dict[ck] = ck2
            # replace the Cookies in the header
            new_cookies = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
            self.headers["Cookie"] = new_cookies
            for link in result_links:
                try:
                    if 'imdb' in link:
                        continue
                    link = client.request(link, headers=self.headers, output='geturl')
                    #log_utils.log('geturl link: ' + repr(link))
                    if link:
                        link = 'https:' + link if link.startswith('//') else link
                        # fix wootly links for resolveurl
                        # web.wootly.ch/e/some/text/123 -> www.wootly.ch/?v=123
                        link = re.sub(r"^(https?://)web\.wootly\.ch/e/.*/([^/]+)$",r"\1www.wootly.ch/?v=\2", link)
                    #log_utils.log('source link: ' + repr(link))
                    for source in scrape_sources.process(hostDict, link):
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

"""

[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://www.wootly.ch/?v=606FEEE4'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://www.wootly.ch/?v=606FEEE4'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://luluvdo.com/anfnouih4p9z'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://luluvdo.com/anfnouih4p9z'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://luluvdo.com/jqg4x9zosm73'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://luluvdo.com/jqg4x9zosm73'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://vide0.net/d/os85gnwmo1eg'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://vide0.net/d/os85gnwmo1eg'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://luluvdo.com/t999lb8uwj8e'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://luluvdo.com/t999lb8uwj8e'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://luluvdo.com/v81eo8pbc40d'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://luluvdo.com/v81eo8pbc40d'
[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://luluvdo.com/2xkgkjrgc9j0'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://luluvdo.com/2xkgkjrgc9j0'


[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://www.wootly.ch/?v=J997EEE4'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://www.wootly.ch/?v=J997EEE4'

[Scrubs v2 - 5.1.42 - DEBUG]: geturl link: 'https://www.wootly.ch/?v=N18AEEE4'
[Scrubs v2 - 5.1.42 - DEBUG]: source link: 'https://www.wootly.ch/?v=N18AEEE4'

"""
