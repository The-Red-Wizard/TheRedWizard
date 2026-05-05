# -*- coding: utf-8 -*-

# DaddyLive plugin - ported from plugin.video.tvfree (TV Free) into the
# Scrubs/GratisRed indexer-plugin format used by tvpassport.py etc.
# Provides a full live-TV / sports schedule from daddylive.mp and
# resolves the m3u8 stream the same way TV Free's ddlv.py does it.

import json
import re
from datetime import date, datetime

from six.moves.urllib_parse import quote_plus, urljoin, urlparse

from resources.lib.indexers import navigator
from resources.lib.modules import client
from resources.lib.modules import control


BASE_URL = 'https://daddylive.mp'
USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': BASE_URL + '/',
    'Origin': BASE_URL + '/',
}


def _request(url, timeout=15):
    try:
        return client.scrapePage(url, headers=HEADERS, timeout=str(timeout)).text or ''
    except Exception:
        try:
            return client.request(url, headers=HEADERS, timeout=str(timeout)) or ''
        except Exception:
            return ''


class listings:
    def __init__(self):
        self.list = []
        self.schedule_url = urljoin(BASE_URL, '/schedule/schedule-generated.php')
        self.channels_url = urljoin(BASE_URL, '/24-7-channels.php')


    def root(self):
        # Top-level menu: 24/7 Channels + every "section" the schedule
        # JSON returns today (sport, movies, news, etc.).
        try:
            navigator.navigator().addDirectoryItem(
                '24/7 Channels', 'daddy_channels', 'channels.png', 'DefaultAddonPVRClient.png'
            )
        except Exception:
            pass
        try:
            response = _request(self.schedule_url)
            schedule = json.loads(response) if response else {}
        except Exception:
            schedule = {}
        for key in schedule.keys():
            try:
                title = key.split(' -')[0].strip() or key
                payload = quote_plus(json.dumps(schedule[key]))
                navigator.navigator().addDirectoryItem(
                    title, 'daddy_cats&url=%s' % payload, 'channels.png', 'DefaultAddonPVRClient.png'
                )
            except Exception:
                continue
        navigator.navigator().endDirectory()


    def channels(self):
        try:
            html = _request(self.channels_url)
            anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', html or '')
            seen = set()
            for href, title in anchors[8:]:
                title = (title or '').strip()
                if not title or title in seen:
                    continue
                if not ('stream' in href or 'channel' in href):
                    continue
                # Skip 18+ unless explicitly enabled (matches TV Free behaviour).
                if '18+' in title and (control.setting('adult_pw') or '') != 'xxXXxx':
                    continue
                seen.add(title)
                full = urljoin(BASE_URL, href)
                payload = quote_plus(json.dumps([[title, full]]))
                navigator.navigator().addDirectoryItem(
                    title, 'daddy_play&url=%s' % payload,
                    'channels.png', 'DefaultAddonPVRClient.png',
                    isFolder=False,
                )
        except Exception:
            pass
        navigator.navigator().endDirectory()


    def categories(self, url):
        try:
            data = json.loads(url)
        except Exception:
            data = {}
        for key in data.keys():
            try:
                title = re.sub(r'</?[^>]+>', '', key).strip() or key
                payload = quote_plus(json.dumps(data[key]))
                navigator.navigator().addDirectoryItem(
                    title, 'daddy_events&url=%s' % payload,
                    'channels.png', 'DefaultAddonPVRClient.png',
                )
            except Exception:
                continue
        navigator.navigator().endDirectory()


    def events(self, url):
        try:
            events = json.loads(url)
        except Exception:
            events = []
        for ev in events:
            try:
                title = ev.get('event', '') or ''
                start_time = ev.get('time', '')
                if start_time:
                    title = '%s - %s' % (self._utc_to_local(start_time), title)
                channels = []
                for ch in ev.get('channels', []) or []:
                    name = ch.get('channel_name', '')
                    cid = ch.get('channel_id', '')
                    if not (name and cid):
                        continue
                    channels.append([name, urljoin(BASE_URL, '/stream/stream-%s.php' % cid)])
                if not channels:
                    continue
                payload = quote_plus(json.dumps(channels))
                navigator.navigator().addDirectoryItem(
                    title, 'daddy_play&url=%s' % payload,
                    'channels.png', 'DefaultAddonPVRClient.png',
                    isFolder=False,
                )
            except Exception:
                continue
        navigator.navigator().endDirectory()


    def play(self, url):
        import sys
        import xbmc
        import xbmcgui
        import xbmcplugin
        try:
            channels = json.loads(url)
        except Exception:
            channels = []
        if not channels:
            return
        if len(channels) > 1:
            labels = [c[0] for c in channels]
            sel = xbmcgui.Dialog().select('Choose a Stream', labels)
            if sel == -1:
                return
            stream_url = channels[sel][1]
            title = channels[sel][0]
        else:
            stream_url = channels[0][1]
            title = channels[0][0]

        try:
            page1 = _request(stream_url)
            iframe = re.findall(r"<iframe[^>]*id=['\"]thatframe['\"][^>]*src=['\"]([^'\"]+)['\"]", page1 or '')
            if not iframe:
                iframe = re.findall(r"<iframe[^>]+src=['\"]([^'\"]+)['\"]", page1 or '')
            if not iframe:
                return
            url2 = iframe[0]
            local_headers = dict(HEADERS)
            local_headers['Referer'] = stream_url
            try:
                page2 = client.scrapePage(url2, headers=local_headers, timeout='15').text or ''
            except Exception:
                page2 = client.request(url2, headers=local_headers, timeout='15') or ''
            parsed = urlparse(url2)
            referer_base = '%s://%s' % (parsed.scheme, parsed.netloc)
            srv_lookup = re.findall(r"fetch\(['\"]([^'\"]+)", page2)
            chan_key = re.findall(r'var channelKey = "([^"]+)"', page2)
            domain = re.findall(
                r'"https://" \+ serverKey \+ "(.+?)" \+ serverKey \+ "/" \+ channelKey \+ "/mono.m3u8";',
                page2,
            )
            if not (srv_lookup and chan_key and domain):
                return
            lookup_url = 'https://%s%s%s' % (parsed.netloc, srv_lookup[0], chan_key[0])
            try:
                lookup_resp = client.scrapePage(lookup_url, headers=local_headers, timeout='15').text or '{}'
            except Exception:
                lookup_resp = client.request(lookup_url, headers=local_headers, timeout='15') or '{}'
            try:
                server_key = json.loads(lookup_resp).get('server_key', '')
            except Exception:
                server_key = ''
            if not server_key:
                return
            referer_q = quote_plus(referer_base)
            ua_q = quote_plus(USER_AGENT)
            final = ('https://%s%s%s/%s/mono.m3u8'
                     '|Referer=%s/&Origin=%s&Connection=Keep-Alive&User-Agent=%s'
                     ) % (server_key, domain[0], server_key, chan_key[0],
                          referer_q, referer_q, ua_q)

            liz = xbmcgui.ListItem(title, path=final)
            liz.setInfo('video', {'title': title, 'plot': title})
            liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
            liz.setMimeType('application/x-mpegURL')
            liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
            liz.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
            liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
            try:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
            except Exception:
                pass
            xbmc.Player().play(final, listitem=liz)
        except Exception:
            return


    @staticmethod
    def _utc_to_local(utc_time_str):
        try:
            today = date.today()
            utc_dt = datetime.strptime('%s %s' % (today, utc_time_str), '%Y-%m-%d %H:%M')
            try:
                import pytz
                from tzlocal import get_localzone
                utc_dt = utc_dt.replace(tzinfo=pytz.utc)
                local = utc_dt.astimezone(get_localzone())
                return local.strftime('%I:%M %p').lstrip('0')
            except Exception:
                return utc_dt.strftime('%I:%M %p').lstrip('0')
        except Exception:
            return utc_time_str
