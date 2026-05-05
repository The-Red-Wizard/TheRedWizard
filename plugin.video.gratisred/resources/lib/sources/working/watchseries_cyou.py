# -*- coding: utf-8 -*-

# Watchseries scraper.
#
# watchseries.cyou is a sister/dupe site of freeprojecttv.cyou (the
# `projectfreetv_cyou` provider) - identical page template, same
# /tv-series/<slug>-season-<n>-episode-<m>/ URL pattern, same
# `<tr class="ext_link_HOST">` row markup with `/open/link/<id>/`
# redirector hrefs.  The site sits behind Cloudflare's managed JS
# challenge, so links only appear when the user has configured a
# FlareSolverr endpoint in addon settings (see client._flaresolverr_url).
# `client.scrapePage` transparently retries CF 403/503 through
# FlareSolverr and caches the cf_clearance cookie per host so all
# subsequent requests on the same domain bypass the challenge with
# plain `requests` - critical for staying under providers.timeout.

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
        self.domains = ['watchseries.cyou']
        self.base_link = 'https://watchseries.cyou'
        self.movie_link = '/movies/%s-%s/'
        self.tvshow_link = '/tv-series/%s-season-%s-episode-%s/'
        self.notes = 'sister site of projectfreetv_cyou - same template, /open/link/ redirector.'
        self.headers = {
            'User-Agent': client.UserAgent,
            'Referer': self.base_link,
        }


    def movie(self, imdb, tmdb, title, localtitle, aliases, year):
        url = {'imdb': imdb, 'title': title, 'year': year}
        return urlencode(url)


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
        return urlencode(url)


    def episode(self, url, imdb, tmdb, tvdb, title, premiered, season, episode):
        if not url:
            return
        url = parse_qs(url)
        url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
        url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
        return urlencode(url)


    def sources(self, url, hostDict):
        try:
            if not url:
                return self.results
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            is_show = 'tvshowtitle' in data
            title = data['tvshowtitle'] if is_show else data.get('title', '')
            year = data.get('premiered', '') if is_show else data.get('year', '')
            season = data.get('season', '0')
            episode = data.get('episode', '0')
            slug = cleantitle.geturl(title)
            if is_show:
                result_url = self.base_link + self.tvshow_link % (slug, season, episode)
            else:
                result_url = self.base_link + self.movie_link % (slug, year)
            page = client.scrapePage(result_url, headers=self.headers, timeout='15')
            html = (getattr(page, 'text', '') or '') if page is not None else ''
            if not html:
                return self.results

            # Embedded iframe (rare on watchseries - usually internal /vembed/).
            try:
                for link in DOM(html, 'iframe', ret='src'):
                    try:
                        link = self.base_link + link if not link.startswith('http') else link
                        for src in scrape_sources.process(hostDict, link):
                            if scrape_sources.check_host_limit(src['source'], self.results):
                                continue
                            self.results.append(src)
                    except Exception:
                        continue
            except Exception:
                pass

            # ext_link rows: <tr class="ext_link_<host>">
            #   <a href="/open/link/<id>/" title="<host>">
            try:
                ext_rows = DOM(html, 'tr', attrs={'class': r'ext_link.+?'})
                for row in ext_rows:
                    try:
                        hrefs = DOM(row, 'a', ret='href')
                        titles = DOM(row, 'a', ret='title')
                        if not hrefs or not titles:
                            continue
                        link, host = hrefs[0], titles[0]
                        link = self.base_link + link if not link.startswith('http') else link
                        item = scrape_sources.make_item(hostDict, link, host=host, info=None, prep=True)
                        if item and not scrape_sources.check_host_limit(item['source'], self.results):
                            self.results.append(item)
                    except Exception:
                        continue
            except Exception:
                pass
            return self.results
        except Exception:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        if any(d in url for d in self.domains):
            try:
                page = client.scrapePage(url, headers=self.headers, timeout='15')
                html = (getattr(page, 'text', '') or '') if page is not None else ''
                # Prefer iframe src.
                try:
                    iframe = DOM(html, 'iframe', ret='src')
                    if iframe:
                        return iframe[0]
                except Exception:
                    pass
                # Fallback: /open/site/... redirect target embedded in page.
                try:
                    m = re.search(r'"(/open/site/[^"]+)"', html, re.I | re.S)
                    if m:
                        target = self.base_link + m.group(1)
                        page2 = client.scrapePage(target, headers=self.headers, timeout='15')
                        return getattr(page2, 'url', target) or target
                except Exception:
                    pass
            except Exception:
                #log_utils.log('resolve', 1)
                pass
        return url
