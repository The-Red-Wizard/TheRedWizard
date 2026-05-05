# -*- coding: utf-8 -*-

import re

from kodi_six import xbmc
import six
from six.moves import urllib_parse

from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import trakt


RES_4K = ['hd4k', '4khd', 'uhd', 'ultrahd', 'ultra hd', 'ultra high', '2160p', '2160i', 'hd2160', '2160hd', '1716p', '1716i', 'hd1716', '1716hd', '2664p', '2664i', 'hd2664', '2664hd', '3112p', '3112i', 'hd3112', '3112hd', '2880p', '2880i', 'hd2880', '2880hd']
RES_1080 = ['1080', '1080p', '1080i', 'hd1080', '1080hd', '1200p', '1200i', 'hd1200', '1200hd']
RES_720 = ['720', '720p', '720i', 'hd720', '720hd', 'hd']
RES_SD = ['576p', '576i', 'sd576', '576sd', '480p', '480i', 'sd480', '480sd', '360p', '360i', 'sd360', '360sd', '240p', '240i', 'sd240', '240sd', 'sd']
RES_SCR = ['dvdscr', 'screener', 'scr']
RES_CAM = ['camrip', 'cam rip', 'tsrip', 'ts rip', 'hdcam', 'hd cam', 'hdts', 'hd ts', 'dvdcam', 'dvd cam', 'dvdts', 'dvd ts', 'cam', 'telesync', 'tele sync', 'ts']

CODEC_H265 = ['hevc', 'h265', 'x265']
CODEC_H264 = ['avc', 'h264', 'x264']
CODEC_XVID = ['xvid']
CODEC_DIVX = ['divx', 'div2', 'div3']
CODEC_MPEG = ['mpeg', 'm4v', 'mpg', 'mpg1', 'mpg2', 'mpg3', 'mpg4', 'msmpeg', 'msmpeg4', 'mpegurl']
CODEC_MP4 = ['mp4']
CODEC_M3U = ['m3u8', 'm3u']
CODEC_AVI = ['avi']
CODEC_MKV = ['mkv', 'matroska']

AUDIO_8CH = ['ch8', '8ch', 'ch7', '7ch', '7 1', 'ch7 1', '7 1ch']
AUDIO_6CH = ['ch6', '6ch', 'ch6', '6ch', '6 1', 'ch6 1', '6 1ch', '5 1', 'ch5 1', '5 1ch']
AUDIO_2CH = ['ch2', '2ch', 'stereo', 'dualaudio', 'dual', '2 0', 'ch2 0', '2 0ch']
AUDIO_1CH = ['ch1', '1ch', 'mono', 'monoaudio', 'ch1 0', '1 0ch']

VIDEO_3D = ['3d', 'sbs', 'hsbs', 'sidebyside', 'side by side', 'stereoscopic', 'tab', 'htab', 'topandbottom', 'top and bottom']


host_limit = control.setting('host.limit') or 'true'
host_limit_count = int(control.setting('host.count')) or '3'
def check_host_limit(item, items): # lazy way to use less code and limit the sources a bit. could likely be coded better but oh well.
    try:
        if host_limit == 'true':
            items = [i['source'] for i in items if 'source' in i] or [i for i in items]
            if items.count(item) == host_limit_count:
                return True
            else:
                return False
        else:
            return False
    except:
        return False


websites = set()
def check_dupes(url):
    parsed = urllib_parse.urlparse(url)
    website = parsed.hostname + parsed.path
    if website in websites:
        return False
    websites.add(website)
    return True


def append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, urllib_parse.quote_plus(headers[key])) for key in headers])


def supported_video_extensions():
    try:
        supported_video_extensions = xbmc.getSupportedMedia('video').split('|')
        video_formats = [i for i in supported_video_extensions if i != '' and i != '.zip']
        return video_formats
    except:
        return []


def is_anime(content, type, type_id):
    try:
        r = trakt.getGenre(content, type, type_id)
        return 'anime' in r or 'animation' in r
    except:
        return False


def aliases_to_array(aliases, filter=None):
    try:
        if not filter:
            filter = []
        if isinstance(filter, six.string_types):
            filter = [filter]
        return [x.get('title') for x in aliases if not filter or x.get('country') in filter]
    except:
        return []


def strip_domain(url):
    try:
        url = client_utils.replaceHTMLCodes(url)
        if url.lower().startswith('http') or url.startswith('/'):
            url = re.findall(r'(?://.+?|)(/.+)', url)[0]
        return url
    except:
        return url


def __top_domain(url):
    url = url.replace('\/', '/').replace('///', '//')
    if not (url.startswith('//') or url.startswith('http://') or url.startswith('https://')):
        url = '//' + url
    elements = urllib_parse.urlparse(url)
    domain = elements.netloc or elements.path
    domain = domain.split('@')[-1].split(':')[0]
    regex = r"(?:www\.)?([\w\-]*\.[\w\-]{2,3}(?:\.[\w\-]{2,3})?)$"
    res = re.search(regex, domain)
    if res:
        domain = res.group(1)
    domain = domain.lower()
    return domain


def is_host_valid(url, domains):
    try:
        host = __top_domain(url)
        hosts = [domain.lower() for domain in domains if host and host in domain.lower()]
        if hosts and '.' not in host:
            host = hosts[0]
        if hosts and any([h for h in ['google', 'picasa', 'blogspot'] if h in host]):
            host = 'gvideo'
        if hosts and any([h for h in ['akamaized', 'ocloud'] if h in host]):
            host = 'CDN'
        return any(hosts), host
    except:
        return False, ''


def get_host(url):
    try:
        url = url.replace('\/', '/').replace('///', '//')
        elements = urllib_parse.urlparse(url)
        domain = elements.netloc or elements.path
        domain = domain.split('@')[-1].split(':')[0]
        res = re.search(r"(?:www\.)?([\w\-]*\.[\w\-]{2,3}(?:\.[\w\-]{2,3})?)$", domain)
        if res:
            domain = res.group(1)
        domain = domain.lower()
    except:
        elements = urllib_parse.urlparse(url)
        host = elements.netloc
        domain = host.replace('www.', '')
    return domain


def checkHost(url, hostList):
    host = get_host(url)
    validHost = False
    for i in hostList:
        if i.lower() in url.lower():
            host = i
            validHost = True
            return validHost, host
    return validHost, host


def get_codec(txt):
    if any(value in txt for value in CODEC_H265):
        _codec = "HEVC | "
    elif any(value in txt for value in CODEC_H264):
        _codec = "AVC | "
    elif any(value in txt for value in CODEC_MKV):
        _codec = "MKV | "
    elif any(value in txt for value in CODEC_DIVX):
        _codec = "DIVX | "
    elif any(value in txt for value in CODEC_MPEG):
        _codec = "MPEG | "
    elif any(value in txt for value in CODEC_MP4):
        _codec = "MP4 | "
    elif any(value in txt for value in CODEC_M3U):
        _codec = "M3U | "
    elif any(value in txt for value in CODEC_XVID):
        _codec = "XVID | "
    elif any(value in txt for value in CODEC_AVI):
        _codec = "AVI | "
    else:
        _codec = '0'
    return _codec


def get_audio(txt):
    if any(value in txt for value in AUDIO_8CH):
        _audio = "7.1 | "
    elif any(value in txt for value in AUDIO_6CH):
        _audio = "5.1 | "
    elif any(value in txt for value in AUDIO_2CH):
        _audio = "2.0 | "
    elif any(value in txt for value in AUDIO_1CH):
        _audio = "Mono | "
    else:
        _audio = '0'
    return _audio


def get_size(txt):
    try:
        _size = re.findall(r'(\d+(?:\.|/,|)?\d+(?:\s+|)(?:gb|GiB|mb|MiB|GB|MB))', txt)
        _size = _size[0].encode('utf-8')
        _size = _size + " | "
    except:
        _size = '0'
    return _size


def get_3D(txt):
    if any(value in txt for value in VIDEO_3D):
        _3D = "3D | "
    else:
        _3D = '0'
    return _3D


def get_quality(txt1, txt2=None):
    if not txt2:
        txt = txt1
    else:
        txt = txt1
        txt += txt2
    if any(value in txt for value in RES_4K):
        _quality = "4K"
    elif any(value in txt for value in RES_1080):
        _quality = "1080p"
    elif any(value in txt for value in RES_720):
        _quality = "720p"
    elif any(value in txt for value in RES_SD):
        _quality = "SD"
    elif any(value in txt for value in RES_SCR):
        _quality = "SCR"
    elif any(value in txt for value in RES_CAM):
        _quality = "CAM"
    else:
        _quality = "SD"
    return _quality


def get_info(txt1, txt2=None):
    if not txt2:
        txt = txt1
    else:
        txt = txt1
        txt += txt2
    _codec = get_codec(txt)
    if not _codec or _codec == '0':
        _codec = ''
    _audio = get_audio(txt)
    if not _audio or _audio == '0':
        _audio = ''
    _size = get_size(txt)
    if not _size or _size == '0':
        _size = ''
    _3D = get_3D(txt)
    if not _3D or _3D == '0':
        _3D = ''
    _info = _codec + _audio + _size + _3D
    return _info


def cleanup(txt):
    try:
        _txt = strip_domain(txt)
        _txt = urllib_parse.unquote(_txt)
        _txt = _txt.lower()
        _txt = re.sub(r'[^a-z0-9 ]+', ' ', _txt)
    except:
        _txt = str(txt.lower())
    return _txt


def cleanupALT(txt):
    try:
        _txt = strip_domain(txt)
        _txt = _txt.upper()
        _txt = re.sub(r'(.+)(\.|\(|\[|\s)(\d{4}|S\d*E\d*|S\d*)(\.|\)|\]|\s)', '', _txt)
        _txt = re.split(r'\.|\(|\)|\[|\]|\s|-', _txt)
        _txt = [i.lower() for i in _txt]
    except:
        _txt = str(txt.lower())
    return _txt


def get_release_quality(release_name, release_link=None):
    try:
        if not release_name:
            return 'SD', []
        try:
            release_name = cleanup(release_name)
            if release_link:
                release_link = cleanup(release_link)
        except:
            release_name = cleanupALT(release_name)
            if release_link:
                release_link = cleanupALT(release_link)
        if release_link and release_link == release_name:
            release_link = None
        quality = get_quality(release_name, release_link)
        info = get_info(release_name, release_link)
        return quality, info
    except:
        return 'SD', []


