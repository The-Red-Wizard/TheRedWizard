# -*- coding: utf-8 -*-

import re
import simplejson as json

from six.moves.urllib_parse import parse_qs, urlencode, urlparse
from six import ensure_str, ensure_text

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import scrape_sources
from resources.lib.modules import log_utils

DOM = client_utils.parseDOM

class source:
    def __init__(self):
        self.results = []
        self.domains = ['m.stagatv.com']
        self.base_link = 'https://m.stagatv.com'
        self.search_link = '/?s={}'
        self.headers = client.dnt_headers
        self.ajax_link = '/wp-admin/admin-ajax.php'
        self.notes = 'Has TV Shows and movies, kinda works, ready to test'


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
            # log_utils.log('url =' + repr(url), 1)
            data = parse_qs(url)
            data = {k: v[0] if v else '' for k, v in data.items()}
            aliases = eval(data.get('aliases', '[]'))
            # title = data.get('tvshowtitle', data.get('title', ''))
            title = data.get('tvshowtitle', data.get('localtitle', data.get('title', '')))
            season, episode = data.get('season', '0'), data.get('episode', '0')
            year = data['year']
            check_term = f"{title} ({year})" if 'tvshowtitle' in data else title
            search_term = f"{title} (s{season.zfill(2)})" if 'tvshowtitle' in data else title
            search_title = cleantitle.get_plus(search_term)
            check_title = cleantitle.get(search_term)

            payload = {'action': 'ts_ac_do_search',
                       'ts_ac_query': search_term,
                       }

            customheaders = self.headers
            customheaders.pop('Pragma', None)
            customheaders.update({
                'Origin': self.base_link,
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': self.base_link,
                'Alt-Used': 'm.stagatv.com',
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Sec-GPC": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "TE": "trailers",
            })

            post_link = self.base_link + self.ajax_link
            # self.cookie = client.request(self.base_link, headers=self.headers, output='cookie', timeout='30')
            results1 = client.request(post_link, post=payload, headers=customheaders, output='json')
            results2 = results1.get("post", [{}])  # safely get the results if they exist
            if results2:
                results2 = results2[0].get("all")
            if len(results2) == 0:
                return

            pattern_year = r"\(\d{4}\)"  # year with parenthesis
            pattern_end = r'\s*(download|full movie|movie)\s*$'
            match = None

            for i in results2:
                post_title = i.get('post_title', '')
                post_title = re.sub(pattern_year, '', post_title)
                post_title = re.sub(pattern_end, '', post_title, flags=re.IGNORECASE)
                post_title = cleantitle.get(post_title)
                post_years = i.get('post_years', [])
                post_years = client_utils.remove_tags(post_years)

                if check_title == post_title and (year in post_years or "?" in post_years):
                    match = i
                    break

            if match:
                result_url = match.get("post_link")
            else:
                return


            results3 = client.request(result_url, headers=self.headers)

            if "tvshowtitle" in data:
                episode_containers = DOM(results3, "div", attrs={"class": "bixbox ts-ep-list"})
                episode_links = DOM(episode_containers, "a", ret="href")
                check_title = cleantitle.get_dash(title)
                search_term = f"{check_title}-season-{season}-episode-{episode}"
                episode_url = next((url for url in episode_links if search_term in url), None)
                if not episode_url:
                    return
                episode_page = client.request(episode_url, headers=self.headers)
                selector_links = DOM(episode_page, "a", attrs={"class": "linkselector"}, ret="href")
                if not selector_links:
                    return
                selector_url = selector_links[0]
                download_page = client.request(selector_url, headers=self.headers)
            else:  # Movie
                download_page = results3

            download_page = download_page.replace("\\", "")

            link_candidates = list(
                zip(
                    (client_utils.remove_codes(i) for i in DOM(download_page, "a")),
                    DOM(download_page, "a", ret="href")
                )
            )

            download_links = [
                (text, href) for text, href in link_candidates
                if "download" in text.lower() and not href.endswith("/")
            ]

            pattern = r"\('(.*?)'\)"
            link = None
            button_onclicks = DOM(download_page, "button", ret="onclick")

            if button_onclicks:
                match = re.search(pattern, button_onclicks[0])
                if match:
                    link = match.group(1)

            if not link and download_links:
                result_url = download_links[0][1]

                if result_url.endswith(('.mp4', '.mkv', '.avi', '.mov')) and "tvshowtitle" in data:
                    link = result_url

                else:
                    download_page = client.request(result_url, headers=self.headers)
                    download_page = download_page.replace("\\", "")
                    button_onclicks = DOM(download_page, "button", ret="onclick")

                    if button_onclicks:
                        match = re.search(pattern, button_onclicks[0])
                        if match:
                            link = match.group(1)

                    if not link:
                        fallback_candidates = list(
                            zip(
                                (client_utils.remove_codes(i) for i in DOM(download_page, "a")),
                                DOM(download_page, "a", ret="href")
                            )
                        )

                        fallback_links = [
                            (text, href) for text, href in fallback_candidates
                            if "download" in text.lower() and not href.endswith("/")
                        ]
                        if fallback_links:
                            link = fallback_links[0][1]

            self.headers.update({
                'Host': 'cdn.stagatvfiles.com',
                'Referer': result_url,
            })

            parts = urlparse(link)
            search = set(hostDict)  # include domain in hostDict

            if parts.hostname not in search:
                hostDict.append(parts.hostname)
                search.add(parts.hostname)

            if link:
                item = scrape_sources.make_direct_item(hostDict, link, host='Direct', info=None, referer=result_url, prep=False)
                if item:
                    self.results.append(item)

            return self.results
            
        except:
            return self.results



    def resolve(self, url):
        # try and catch some bad links
        check = client.request(url, headers=self.headers, output='headers', timeout='30')
        if not check:
            url = None
        # log_utils.log('url =' + repr(url), 1)
        return url


