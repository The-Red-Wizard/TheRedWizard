# -*- coding: utf-8 -*-

import re

import simplejson as json
from six.moves import urllib_parse

from resources.lib.modules import client


def googletag(url, append_height=False):
    quality = re.compile(r'itag=(\d*)').findall(url)
    quality += re.compile(r'=m(\d*)$').findall(url)
    try:
        quality = quality[0]
    except:
        return []
    itag_map = {'5': {'quality': 'SD', 'height': 240}, '6': {'quality': 'SD', 'height': 270},
        '17': {'quality': 'SD', 'height': 144}, '18': {'quality': 'SD', 'height': 360}, '22': {'quality': 'HD', 'height': 720},
        '34': {'quality': 'SD', 'height': 360}, '35': {'quality': 'SD', 'height': 480}, '37': {'quality': '1080p', 'height': 1080},
        '38': {'quality': '4K', 'height': 3072}, '43': {'quality': 'SD', 'height': 360}, '44': {'quality': 'SD', 'height': 480},
        '45': {'quality': 'HD', 'height': 720}, '46': {'quality': '1080p', 'height': 1080}, '59': {'quality': 'SD', 'height': 480},
        '78': {'quality': 'SD', 'height': 480}, '82': {'quality': 'SD', 'height': 360}, '83': {'quality': 'SD', 'height': 480},
        '84': {'quality': 'HD', 'height': 720}, '85': {'quality': '1080p', 'height': 1080}, '91': {'quality': 'SD', 'height': 144},
        '92': {'quality': 'SD', 'height': 240}, '93': {'quality': 'SD', 'height': 360}, '94': {'quality': 'SD', 'height': 480},
        '95': {'quality': 'HD', 'height': 720}, '96': {'quality': '1080p', 'height': 1080}, '100': {'quality': 'SD', 'height': 360},
        '101': {'quality': 'SD', 'height': 480}, '102': {'quality': 'HD', 'height': 720}, '132': {'quality': 'SD', 'height': 240},
        '133': {'quality': 'SD', 'height': 240}, '134': {'quality': 'SD', 'height': 360}, '135': {'quality': 'SD', 'height': 480},
        '136': {'quality': 'HD', 'height': 720}, '137': {'quality': '1080p', 'height': 1080}, '151': {'quality': 'SD', 'height': 72},
        '160': {'quality': 'SD', 'height': 144}, '167': {'quality': 'SD', 'height': 360}, '168': {'quality': 'SD', 'height': 480},
        '169': {'quality': 'HD', 'height': 720}, '170': {'quality': '1080p', 'height': 1080}, '212': {'quality': 'SD', 'height': 480},
        '218': {'quality': 'SD', 'height': 480}, '219': {'quality': 'SD', 'height': 480}, '242': {'quality': 'SD', 'height': 240},
        '243': {'quality': 'SD', 'height': 360}, '244': {'quality': 'SD', 'height': 480}, '245': {'quality': 'SD', 'height': 480},
        '246': {'quality': 'SD', 'height': 480}, '247': {'quality': 'HD', 'height': 720}, '248': {'quality': '1080p', 'height': 1080},
        '264': {'quality': '1440p', 'height': 1440}, '266': {'quality': '4K', 'height': 2160}, '271': {'quality': '1440p', 'height': 1440},
        '272': {'quality': '4K', 'height': 2160}, '278': {'quality': 'SD', 'height': 144}, '298': {'quality': 'HD', 'height': 720},
        '299': {'quality': '1080p', 'height': 1080}, '302': {'quality': 'HD', 'height': 720}, '303': {'quality': '1080p', 'height': 1080},
        '308': {'quality': '1440p', 'height': 1440}, '313': {'quality': '4K', 'height': 2160}, '315': {'quality': '4K', 'height': 2160}
    }
    if quality in itag_map:
        quality = itag_map[quality]
        if append_height:
            return [{'quality': quality['quality'], 'height': quality['height'], 'url': url}]
        else:
            return [{'quality': quality['quality'], 'url': url}]
    else:
        return []


def googlepass(url):
    try:
        try:
            headers = dict(urllib_parse.parse_qsl(url.rsplit('|', 1)[1]))
        except:
            headers = None
        url = url.split('|')[0].replace('\\', '')
        url = client.request(url, headers=headers, output='geturl')
        if 'requiressl=yes' in url:
            url = url.replace('http://', 'https://')
        else:
            url = url.replace('https://', 'http://')
        if headers:
            url += '|%s' % urllib_parse.urlencode(headers)
        return url
    except:
        return


def google(url):
    try:
        if any(x in url for x in ['youtube.', 'docid=']):
            url = 'https://drive.google.com/file/d/%s/view' % re.compile(r'docid=([\w-]+)').findall(url)[0]
        netloc = urllib_parse.urlparse(url.strip().lower()).netloc
        netloc = netloc.split('.google')[0]
        if netloc == 'docs' or netloc == 'drive':
            url = url.split('/preview', 1)[0]
            url = url.replace('drive.google.com', 'docs.google.com')
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}
        result = client.request(url, output='extended', headers=headers)
        try:
            headers['Cookie'] = result[2]['Set-Cookie']
        except:
            pass
        result = result[0]
        if netloc == 'docs' or netloc == 'drive':
            result = re.compile(r'"fmt_stream_map",(".+?")').findall(result)[0]
            result = json.loads(result)
            result = [i.split('|')[-1] for i in result.split(',')]
            result = sum([googletag(i, append_height=True) for i in result], [])
        elif netloc == 'photos':
            result = result.replace('\r', '').replace('\n', '').replace('\t', '')
            result = re.compile(r'"\d*/\d*x\d*.+?","(.+?)"').findall(result)[0]
            result = result.replace('\\u003d', '=').replace('\\u0026', '&')
            result = re.compile(r'url=(.+?)&').findall(result)
            result = [urllib_parse.unquote(i) for i in result]
            result = sum([googletag(i, append_height=True) for i in result], [])
        elif netloc == 'picasaweb':
            id = re.compile(r'#(\d*)').findall(url)[0]
            result = re.search(r'feedPreload:\s*(.*}]}})},', result, re.DOTALL).group(1)
            result = json.loads(result)['feed']['entry']
            if len(result) > 1:
                result = [i for i in result if str(id) in i['link'][0]['href']][0]
            elif len(result) == 1:
                result = result[0]
            result = result['media']['content']
            result = [i['url'] for i in result if 'video' in i['type']]
            result = sum([googletag(i, append_height=True) for i in result], [])
        elif netloc == 'plus':
            id = (urllib_parse.urlparse(url).path).split('/')[-1]
            result = result.replace('\r', '').replace('\n', '').replace('\t', '')
            result = result.split('"%s"' % id)[-1].split(']]')[0]
            result = result.replace('\\u003d', '=').replace('\\u0026', '&')
            result = re.compile(r'url=(.+?)&').findall(result)
            result = [urllib_parse.unquote(i) for i in result]
            result = sum([googletag(i, append_height=True) for i in result], [])
        result = sorted(result, key=lambda i: i.get('height', 0), reverse=True)
        url = []
        for q in ['4K', '1440p', '1080p', 'HD', 'SD']:
            try:
                url += [[i for i in result if i.get('quality') == q][0]]
            except:
                pass
        for i in url:
            i.pop('height', None)
            i.update({'url': i['url'] + '|%s' % urllib_parse.urlencode(headers)})
        if not url: return
        return url
    except:
        return


