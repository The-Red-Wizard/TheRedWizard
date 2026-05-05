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
        self.domains = ['naijavault.com']
        self.base_link = 'https://www.naijavault.com'
        self.search_link = '/?s=%s'
        self.headers = client.dnt_headers
        self.notes = 'testing this'
        

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
            season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            check_term = '%s Season %s' % (title, season) if 'tvshowtitle' in data else title
            check_title = cleantitle.get(check_term)
            search_url = self.base_link + self.search_link % cleantitle.get_utf8(title)
            r = client.scrapePage(search_url, headers=self.headers).text
            r = DOM(r, 'div', attrs={'class': 'mh-loop-content mh-clearfix'})
            if not r:   # new search using localtitle
                title = data['localtitle']
                check_term = '%s Season %s' % (title, season) if 'tvshowtitle' in data else title
                check_title = cleantitle.get(check_term)
                search_url = self.base_link + self.search_link % cleantitle.get_utf8(title)
                r = client.scrapePage(search_url, headers=self.headers).text
                r = DOM(r, 'div', attrs={'class': 'mh-loop-content mh-clearfix'})

            r = [(DOM(i, 'a', ret='href', attrs={'rel': 'bookmark'}),
            DOM(i, 'a', ret='title'),
            DOM(i, 'div', attrs={'class': 'mh-excerpt'})) for i in r]
            # FLATTEN the list
            r = [(i[0][0], i[1][0], i[2][0]) for i in r if len(i[0]) > 0 and len(i[1]) > 0 and len(i[2]) > 0]
            r = [(i[0], client_utils.replaceHTMLCodes(i[1]), client_utils.replaceHTMLCodes(i[2])) for i in r]

            keywords = [           # so we can add more later
                r"\d{4}",          # year
                "complete(?:d)?",
                "added",
                "remix",
                "full hd",
                "download",
                "hollywood",
                "zip file",
                "music",
                "more details here"
            ]

            pattern = (
                r"[\(\[]?"                            # optional ( or [
                r"(?:\b(" + "|".join(keywords) + r")\b)"  # the keywords
                r"[\)\]]?"                            # optional ) or ]
            )

            r = [( i[0], re.sub(pattern, '', i[1], flags=re.IGNORECASE).strip(), i[2]) for i in r]
           
            if 'tvshowtitle' in data:
                result_url = [i[0] for i in r if check_title in cleantitle.get(i[1])]
                result_url = result_url[0] if result_url else None
                if result_url is None:
                    # try again; Site sucks for TV titles. Names/seasons are wrong, and/or missing info
                    check_title2 = cleantitle.get(title)
                    result_url = [i[0] for i in r if check_title2 in cleantitle.get(i[1])]
                    result_url = result_url[0] if result_url else None
            else:
                result_urls = [i[0] for i in r if check_title in cleantitle.get(i[1]) 
                              and 'movie' in i[1].lower()
                              and cleantitle.match_year(i[0], year)]
                result_url = result_urls[0] if result_urls else None
                if not result_url:
                    result_urls = [i[0] for i in r if check_title in cleantitle.get(i[1])
                                  and cleantitle.match_year(i[0], year)]
                    result_url = result_urls[0] if result_urls else None
            if result_url is None:
                return
            
            result_link = self.base_link + result_url if result_url.startswith('/') else result_url
            r = client.scrapePage(result_link, headers=self.headers).text
            if 'tvshowtitle' in data:
                check_episode = f'S{int(season):02}E{int(episode):02}'
                r = DOM(r, 'a', ret='href', attrs={'id': 'download-button'})
                episode_urls = [i for i in r if check_episode in i]
                episode_link = episode_urls[0] if episode_urls else None
                if episode_link is None:
                    return
                link = self.base_link + episode_link if episode_link.startswith('/') else episode_link
            else:
                # site has many different types of download links, 'download-button'
                # 'download movie', download
                links = list(zip(DOM(r,'a', ret='href'), DOM(r, 'a')))
                links2 = [(i[0], i[1]) for i in links if 'download' in i[1].lower()]
                links3 = [(i[0], i[1]) for i in links2 if 'wp-content/uploads' not in i[1].lower()]
                if not links3:
                    return
                link = links3[0][0] if links3 else None

            if link is None:
                return
            parts = urlparse(link)
            search = set(hostDict)  # include domain in hostDict, so we can use make_item
            
            if parts.hostname not in search:
                hostDict.append(parts.hostname)
                search.add(parts.hostname)
            if link:
                for source in scrape_sources.process(hostDict, link):
                    self.results.append(source)

            return self.results
        except:
            return self.results


    def resolve(self, url):
        if 'downloadwella' in url:
            html = client.request(url, verify=False)
            form = DOM(html, 'form', attrs={'method': 'POST'})[0]
            postdata = dict(zip(DOM(form, 'input', ret='name'), DOM(form, 'input', ret='value')))
            url = client.request(url, headers=self.headers, post=postdata, output='geturl')
        elif 'filevault' in url:
            url = client.request(url, headers=self.headers, output='geturl')
            if url.endswith('?preview'):
                url = url[:-len('?preview')]
        elif 'loadedfiles' in url:
            self.headers.pop("Cookie", None)  # remove the item Cookie, if exists
            self.cookie = client.request(url, headers=self.headers, output='cookie', timeout='10')
            self.headers.update({'Host': 'loadedfiles.org'})
            html = client.request(url, headers=self.headers, cookie=self.cookie)
            match = re.search(r'var\s+downloadUrl\s*=\s*["\']([^"\']+)["\']', html)
            if not match:
                return
            download_link = match.group(1)
            self.headers.update({'Referer': url,
                                 'Priority': 'u=0, i',
                                 'Te': 'trailers',
                                 })
            html2 = client.request(download_link, headers=self.headers)
            match2 = re.search(r'var\s+downloadUrl\s*=\s*["\']([^"\']+)["\']', html2)
            if not match2:
                return
            download_link2 = match2.group(1)
            url = client.request(download_link2, headers=None, cookie=self.cookie, output='geturl', timeout='30')
        elif any(i in url for i in self.domains):
            r = client.scrapePage(url, headers=self.headers).text
            url = DOM(r, 'a', ret='href', attrs={'class': 'sdm_download green'})
            url = url[0] if url else None
        # log_utils.log('url =' + repr(url), 1)

        return url


