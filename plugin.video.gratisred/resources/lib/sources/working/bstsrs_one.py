# -*- coding: utf-8 -*-

# Bstsrs scraper.
#
# State of bstsrs domains as of v1.0.7 (2026-04-29):
#   * bstsrs.in  - LIVE but behind a Cloudflare managed JS challenge
#                  (cf-mitigated: challenge).  Plain `requests` always
#                  gets the "Just a moment..." 403 page, so this scraper
#                  only produces links when the user has configured a
#                  FlareSolverr endpoint in `Settings > Playback Settings >
#                  FlareSolverr URL`.  client.scrapePage transparently
#                  retries CF 403/503 through FlareSolverr when set.
#   * bstsrs.one - parked / 302s to ad-redirector domain.  Skipped.
#   * bstsrs.cc  - 302s to ww1.bstsrs.cc parking page.  Skipped.
#
# Page format and `dbneg(...)` embed encoding are identical to the sister
# site srstop.link, so we mirror that scraper's slug + search-API + dual
# decoder approach.

import json
import re

from six.moves.urllib_parse import parse_qs, quote_plus, urlencode

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import decryption
from resources.lib.modules import scrape_sources
#from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.results = []
        self.domains = ['bstsrs.in']
        self.base_link = 'https://bstsrs.in'
        self.search_link = '/ajax/search.php?q=%s'
        self.episode_link = '/show/%s-s%02de%02d/season/%s/episode/%s'
        self.headers = {
            'User-Agent': client.UserAgent,
            'Referer': self.base_link,
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
        }


    def tvshow(self, imdb, tmdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        if tvshowtitle == 'House':
            tvshowtitle = 'House M.D.'
        url = {
            'imdb': imdb,
            'tvshowtitle': tvshowtitle,
            'localtvshowtitle': localtvshowtitle or '',
            'aliases': aliases,
            'year': year,
        }
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
            local = data.get('localtvshowtitle', '')
            year = data.get('year', '')
            season = data.get('season', '')
            episode = data.get('episode', '')
            if not (title and season and episode):
                return self.results

            urls = self._candidate_urls(title, local, year, season, episode)
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


    def _candidate_urls(self, title, local, year, season, episode):
        urls = []
        try:
            sint, eint = int(season), int(episode)
            slugs = []
            # Italian local title FIRST (bstsrs.in is the Italian site -
            # show URLs use Italian show names like dr-house-medical-division).
            if local:
                if year:
                    slugs.append(cleantitle.geturl('%s %s' % (local, year)))
                slugs.append(cleantitle.geturl(local))
            # Original (English) title fallbacks.
            if year:
                slugs.append(cleantitle.geturl('%s %s' % (title, year)))
            slugs.append(cleantitle.geturl(title))
            slugs.append(re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-'))
            for slug in slugs:
                if not slug:
                    continue
                urls.append(self.base_link + self.episode_link % (slug, sint, eint, sint, eint))
            # Search-API fallback - resolves the real Italian permalink
            # for both the local and original title.
            for q in (local, title):
                if not q:
                    continue
                try:
                    resp = client.scrapePage(
                        self.base_link + self.search_link % quote_plus(q),
                        headers=self.headers,
                        timeout='10',
                    ).text
                    items = self._parse_search_json(resp)
                    if isinstance(items, list):
                        for it in items[:3]:
                            permalink = (it or {}).get('permalink', '')
                            if not permalink:
                                continue
                            urls.append(permalink.rstrip('/') + '/season/%d/episode/%d' % (sint, eint))
                except Exception:
                    continue
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
        # Primary: GratisRed's hex-table decoder.
        try:
            decoded = decryption.decode(coded)
            if decoded.startswith('http'):
                return decoded
        except Exception:
            pass
        # Fallback: per-string offset variant (T4ils' bst.py).
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
