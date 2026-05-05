# -*- coding: utf-8 -*-

import re
from six import ensure_text
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import source_utils
from resources.lib.modules import log_utils

######################################################
############ Used for process.
######################################################
# Using these gdriveplayer_domains in prepare_link to be lazy. Some are just fake-makes that i tossed in incase they ever show up lol.
gdriveplayer_domains = ['database.gdriveplayer.co', 'database.gdriveplayer.io', 'database.gdriveplayer.me', 'database.gdriveplayer.us', 'database.gdriveplayer.xyz',
    'database,gdriveplayer.co', 'database,gdriveplayer.io', 'database,gdriveplayer.me', 'database,gdriveplayer.us', 'database,gdriveplayer.xyz', # This lines just ghetto made alts incase the api links are fuckered.
    'databasegdriveplayer.co', 'databasegdriveplayer.io', 'databasegdriveplayer.me', 'databasegdriveplayer.us', 'databasegdriveplayer.xyz',
    'series.databasegdriveplayer.co', 'series.databasegdriveplayer.io', 'series.databasegdriveplayer.me', 'series.databasegdriveplayer.us', 'series.databasegdriveplayer.xyz' # Lazy line beisdes the first one lol.
]
gomo_domains = ['gomo.to']
#truepoweroflove_domains = ['truepoweroflove.com']
furher_domains = ['furher.in']
#hlspanel_domains = ['hlspanel.xyz']
linkbin_domains = ['linkbin.me']
#ronemo_domains = ['ronemo.com']
#source_stream_domains = [] # Saved for ramdom odd ones found later lol.
#superembed_domains = ['streamembed.net']
twoembed_domains = ['2embed.cc', '2embed.skin', 'moviekhhd.net']
vidembed_domains = ['goload.io', 'goload.pro', 'membed1.com', 'membed.co', 'membed.net', 'movembed.cc',
    'vidcloud9.com', 'vidembed.cc', 'vidembed.io', 'vidembed.me', 'vidembed.net', 'vidnext.net', 'vidnode.net',
    'anihdplay.com', 'gotaku1.com', 'playtaku.net', 'playtaku.online', 'movstreamhd.pro'
]
vidlink_domains = ['vidlink.org']
vidsrc_domains = ['vidsrc.to', 'vsembed.ru', 'vsembed.su', 'v2.vidsrc.me', 'vidsrc.me']
#voxzer_domains = ['voxzer.org']
######################################################
############ Used for prepare_link.
######################################################
doodstream_redir_domains = ['dood.to', 'dood.so', 'dood.cx', 'dood.pm', 'ds2play.com', 'doods.pro']
######################################################
entervideo_failing_domains = ['entervideo.net', 'eplayvid.com']
######################################################
# Spare Alt  gotaku1.com, playtaku.net, playtaku.online
goload_failing_domains = ['gogohd.pro', 'goload.io', 'streamani.net', 'vidstreaming.io', 'anihdplay.com']
goload_redir_domains = ['gembedhd.com', 'gogo-play.net', 'gogohd.net', 'goload.pro', 'playgo1.cc']
goload_failing_domains = goload_failing_domains + goload_redir_domains
######################################################
gomoplayer_failing_domains = ['gomoplayer.com', 'tunestream.net']
######################################################
streamhide_redir_domains = ['ahvsh.com', 'guccihide.com', 'louishide.com']
streamhide_working_domains = ['streamhide.com', 'streamhide.to', 'movhide.pro', 'moviesm4u.com', 'bikurathulw.sbs', 'javb1.com']
######################################################
streamwish_failing_domains = ['abkrzkz.sbs', 'ajmidyad.sbs', 'atabkhha.sbs', 'atabknha.sbs', 'atabknhk.sbs', 'atabknhs.sbs', 'embedwish.com', 'hayaatieadhab.sbs',
    'khadhnayad.sbs', 'kharabnahs.sbs', 'mwish.pro', 'wishfast.top', 'yadmalik.sbs'
]
streamwish_working_domains = ['abkrzkr.sbs', 'ankrzkz.sbs', 'awish.pro', 'cilootv.store', 'doodporn.xyz', 'dwish.pro', 'streamwish.com', 'streamwish.site',
    'streamwish.to', 'strmwis.xyz', 'tuktukcinema.store', 'vidmoviesb.xyz', 'volvovideo.top', 'wishembed.pro'
]
######################################################
# Spare Alt  movembed.cc | The redirects goto membed1.com i think but done now to be lazy and for dupe checks.
vidcloud9_failing_domains = ['membed.co', 'vidembed.io', 'vidembed.me', 'vidembed.net', 'vidcloud.icu']
vidcloud9_redir_domains = ['membed.net', 'vidcloud9.com', 'vidembed.cc', 'vidnext.net', 'vidnode.net']
vidcloud9_failing_domains = vidcloud9_failing_domains + vidcloud9_redir_domains
######################################################
vidcloud_failing_domains = ['vidcloud.pro', 'vidcloud.is']
######################################################
twoembed_failing_domains = ['2embed.ru', '2embed.to']
######################################################
############ Used for each scrape def.
######################################################
scrape_gdriveplayer = control.setting('scrape.gdriveplayer') or 'true'
scrape_gomo = control.setting('scrape.gomo') or 'true'
scrape_furher = control.setting('scrape.furher') or 'true'
#scrape_hlspanel = control.setting('scrape.hlspanel') or 'true'
scrape_linkbin = control.setting('scrape.linkbin') or 'true'
#scrape_ronemo = control.setting('scrape.ronemo') or 'true'
#scrape_source_stream = control.setting('scrape.source_stream') or 'true'
#scrape_superembed = control.setting('scrape.superembed') or 'true'
#scrape_truepoweroflove = control.setting('scrape.truepoweroflove') or 'true'
scrape_twoembed = control.setting('scrape.twoembed') or 'true'
scrape_vidembed = control.setting('scrape.vidembed') or 'true'
scrape_vidlink = control.setting('scrape.vidlink') or 'true'
scrape_vidsrc = control.setting('scrape.vidsrc') or 'true'
#scrape_voxzer = control.setting('scrape.voxzer') or 'true'
######################################################
mod_domains = control.setting('mod.domains') or 'true'
######################################################


def prepare_link(url):
    if not url:
        return
    url = url.replace("\/", "/")
    url = url.replace("\\", "")
    url = url.replace('///', '//')
    if url.startswith('//'):
        url = 'https:' + url
    if not url.startswith('http'):
        url = re.sub(r'\s+', '', url)
    if not url.startswith('http'):
        #log_utils.log('scrape_sources - prepare_link NOT-link: ' + str(url))
        return
    u = url.replace('//www.', '//')
    if mod_domains == 'true':
        try:
            old_domain = re.findall(r'//(.+?)/', u)[0]
        except:
            #log_utils.log('scrape_sources - prepare_link - old_domain failed-u: ' + str(u))
            return
        if old_domain in doodstream_redir_domains:
            url = url.replace(old_domain, 'doodstream.com')
        elif old_domain in entervideo_failing_domains:
            url = url.replace(old_domain, 'eplayvid.net')
        elif old_domain in gdriveplayer_domains:
            url = url.replace(old_domain, 'databasegdriveplayer.co')
        elif old_domain in goload_failing_domains:
            url = url.replace(old_domain, 'gotaku1.com')
        elif old_domain in gomoplayer_failing_domains:
            url = url.replace(old_domain, 'xvideosharing.com')
        elif old_domain in streamhide_redir_domains:
            url = url.replace(old_domain, 'streamhide.com')
        elif old_domain in streamwish_failing_domains:
            url = url.replace(old_domain, 'streamwish.to')
        elif old_domain in vidcloud9_failing_domains:
            url = url.replace(old_domain, 'movstreamhd.pro')
        elif old_domain in vidcloud_failing_domains:
            url = url.replace(old_domain, 'vidcloud.co')
        elif old_domain in twoembed_failing_domains:
            url = url.replace(old_domain, '2embed.me')
        elif old_domain == 'aparat.cam':
            url = url.replace(old_domain, 'wolfstream.tv')
        elif old_domain == 'clipwatching.com':
            url = url.replace(old_domain, 'highstream.tv')
        elif old_domain == 'cloudvid.co':
            url = url.replace(old_domain, 'cloudvideo.tv')
        elif old_domain == 'fastclick.to':
            url = url.replace(old_domain, 'drop.download')
        elif old_domain == 'gomostream.com':
            url = url.replace(old_domain, 'gomo.to')
        elif old_domain == 'sendit.cloud':
            url = url.replace(old_domain, 'send.cm')
        elif old_domain == 'streamvid.co':
            url = url.replace(old_domain, 'streamvid.cc')
    if '//vidcloud.co/embed/' in u:
        url = url.replace('/embed/', '/v/')  # Ghetto fix to get the resolver pattern to notice the url
    #log_utils.log('scrape_sources - prepare_link link: ' + str(url))
    # this log line should log atleast 90% of the source links when used. altho its gonna have dupes and links from before and after various process steps.
    return url


def check_host_limit(item, items): # lazy way to not import source_utils if i dont gotta and a little less code use sorta.
    return source_utils.check_host_limit(item, items)


def check_direct(hostDict, url, host=None): # unused code saved. now works like is_host_valid but as direct lol.
    try:
        url = prepare_link(url)
        if not url:
            raise Exception()
        host = url if not host else host
        direct_check = tuple(source_utils.supported_video_extensions())
        valid, host = source_utils.is_host_valid(host, hostDict)
        if valid:
            return False, url
        elif '/hls/' in url or url.endswith(direct_check):
            return True, url
        return False, url
    except:
        log_utils.log('check_direct', 1)
        return False, url


def make_direct_item(hostDict, link, host=None, info=None, referer=None, prep=False):
    item = {}
    try:
        if prep:
            link = prepare_link(link)
        if not link:
            return item
        host = link if host == None else host
        info = link if info == None else info
        valid, host = source_utils.is_host_valid(host, hostDict)
        quality, info = source_utils.get_release_quality(link, info)
        if referer:
            link += source_utils.append_headers({'Referer': referer})
        item = {'source': host, 'quality': quality, 'info': info, 'url': link, 'direct': True}
        #log_utils.log('scrape_sources - make_direct_item item: ' + str(item))
        return item
    except:
        log_utils.log('make_direct_item', 1)
        return item


def make_item(hostDict, link, host=None, info=None, prep=False):
    item = {}
    try:
        if prep:
            link = prepare_link(link)
        if not link:
            return item
        host = link if host == None else host
        info = link if info == None else info
        valid, host = source_utils.is_host_valid(host, hostDict)
        if valid:
            quality, info = source_utils.get_release_quality(link, info)
            item = {'source': host, 'quality': quality, 'info': info, 'url': link, 'direct': False}
        #else: log_utils.log('scrape_sources - make_item - non-valid link: ' + str(link))
        #log_utils.log('scrape_sources - make_item item: ' + str(item))
        return item
    except:
        log_utils.log('make_item', 1)
        return item


def process(hostDict, link, host=None, info=None):
    sources = []
    try:
        link = prepare_link(link)
        if not link:
            return sources
        host = link if host == None else host
        info = link if info == None else info
        #if 'google' in link:
            #link = googlestream.googlepass(link)
        if any(i in host for i in gdriveplayer_domains):
            #log_utils.log('scrape_sources - process - gdriveplayer link: '+repr(link))
            for source in gdriveplayer(link, hostDict, info=info):
                sources.append(source)
        elif any(i in host for i in gomo_domains):
            #log_utils.log('scrape_sources - process - gomo link: '+repr(link))
            for source in gomo(link, hostDict, info=info):
                sources.append(source)
        elif any(i in host for i in furher_domains):
            #log_utils.log('scrape_sources - process - furher link: '+repr(link))
            for source in furher(link, hostDict, info=info):
                sources.append(source)
        #elif any(i in host for i in hlspanel_domains):
            #log_utils.log('scrape_sources - process - hlspanel link: '+repr(link))
            #for source in hlspanel(link, hostDict, info=info):
                #sources.append(source)
        elif any(i in host for i in linkbin_domains):
            #log_utils.log('scrape_sources - process - linkbin link: '+repr(link))
            for source in linkbin(link, hostDict, info=info):
                sources.append(source)
        #elif any(i in host for i in ronemo_domains):
            #log_utils.log('scrape_sources - process - ronemo link: '+repr(link))
            #for source in ronemo(link, hostDict, info=info):
                #sources.append(source)
        #elif any(i in host for i in source_stream_domains):
            #log_utils.log('scrape_sources - process - source_stream link: '+repr(link))
            #for source in source_stream(link, hostDict, info=info):
                #sources.append(source)
        #elif any(i in host for i in superembed_domains):
            #log_utils.log('scrape_sources - process - superembed link: '+repr(link))
            #for source in superembed(link, hostDict, info=info):
                #sources.append(source)
        #elif any(i in host for i in truepoweroflove_domains):
            #log_utils.log('scrape_sources - process - truepoweroflove link: '+repr(link))
            #for source in truepoweroflove(link, hostDict, info=info):
                #sources.append(source)
        elif any(i in host for i in twoembed_domains):
            #log_utils.log('scrape_sources - process - twoembed link: '+repr(link))
            for source in twoembed(link, hostDict, info=info):
                sources.append(source)
        elif any(i in host for i in vidembed_domains):
            #log_utils.log('scrape_sources - process - vidembed link: '+repr(link))
            for source in vidembed(link, hostDict, info=info):
                sources.append(source)
        elif any(i in host for i in vidlink_domains):
            #log_utils.log('scrape_sources - process - vidlink link: '+repr(link))
            for source in vidlink(link, hostDict, info=info):
                sources.append(source)
        elif any(i in host for i in vidsrc_domains):
            #log_utils.log('scrape_sources - process - vidsrc link: '+repr(link))
            for source in vidsrc(link, hostDict, info=info):
                sources.append(source)
        #elif any(i in host for i in voxzer_domains):
            #log_utils.log('scrape_sources - process - voxzer link: '+repr(link))
            #for source in voxzer(link, hostDict, info=info):
                #sources.append(source)
        else:
            try:
                item = make_item(hostDict, link, host=host, info=info)
                if item:
                    sources.append(item)
                #else: log_utils.log('scrape_sources - process - non-item link: ' + str(link))
            except:
                log_utils.log('process', 1)
                pass
        return sources
    except Exception:
        log_utils.log('process', 1)
        return sources


def rescrape(url, regex=None): # unused old code saved.
    try:
        html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        if regex:
            link = re.findall(regex, html)[0]
        else:
            link = re.findall(r'(?:file|source)(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')', html)[0]
        return link
    except:
        log_utils.log('rescrape', 1)
        return url


def linkbin(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try:
        if scrape_linkbin == 'false':
            return sources
        html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        results = client_utils.parseDOM(html, 'li', attrs={'class': 'signle-link'})
        results = [(client_utils.parseDOM(i, 'a', ret='href'), client_utils.parseDOM(i, 'a')) for i in results]
        results = [(i[0][0], i[1][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0]
        for result in results:
            try:
                url = prepare_link(result[0])
                if not url:
                    continue
                if info:
                    info += ' ' + result[1]
                else:
                    info = result[1]
                item = make_item(hostDict, url, host=None, info=info)
                if item:
                    sources.append(item)
                #else: log_utils.log('scrape_sources - linkbin - non-item link: ' + str(url))
            except:
                log_utils.log('linkbin', 1)
                pass
        return sources
    except Exception:
        log_utils.log('linkbin', 1)
        return sources


def gomo(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try:
        if scrape_gomo == 'false':
            return sources
        domain = re.findall(r'(?://|\.)(playerhost\.net|gomo\.to|gomostream\.com|gomoplayer\.com)/', link)[0]
        gomo_link = 'https://%s/decoding_v3.php' % domain
        result = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        tc = re.compile(r'tc = \'(.+?)\';').findall(result)[0]
        token = re.compile(r'"_token": "(.+?)",').findall(result)[0]
        post = {'tokenCode': tc, '_token': token}
        def tsd(tokenCode):
            _13x48X = tokenCode
            _71Wxx199 = _13x48X[4:18][::-1]
            return _71Wxx199 + "18" + "432782"
        headers = {'Host': domain, 'Referer': link, 'User-Agent': client.UserAgent, 'x-token': tsd(tc)}
        urls = client.request(gomo_link, XHR=True, post=post, headers=headers, output='json', timeout='5')
        for url in urls:
            try:
                url = prepare_link(url)
                if not url:
                    continue
                if 'gomo.to' in url or 'playerhost.net' in url:
                    headers = {'User-Agent': client.UserAgent, 'Referer': url}
                    url = client.request(url, headers=headers, output='geturl', timeout='5')
                    url = prepare_link(url)
                    if not url:
                        continue
                    if url == 'http://ww1.gomoplayer.com/':
                        continue
                    if any(i in url for i in gdriveplayer_domains):
                        for source in gdriveplayer(url, hostDict):
                            sources.append(source)
                    else:
                        item = make_item(hostDict, url, host=None, info=info)
                        if item:
                            sources.append(item)
                        #else: log_utils.log('scrape_sources - gomo - non-item link1: ' + str(url))
                else:
                    item = make_item(hostDict, url, host=None, info=info)
                    if item:
                        sources.append(item)
                    #else: log_utils.log('scrape_sources - gomo - non-item link2: ' + str(url))
            except:
                log_utils.log('gomo', 1)
                pass
        return sources
    except Exception:
        log_utils.log('gomo', 1)
        return sources


def gdriveplayer(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try:
        if scrape_gdriveplayer == 'false':
            return sources
        html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        servers = client_utils.parseDOM(html, 'ul', attrs={'class': 'list-server-items'})[0]
        urls = client_utils.parseDOM(servers, 'a', ret='href')
        for url in urls:
            try:
                if not url or url.startswith('/player.php'):
                    continue
                url = prepare_link(url)
                if not url:
                    continue
                item = make_item(hostDict, url, host=None, info=info)
                if item:
                    sources.append(item)
                #else: log_utils.log('scrape_sources - gdriveplayer - non-item link: ' + str(url))
            except:
                log_utils.log('gdriveplayer', 1)
                pass
        return sources
    except Exception:
        log_utils.log('gdriveplayer', 1)
        return sources


def vidembed(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try:
        try:
            if scrape_vidembed == 'false':
                return sources
            html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
            urls = []
            urls += client_utils.parseDOM(html, 'li', ret='data-video')
            urls += client_utils.parseDOM(html, 'iframe', ret='src')
            if urls:
                for url in urls:
                    try:
                        url = prepare_link(url)
                        if not url:
                            continue
                        item = make_item(hostDict, url, host=None, info=info)
                        if item:
                            sources.append(item)
                        #else: log_utils.log('scrape_sources - vidembed - non-item link1: ' + str(url))
                    except:
                        log_utils.log('vidembed', 1)
                        pass
        except:
            log_utils.log('vidembed', 1)
            pass
        try:
            item = make_item(hostDict, link, host=None, info=info)
            if item:
                sources.append(item)
            #else: log_utils.log('scrape_sources - vidembed - non-item link2: ' + str(link))
        except:
            log_utils.log('vidembed', 1)
            pass
        return sources
    except Exception:
        log_utils.log('vidembed', 1)
        return sources


def vidlink(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Blocked.(update_views page)
    try:
        if scrape_vidlink == 'false':
            return sources
        try:
            postID = link.split('/embed/')[1]
            post_link = 'https://vidlink.org/embed/update_views'
            headers = {'User-Agent': client.UserAgent, 'Referer': link}
            ihtml = client.request(post_link, post={'postID': postID}, headers=headers, XHR=True)
            if ihtml:
                linkcode = client_utils.unpacked(ihtml)
                linkcode = linkcode.replace('\\', '')
                links = re.findall(r'var file1="(.+?)"', linkcode)[0]
                stream_link = links.split('/pl/')[0]
                headers = {'Referer': 'https://vidlink.org/', 'User-Agent': client.UserAgent}
                response = client.scrapePage(links, headers=headers).text
                urls = re.findall(r'[A-Z]{10}=\d+x(\d+)\W[A-Z]+=\"\w+\"\s+\/(.+?)\.', response)
                if urls:
                    for qual, url in urls:
                        url = stream_link + '/' + url + '.m3u8'
                        qual = qual + ' ' + info if not info == None else qual
                        item = make_item(hostDict, url, host=None, info=qual)
                        if item:
                            sources.append(item)
                        #else: log_utils.log('scrape_sources - vidlink - non-item link: ' + str(url))
        except:
            headers = {'User-Agent': client.UserAgent, 'Referer': link}
            html = client.scrapePage(link, headers=headers).text
            iframe = client_utils.parseDOM(html, 'iframe', ret='src')
            for i in iframe:
                for source in process(hostDict, i):
                    sources.append(source)
        return sources
    except Exception:
        log_utils.log('vidlink', 1)
        return sources


def vidsrc(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try: # https://vidsrc.to/embed/tv/72710/1/1
        if scrape_vidsrc == 'false':
            return sources
        domain = re.findall(r'(?://|\.)(v2\.vidsrc\.me|vidsrc\.me|vidsrc\.to)/', link)[0]
        headers = {'User-Agent': client.UserAgent, 'Referer': 'https://%s/' % domain}
        html = client.scrapePage(link, headers=headers).text
        items = client_utils.parseDOM(html, 'div', ret='data-hash')
        for item in items:
            try:
                item_base = 'https://source.%s/source/' % domain
                item_url = item_base + item
                item_html = client.scrapePage(item_url, headers=headers).text
                if not item_html:
                    continue
                item_html = item_html.replace("\'", '"')
                item_src = re.findall(r'src:\s*"([^"]+)"', item_html, re.DOTALL)[0]
                item_src = 'https:' + item_src if item_src.startswith('//') else item_src
                item_link = client.request(item_src, headers=headers, output='geturl')
                url = prepare_link(item_link)
                if not url:
                    continue
                item = make_item(hostDict, url, host=None, info=info)
                if item:
                    sources.append(item)
                #else: log_utils.log('scrape_sources - vidsrc - non-item link: ' + str(url))
            except:
                log_utils.log('vidsrc', 1)
                pass
        return sources
    except Exception:
        log_utils.log('vidsrc', 1)
        return sources


def twoembed(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 6-28-2023  Status: Working.
    try:
        if scrape_twoembed == 'false':
            return sources
        link = link.replace('/embed/imdb/tv?id=', '/embed/')
        link = link.replace('/embed/imdb/movie?id=', '/embed/')
        link = link.replace('/embed/tmdb/tv?id=', '/embed/')
        link = link.replace('/embed/tmdb/movie?id=', '/embed/')
        headers = {'User-Agent': client.UserAgent, 'Referer': link}
        html = client.scrapePage(link, headers=headers).text
        iframe = client_utils.parseDOM(html, 'iframe', ret='src')[0]
        iframe_html = client.scrapePage(iframe, headers=headers).text
        try:
            iframe_unpacked = client_utils.unpacked(iframe_html)
        except:
            iframe_unpacked = ''
        if not iframe_unpacked:
            iframe_unpacked = iframe_html
        iframe_sources = re.findall(r'sources:\[(.+?)\]', iframe_unpacked, re.S)[0]
        source_link = re.findall(r'(?:file|src)\s*(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')', iframe_sources)[0]
        item = make_direct_item(hostDict, source_link, host='2embed.me', info=info, referer=link)
        if item:
            sources.append(item)
        #else: log_utils.log('scrape_sources - twoembed - non-item link: ' + str(url))
        return sources
    except Exception:
        log_utils.log('twoembed', 1)
        return sources


def furher(link, hostDict, info=None):
    sources = [] # Last Tested/Checked: 8-12-2023  Status: Working.
    try: #https://furher.in/e/g5pjexss0zhm
        if scrape_furher == 'false':
            return sources
        embed_html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        embed_unpacked = client_utils.unpacked(embed_html)
        embed_sources = re.findall(r'sources:\[(.+?)\]', embed_unpacked, re.S)[0]
        source_link = re.findall(r'(?:file|src)\s*(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')', embed_sources)[0]
        item = make_direct_item(hostDict, source_link, host='furher.in', info=info, referer=link)
        if item:
            sources.append(item)
        #else: log_utils.log('scrape_sources - furher - non-item link: ' + str(url))
        return sources
    except Exception:
        log_utils.log('furher', 1)
        return sources


#def hlspanel(link, hostDict, info=None):
    #sources = []
    #try:
        #if scrape_hlspanel == 'false':
            #return sources
        #headers = {'User-Agent': client.UserAgent, 'Referer': link, 'X-Requested-With': 'XMLHttpRequest'}
        #url_hash = link.split('/video/')[1]
        #getvid_link = 'https://hlspanel.xyz/player/index.php?data=%s&do=getVideo' % url_hash
        #data = {"hash": url_hash, "r": link}
        #page = client.scrapePage(getvid_link, headers=headers, post=data).json()
        #url = page["securedLink"]
        #item = make_direct_item(hostDict, url, host=None, info=info, referer=link)
        #if item:
            #sources.append(item)
        #return sources
    #except Exception:
        #log_utils.log('hlspanel', 1)
        #return sources


#def superembed(link, hostDict, info=None):
    #sources = []
    #try:
        #if scrape_superembed == 'false':
            #return sources
        #r = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        #i = client_utils.parseDOM(r, 'iframe', ret='src')[0]
        #p = re.findall(r'''window.atob\('(.+?)'\)''', i)[0]
        #link = base64.b64decode(p)
        #link = ensure_text(link, errors='ignore')
        #url = link.replace('\/', '/').replace('///', '//')
        #item = make_item(hostDict, url, host=None, info=info)
        #if item:
            #sources.append(item)
        #else: log_utils.log('scrape_sources - superembed - non-item link: ' + str(url))
        #return sources
    #except Exception:
        #log_utils.log('superembed', 1)
        #return sources


#def truepoweroflove(link, hostDict, info=None):
    #sources = [] # Last Tested/Checked: 10-6-2023  Status: Working.
    #try: #https://truepoweroflove.com/e/7ob3wdc0jkjx
        #if scrape_truepoweroflove == 'false':
            #return sources
        #embed_html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        #embed_unpacked = client_utils.unpacked(embed_html)
        #embed_sources = re.findall(r'sources:\[(.+?)\]', embed_unpacked, re.S)[0]
        #source_link = re.findall(r'(?:file|src)\s*(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')', embed_sources)[0]
        #item = make_direct_item(hostDict, source_link, host='truepoweroflove.com', info=info, referer=link)
        #if item:
            #sources.append(item)
        #else: log_utils.log('scrape_sources - truepoweroflove - non-item link: ' + str(url))
        #return sources
    #except Exception:
        #log_utils.log('truepoweroflove', 1)
        #return sources


#def ronemo(link, hostDict, info=None):
    #sources = []
    #try:
        #if scrape_ronemo == 'false':
            #return sources
        #html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        #url = re.findall(r'"link":"(.+?)",', html)[0]
        #item = make_direct_item(hostDict, url, host=None, info=info, referer=link)
        #if item:
            #sources.append(item)
        #return sources
    #except:
        #log_utils.log('ronemo', 1)
        #return sources


#def voxzer(link, hostDict, info=None):
    #sources = []
    #try:
        #if scrape_voxzer == 'false':
            #return sources
        #link = link.replace('/view/', '/list/')
        #html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).json()
        #url = html['link']
        #item = make_direct_item(hostDict, url, host=None, info=info, referer=link)
        #if item:
            #sources.append(item)
        #return sources
    #except Exception:
        #log_utils.log('voxzer', 1)
        #return sources


#def source_stream(link, hostDict, info=None):
    #sources = []
    #try:
        #if scrape_source_stream == 'false':
            #return sources
        #html = client.scrapePage(link, headers={'User-Agent': client.UserAgent, 'Referer': link}).text
        #url = client_utils.parseDOM(html, 'source', ret='src')[0]
        #item = make_direct_item(hostDict, url, host=None, info=info, referer=link)
        #if item:
            #sources.append(item)
        #return sources
    #except Exception:
        #log_utils.log('source_stream', 1)
        #return sources


