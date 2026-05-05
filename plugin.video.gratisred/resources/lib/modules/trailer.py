# -*- coding: utf-8 -*-

import re
import sys

import six
from six.moves.urllib_parse import quote_plus

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
#from resources.lib.modules import log_utils
from resources.lib.modules import tmdb_utils
from resources.lib.modules import trakt


try:
    #from infotagger.listitem import ListItemInfoTag
    from resources.lib.modules.listitem import ListItemInfoTag
except:
    pass

kodi_version = control.getKodiVersion()


class source:
    def __init__(self):
        self.content = control.infoLabel('Container.Content')
        self.trailer_mode = control.setting('trailer.select') or '1'
        self.trailer_source = control.setting('trailer.source') or '5'
        self.trailer_autofallback = control.setting('trailer.autofallback') or 'true'
        self.trailer_specials = control.setting('trailer.specials') or 'false'
        self.trailers_tmdb = control.setting('trailers.tmdb') or 'true'
        self.trailers_youtube = control.setting('trailers.youtube') or 'true'
        self.trailers_imdb = control.setting('trailers.imdb') or 'true'
        self.trailers_trakt = control.setting('trailers.trakt') or 'true'
        self.youtube_lang = control.apiLanguage().get('youtube', 'en') or 'en'
        self.tmdb_lang = control.apiLanguage().get('tmdb', 'en') or 'en'
        # YouTube is now an optional fallback only. No bundled API keys are shipped with the add-on.
        # The user can either:
        #   1. Pair with plugin.video.youtube (its configured key will be used), or
        #   2. Supply their own key in this add-on's settings (youtube.api).
        if control.condVisibility('System.HasAddon(plugin.video.youtube)'):
            self.youtube_key = control.addon('plugin.video.youtube').getSetting('youtube.api.key') or ''
        else:
            self.youtube_key = ''
        if not self.youtube_key:
            self.youtube_key = control.setting('youtube.api') or ''
        self.imdb_link = 'https://www.imdb.com/_json/video/'
        self.youtube_link = 'https://youtube.com'
        self.youtube_watch_link = self.youtube_link + '/watch?v='
        #self.youtube_plugin_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
        self.youtube_plugin_url = 'plugin://plugin.video.youtube/play/?video_id='
        self.youtube_lang_link = '' if self.youtube_lang == 'en' else '&relevanceLanguage=%s' % self.youtube_lang
        if self.trailer_mode == '0':
            self.youtube_search_link = 'https://www.googleapis.com/youtube/search?part=id&type=video&maxResults=10&q=%s&key=%s%s' % ('%s', '%s', self.youtube_lang_link)
        else:
            self.youtube_search_link = 'https://www.googleapis.com/youtube/search?part=snippet&type=video&maxResults=10&q=%s&key=%s%s' % ('%s', '%s', self.youtube_lang_link)


    def youtube_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        trailer_list = []
        try:
            # Fallback source: requires a user-supplied YouTube API key
            # (either from this add-on's settings or paired plugin.video.youtube).
            if not self.youtube_key:
                return trailer_list
            if self.content not in ['tvshows', 'seasons', 'episodes']:
                name += ' %s' % control.infoLabel('ListItem.Year')
            elif self.content in ['seasons', 'episodes']:
                if season and episode:
                    name += ' %sx%02d' % (season, int(episode))
                elif season:
                    name += ' season %01d' % int(season)
            if self.content != 'episodes':
                name += ' trailer'
            query = quote_plus(name)
            url = self.youtube_search_link % (query, self.youtube_key)
            result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                return trailer_list
            results = result['items']
            if not results:
                return trailer_list
            for i in results:
                trailer_list.append({'source': 'YouTube', 'title': i.get('snippet', {}).get('title', ''), 'url': i.get('id', {}).get('videoId', ''), 'type': 'Trailer'})
            return trailer_list
        except:
            #log_utils.log('youtube_trailers', 1)
            return trailer_list


    def trakt_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        trailer_list = []
        try:
            if not imdb or imdb == '0':
                return trailer_list
            if self.content not in ['tvshows', 'seasons', 'episodes']:
                results = trakt.getMovieSummary(imdb, full=True)
                if not results:
                    year = control.infoLabel('ListItem.Year')
                    try:
                        results = trakt.SearchMovie(name, year, full=True)
                        if results[0]['movie']['title'].lower() != name.lower() or int(results[0]['movie']['year']) != int(year):
                            raise Exception()
                        results = results[0].get('movie', {})
                    except:
                        results = {}
            else:
                results = trakt.getTVShowSummary(imdb, full=True)
                if not results:
                    year = control.infoLabel('ListItem.Year')
                    try:
                        results = trakt.SearchTVShow(name, year, full=True)
                        if results[0]['show']['title'].lower() != name.lower() or int(results[0]['show']['year']) != int(year):
                            raise Exception()
                        results = results[0].get('show', {})
                    except:
                        results = {}
            if not results:
                return trailer_list
            else:
                trailer_list.append({'source': 'Trakt', 'title': name, 'url': results.get('trailer', ''), 'type': 'Trailer'})
            return trailer_list
        except:
            #log_utils.log('trakt_trailers', 1)
            return trailer_list


    def imdb_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        trailer_list = []
        try:
            if not imdb or imdb == '0':
                return trailer_list
            link = self.imdb_link + imdb
            items = client.scrapePage(link, timeout='30').json()
            listItems = items['playlists'][imdb]['listItems']
            videoMetadata = items['videoMetadata']
            for item in listItems:
                try:
                    videoId = item['videoId']
                    metadata = videoMetadata[videoId]
                    title = metadata['title']
                    related_to = metadata.get('primaryConst') or imdb
                    if not related_to == imdb:
                        continue
                    videoUrl = [i['videoUrl'] for i in metadata['encodings'] if i['definition'] in ['1080p', '720p', '480p', '360p', 'SD']]
                    if not videoUrl:
                        continue
                    videoType = 'Trailer' if 'trailer' in title.lower() else 'N/A'
                    trailer_list.append({'source': 'IMDb', 'title': title, 'url': videoUrl[0], 'type': videoType})
                except:
                    pass
            return trailer_list
        except:
            #log_utils.log('imdb_trailers', 1)
            return trailer_list


    def tmdb_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        trailer_list = []
        try:
            if not tmdb or tmdb == '0':
                return trailer_list
            if self.content == 'tvshows':
                items = tmdb_utils.get_tvshow_trailers(tmdb)
            elif self.content == 'seasons':
                items = tmdb_utils.get_season_trailers(tmdb, season)
            elif self.content == 'episodes':
                items = tmdb_utils.get_episode_trailers(tmdb, season, episode)
            else:
                items = tmdb_utils.get_movie_trailers(tmdb)
            if not items:
                if episode != '':
                    items = tmdb_utils.get_season_trailers(tmdb, season)
            if not items:
                if season != '':
                    items = tmdb_utils.get_tvshow_trailers(tmdb)
            if not items:
                return trailer_list
            items = [r for r in items if r.get('site') == 'YouTube']
            results = [x for x in items if x.get('iso_639_1') == self.tmdb_lang]
            if not self.tmdb_lang == 'en':
                results += [x for x in items if x.get('iso_639_1') == 'en']
            results += [x for x in items if x.get('iso_639_1') not in set([self.tmdb_lang, 'en'])]
            if not results:
                return trailer_list
            for i in results:
                trailer_list.append({'source': 'TMDb', 'title': i.get('name', ''), 'url': i.get('key', ''), 'type': i.get('type', 'N/A')})
            return trailer_list
        except:
            #log_utils.log('tmdb_trailers', 1)
            return trailer_list


    def get(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            trailers_list = []
            # Mapping of single-source selections to their fetcher method.
            single_source_map = {
                '0': self.tmdb_trailers,
                '1': self.youtube_trailers,
                '2': self.imdb_trailers,
                '3': self.trakt_trailers,
            }
            # Smart cascade order: TMDb -> IMDb -> Trakt -> YouTube.
            # YouTube is intentionally last since it requires a user-supplied API key.
            smart_cascade = [
                self.tmdb_trailers,
                self.imdb_trailers,
                self.trakt_trailers,
                self.youtube_trailers,
            ]

            if self.trailer_source == '5':
                # Smart (Auto-Cascade): try each source until one returns results.
                for fetcher in smart_cascade:
                    trailers_list = fetcher(name, url, tmdb, imdb, season, episode) or []
                    if trailers_list:
                        break
            elif self.trailer_source in single_source_map:
                fetcher = single_source_map[self.trailer_source]
                trailers_list = fetcher(name, url, tmdb, imdb, season, episode) or []
                # Auto-fallback: if the chosen source yields nothing, walk the Smart cascade
                # skipping the already-tried source.
                if not trailers_list and self.trailer_autofallback == 'true':
                    for fetcher in smart_cascade:
                        if fetcher is single_source_map[self.trailer_source]:
                            continue
                        trailers_list = fetcher(name, url, tmdb, imdb, season, episode) or []
                        if trailers_list:
                            break
            else:
                # Multi: aggregate results from every enabled source.
                if self.trailers_tmdb == 'true':
                    trailers_list += self.tmdb_trailers(name, url, tmdb, imdb, season, episode) or []
                if self.trailers_youtube == 'true':
                    trailers_list += self.youtube_trailers(name, url, tmdb, imdb, season, episode) or []
                if self.trailers_imdb == 'true':
                    trailers_list += self.imdb_trailers(name, url, tmdb, imdb, season, episode) or []
                if self.trailers_trakt == 'true':
                    trailers_list += self.trakt_trailers(name, url, tmdb, imdb, season, episode) or []
            control.idle()
            item = self.select_items(trailers_list)
            control.idle()
            return self.item_play(item, windowedtrailer)
        except:
            #log_utils.log('get', 1)
            return


    def select_items(self, results):
        try:
            if not results:
                return
            if self.trailer_specials == 'true':
                results = [i for i in results if i.get('type') == 'Trailer'] + [i for i in results if i.get('type') != 'Trailer']
            else:
                results = [i for i in results if i.get('type') == 'Trailer']
            if self.trailer_mode == '1':
                items = ['%s | %s (%s)' % (i.get('source', ''), i.get('title', ''), i.get('type', 'N/A')) for i in results]
                select = control.selectDialog(items, 'Trailers')
                if select == -1:
                    return 'canceled'
                return results[select]
            items = [i.get('url') for i in results]
            for vid_id in items:
                url = self.worker(vid_id)
                if url:
                    return url
            return
        except:
            #log_utils.log('select_items', 1)
            return


    def item_play(self, result, windowedtrailer):
        try:
            control.idle()
            if not result:
                return control.infoDialog('No trailer available')
            elif result == 'canceled':
                return
            title = result.get('title', '')
            if not title:
                title = control.infoLabel('ListItem.Title')
            url = result.get('url', '')
            if not url:
                return control.infoDialog('No trailer available')
            if not url.startswith(self.youtube_plugin_url):
                url = self.worker(url)
            item = control.item(label=title, path=url)
            item.setProperty('IsPlayable', 'true')
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': title})
            else:
                item.setInfo(type='video', infoLabels={'title': title})
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            #log_utils.log('item_play', 1)
            return


    def worker(self, url):
        try:
            if not url:
                raise Exception()
            url = url.replace('http://', 'https://')
            url = url.replace('www.youtube.com', 'youtube.com')
            if url.startswith(self.youtube_link):
                url = self.resolve(url)
                if not url:
                    raise Exception()
            elif not url.startswith('http'):
                url = self.youtube_watch_link + url
                url = self.resolve(url)
                if not url:
                    raise Exception()
            return url
        except:
            #log_utils.log('worker', 1)
            return


    def resolve(self, url):
        try:
            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            url = self.youtube_watch_link + id
            result = client.scrapePage(url, timeout='30').text
            message = client_utils.parseDOM(result, 'div', attrs={'id': 'unavailable-submessage'})
            message = ''.join(message)
            alert = client_utils.parseDOM(result, 'div', attrs={'id': 'watch7-notification-area'})
            if len(alert) > 0:
                raise Exception()
            if re.search(r'[a-zA-Z]', message):
                raise Exception()
            url = self.youtube_plugin_url + id
            return url
        except:
            #log_utils.log('resolve', 1)
            return


