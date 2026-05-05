# -*- coding: utf-8 -*-

# Srstop scraper - ported from plugin.video.tvfree (TV Free) into the
# Scrubs/GratisRed `class source` provider format.  Srstop.link is a TV
# show indexer (no movies); the embed urls on each episode page are
# encoded with the same dbneg(...) family used by bstsrs (Italian sister
# site).  We try the existing modules.decryption.decode first, and fall
# back to the per-string offset algorithm shipped with TV Free's bst.py
# in case Srstop ever rolls back to the older variant.

import json
import re

from six.moves.urllib_parse import parse_qs, quote_plus, urlencode, urljoin

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import decryption
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['srstop.link', 'srstop.com']
        self.base_link = 'https://srstop.link'
        self.search_link = '/ajax/search.php?q=%s'
        # Direct slug-style episode URL used by the bstsrs family of
        # sites - covers most cases without needing the search API.
        self.episode_link = '/show/%s-s%02de%02d/season/%s/episode/%s'
        self.headers = {
            'User-Agent': client.UserAgent,
            'Referer': self.base_link,
        }


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        url = {'imdb': imdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
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
            title = data.get('tvshowtitle', '')
            season = data.get('season', '')
            episode = data.get('episode', '')
            if not (title and season and episode):
                return self.results

            urls = self._candidate_urls(title, season, episode)
            html = ''
            for ep_url in urls:
                try:
                    html = client.scrapePage(ep_url, headers=self.headers, timeout='10').text or ''
                except Exception:
                    html = ''
                if html and ('embed-selector' in html or 'dbneg(' in html):
                    break
                # Short-circuit if we got the CF challenge - no point trying
                # more URLs on the same domain, FlareSolverr is the gate.
                if html and 'Just a moment' in html[:1000]:
                    return self.results
            if not html:
                return self.results

            blocks = re.findall(
                r"(?:class=['\"]embed-selector['\"][^>]*>.*?)?dbneg\(['\"]([^'\"]+)['\"]\).*?domain=([^'\"&<> ]+)",
                html,
                re.DOTALL,
            )
            if not blocks:
                blocks = [(c, '') for c in re.findall(r"dbneg\(['\"]([^'\"]+)['\"]\)", html)]

            for coded, host in blocks:
                try:
                    link = self._dbneg(coded)
                    if not link or not link.startswith('http'):
                        continue
                    items = scrape_sources.process(hostDict, link, host=host or None)
                    if items:
                        for item in items:
                            if scrape_sources.check_host_limit(item['source'], self.results):
                                continue
                            self.results.append(item)
                    else:
                        item = scrape_sources.make_item(hostDict, link, host=host or None, prep=True)
                        if item and not scrape_sources.check_host_limit(item['source'], self.results):
                            self.results.append(item)
                except Exception:
                    #log_utils.log('sources', 1)
                    continue
            return self.results
        except Exception:
            #log_utils.log('sources', 1)
            return self.results


    def _candidate_urls(self, title, season, episode):
        urls = []
        try:
            sint, eint = int(season), int(episode)
            slug1 = cleantitle.geturl(title)
            urls.append(self.base_link + self.episode_link % (slug1, sint, eint, sint, eint))
            slug2 = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            if slug2 and slug2 != slug1:
                urls.append(self.base_link + self.episode_link % (slug2, sint, eint, sint, eint))
            # Search API fallback - resolves the real show permalink even
            # when the slug heuristic fails (e.g. "Mr. Robot" -> "mr-robot").
            try:
                resp = client.scrapePage(
                    self.base_link + self.search_link % quote_plus(title),
                    headers=self.headers,
                    timeout='10',
                ).text
                items = self._parse_search_json(resp)
                if isinstance(items, list):
                    for it in items[:3]:
                        permalink = (it or {}).get('permalink', '')
                        if not permalink:
                            continue
                        # show -> /season/N/episode/M
                        urls.append(permalink.rstrip('/') + '/season/%d/episode/%d' % (sint, eint))
            except Exception:
                pass
        except Exception:
            pass
        # de-dupe while preserving order
        seen = set()
        out = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out


    def _parse_search_json(self, resp):
        """Decode the /ajax/search.php payload.  When FlareSolverr is in
        play the JSON arrives wrapped in `<html><body><pre>JSON</pre></body>`;
        strip the wrapper before parsing."""
        if not resp:
            return []
        try:
            return json.loads(resp)
        except Exception:
            pass
        try:
            m = re.search(r'<pre[^>]*>(.+?)</pre>', resp, re.DOTALL)
            if m:
                return json.loads(m.group(1))
        except Exception:
            pass
        try:
            m = re.search(r'(\[.*\]|\{.*\})', resp, re.DOTALL)
            if m:
                return json.loads(m.group(1))
        except Exception:
            pass
        return []



    def _dbneg(self, coded):
        # Try GratisRed's existing hex-table decoder first (bstsrs style).
        try:
            decoded = decryption.decode(coded)
            if decoded.startswith('http'):
                return decoded
        except Exception:
            pass
        # Fallback: TV Free's per-string offset algorithm (credit T4ils).
        try:
            ret = ''
            offset = None
            for sp in coded.split('-'):
                if not sp:
                    continue
                code = int(sp, 16)
                if offset is None:
                    offset = code - ord('h')
                ret += chr(code - offset)
            if ret.startswith('http'):
                return ret
        except Exception:
            pass
        return ''


    def resolve(self, url):
        return url
