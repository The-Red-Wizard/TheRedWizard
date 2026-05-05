# -*- coding: utf-8 -*-

import re
import simplejson as json

from six.moves.urllib_parse import urlparse, parse_qs, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
from resources.lib.modules import log_utils

DOM = client_utils.parseDOM

class source:
    def __init__(self):
        self.results = [] ## Mirror Holder  https://hollymoviehd-official.com/
        self.domains = ['hollymoviehd.cc', 'hollymoviehd-official.com' ] # Alt domains:  nmovies.cc  yeshd.net
        self.base_link = 'https://hollymoviehd.cc'
        self.search_link = '/?s=%s'
        self.ajax_link = '/wp-admin/admin-ajax.php'
        self.headers = client.dnt_headers
        self.notes = 'Dupe of novamovie_net. Search has blockage.'


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
            search = '%s Season %s' % (title, season) if 'tvshowtitle' in data else title
            search_url = self.base_link + self.search_link % cleantitle.get_plus(search)
            self.headers.update({'Origin': self.base_link})
            post_link = self.base_link + self.ajax_link
            try:
                r = client.scrapePage(search_url).text
                r = DOM(r, 'div', attrs={'class': 'ml-item'})
                if not r and 'tvshowtitle' in data:
                    search_url = self.base_link + self.search_link % cleantitle.get_plus(title)
                    r = client.scrapePage(search_url).text
                    r = DOM(r, 'div', attrs={'class': 'ml-item'})
                r = [(DOM(i, 'a', ret='href'), DOM(i, 'a', ret='title')) for i in r]
                r = [(i[0][0], i[1][0]) for i in r if len(i[0]) > 0 and len(i[1]) > 0]
                if 'tvshowtitle' in data:
                    r = [(i[0], re.findall(r'(.+?) Season (\d+)', i[1])) for i in r]
                    r = [(i[0], i[1][0]) for i in r if len(i[1]) > 0]
                    url = [i[0] for i in r if cleantitle.match_alias(i[1][0], aliases) and i[1][1] == season][0]
                    url = url.replace('/series/', '/episode/')
                    url = url[:-1] if url.endswith('/') else url
                    url = url + '-episode-%s/' % episode
                else:
                    try:
                        r = [(i[0], re.findall(r'(.+?) \((\d{4})', i[1])) for i in r]
                        r = [(i[0], i[1][0]) for i in r if len(i[1]) > 0]
                        url = [i[0] for i in r if cleantitle.match_alias(i[1][0], aliases) and cleantitle.match_year(i[1][1], year)][0]
                    except:
                        url = [i[0] for i in r if cleantitle.match_alias(i[1], aliases)][0]
            except:
                if 'tvshowtitle' in data:
                    url = self.base_link + '/episode/%s-season-%s-episode-%s/' % (cleantitle.get_dash(title), season, episode)
                else:
                    url = self.base_link + '/%s-%s/' % (cleantitle.get_dash(title), year)
            r = client.scrapePage(url, headers=self.headers).text
            r10 = DOM(r, 'div', attrs={'id': 'mv-info'})
            req_data1 = DOM(r10, 'div', attrs={'id': r'player\d'}, ret='data-streamkey')[0]
            req_data2 = DOM(r10, 'div', attrs={'id': r'player\d'}, ret='data-wpnonce')[0]
            if not req_data1 or not req_data2:
                return
            self.headers.update({'Referer': url})
            payload = { 'action': 'ajax_getlinkstream',
                        'streamkey': req_data1,
                        'nonce': req_data2,
                        'imdbid': data['imdb']
                        }
            resp = client.request(post_link, post=payload, headers=self.headers, verify=None, XHR=True, output='extended')
            if not resp:
                return
            body, self.headers, *_ = resp
            body = client_utils.replaceHTMLCodes(body)
            links = []
            if 'streamsvr' in body:  # hack to create streamsvr link; need help from resolveURL for cleanup
                resp_data = json.loads(body)
                iframe_servers = resp_data.get('servers_iframe', {})
                iframe_url = next(iter(iframe_servers.values()), None)
                parts = urlparse(iframe_url)
                if not parts.query:
                    return
                # build the link
                s = payload['streamkey']
                base_url = f"https://{parts.hostname}/pl"
                match = re.search(r'([^|]+)\|([^|@]+)@1080p', s)
                if match:
                    key_720p, key_1080p = match.groups()   # Unpack the stream keys from the match
                    links.append(f"{base_url}/{key_720p}/720?{parts.query}")
                    links.append(f"{base_url}/{key_1080p}/1080?{parts.query}")
                else:
                    links.append(f"{base_url}/{s}/720?{parts.query}")
                # log_utils.log('links =' + repr(links), 1)

            search = set(hostDict) # include domain in hostDict, so we can use make_item
            if parts.hostname not in search:
                hostDict.append(parts.hostname)
                search.add(parts.hostname)
            for link in links:
                for source in scrape_sources.process(hostDict, link):
                    self.results.append(source)
            
            return self.results
        except:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        return url


