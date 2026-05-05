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
        self.domains = ['seriezloaded.com.ng']
        self.base_link = 'https://www.seriezloaded.com.ng'
        self.search_link = '?action=live_search_posts&term=%s'
        self.ajax_link = '/wp-admin/admin-ajax.php'
        self.headers = client.dnt_headers
        self.notes = 'tough site, lots of custom links and weird grouping.'
        

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

    def getlinks(self, data, aliases, title, season, episode, year, page_link=None):
        if any(domain in page_link for domain in self.domains):
            html = client.request(page_link, headers=self.headers)
            ext_links = DOM(html, 'div', attrs={'class': 'sl-container'})
            if not ext_links:
                return

            onclick_values = DOM(ext_links, 'button', ret='onclick')
            title_elements = DOM(ext_links, 'h2')

            if not onclick_values or not title_elements:
                return

            url = onclick_values[0]
            title = title_elements[0]

            match = re.search(r"https?://[^\s'\"]+", url)  # don't include ending single quote
            link = None
            if match:
                link = match.group()
        else:
            link = page_link

            
        return link

    def sources(self, url, hostDict):
        try:
            if not url:
                return self.results
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            aliases = eval(data['aliases'])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            title_imdb = data['imdb']
            season, episode = (data['season'], data['episode']) if 'tvshowtitle' in data else ('0', '0')
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            search_url = self.base_link + self.ajax_link + self.search_link % cleantitle.get_utf8(title_imdb)   # MOVIES
            if 'tvshowtitle' in data:
                title_clean = f'%22{title_imdb}%22 %22season {season}%22 %22episode {episode}%22'
                title_clean = cleantitle.get_utf8(title_clean)
                search_url = self.base_link + self.ajax_link + self.search_link % title_clean

            r = client.request(search_url, headers=self.headers, output='json')

            if not r:
                title_clean = f'%22{title_imdb}%22 %22season {season}%22'
                title_clean = cleantitle.get_utf8(title_clean)
                search_url = self.base_link + self.ajax_link + self.search_link % title_clean
                r = client.request(search_url, headers=self.headers, output='json')
            if not r:
                return

            r_list = []
            for item in r:  # push the (YYYY) into a new field
                title = item['title']
                link = item['link']

                match = re.search(r'\((\d{4})\)', title)  # (YYYY)
                year = match.group(1) if match else ''

                match2 = re.search(r'\bepisode\s+\d+\s*[-–]\s*\d+\b', title, re.I)  # episode 1 [emdash] 8
                brange = True if match2 else False

                clean_title = re.sub(r'\s*\(\d{4}\)', '', title)

                r_list.append({
                    "title": clean_title,
                    "year": year,
                    "link": link,
                    "brange": brange,
                })

            result_urls = [(i['link'], i['brange']) for i in r_list]

            if not result_urls:
                return

            result_url = result_urls[0][0] if result_urls else None
            brange = result_urls[0][1] if result_url else None

            r = client.request(result_url, headers=self.headers)

            if 'imdb:' in r.lower() and data['imdb'] not in r:  # IMDB is listed so let's confirm
                return

            final_links = []
            if 'tvshowtitle' in data:  # TV series only have 1 link per episode
                article = client_utils.parseDOM(r, 'article', attrs={'id': r'post.+?'})
                search_items = [
                    ('a', {'id': 'download-button'}),
                    ('a', {'id': 'sl-download-button'}),
                    ('a', {'class': 'btn-ghost'})
                ]

                for tag, attrs in search_items:
                    hrefs = DOM(article, tag, ret='href', attrs=attrs)
                    if hrefs:
                        elements = DOM(article, tag, attrs=attrs)
                        links = list(zip(hrefs, elements))
                        break
                else:  # often misunderstood; when break NOT hit then do this.
                    paragraphs = DOM(article, 'p')
                    r = [i for i in paragraphs if 'episode' in i.lower()]  # pull out the episode links
                    r = [i.partition("||")[0].strip() for i in r]          # remove the text after ||
                    links = list(zip(DOM(r, 'a', ret='href'),
                                     DOM(r, 'em')))

                episode_links = [(href, text) for href, text in links if href and text]  # FLATTEN

                if brange:  # Range of episodes found. ie episodes 1 - 10
                    check_episode = rf'\bepisode\s+{episode}\b'
                    episode_link = [t for t in episode_links if re.search(check_episode, t[1], re.IGNORECASE)]
                    episode_link = episode_link[0][0] if episode_link else None

                    if not episode_link:
                        return

                    link = self.getlinks(data, aliases, title, season, episode, year, page_link=episode_link)

                    if not link:
                        link = episode_link

                    final_links += [(link, title)]

                else:
                    for episode_link, info in episode_links:
                        my_link = None
                        my_link = self.getlinks(data, aliases, title, season, episode, year, page_link=episode_link)
                        if my_link:
                            final_links += [(my_link, info)]

            else:  # movies have multiple links
                links2 = list(zip(DOM(r,'a', ret='href', attrs={'class': 'btn-ghost'}),
                                 DOM(r, 'a', attrs={'class': 'btn-ghost'})))
                links = [(i[0], i[1]) for i in links2 if 'download' in i[1].lower()]
                if not links:
                    return

                for link, info in links:
                    my_link = self.getlinks(data, aliases, title, season, episode, year, page_link=link)
                    if my_link:
                        final_links += [(my_link, info)]

            for link, info in final_links:
                if 'download subtitle' == info.lower():
                    continue
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
        try:
            if 'send' in url:
                url = url.replace('send.cm', 'send.now')  # pull request https://github.com/Gujal00/ResolveURL/pull/1133
                url = url.replace('sendit.cloud', 'send.now')
            elif 'waffi.cloud' in url:
                if url.endswith('?preview'):
                    url = url[:-len('?preview')]
            elif 'loadedfiles' in url:   #  TODO: move to scrape_sources_py
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
            elif 'pixeldrain' in url:
                return url
            else:
                html = client.request(url, headers=self.headers, timeout=10)
                if not html:
                    return
                if any(msg in html.lower() for msg in ('file not found',
                                                       'no such file=',
                                                       'video you are looking for is not found',
                                                       'video unavailable',
                                                       'need to enable javascript',
                                                       )):
                    return

                link = DOM(html, 'iframe', ret='src')
                if not link:
                    return
                url = link[0] if link else None
                if link == '/e/' or 'javascript' in link:
                    link = None


        except:
            pass

        return url


