# -*- coding: utf-8 -*-

import re

import six
import simplejson as json

from resources.lib.modules import dom_parser

try: # Py2
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape
except ImportError: # Py3
    from html import unescape


regex_pattern1 = r'(?:iframe|source).+?(?:src)=(?:\"|\')(.+?)(?:\"|\')'
regex_pattern2 = r'(?:data-video|data-src|data-href)=(?:\"|\')(.+?)(?:\"|\')'
regex_pattern3 = r'(?:file|source)(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')'
regex_pattern4 = r'''(magnet:\?[^"']+)'''
regex_pattern5 = r'<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"'
regex_pattern6 = r'''['"]file['"]\s*:\s*['"]([^'"]+)'''
regex_pattern7 = r'''['"]?file['"]?\s*:\s*['"]([^'"]*)'''
regex_pattern8 = r'file(?:\'|\")?\s*(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')'
regex_pattern9 = r'sources\s*:\s*\[(.+?)\]'
regex_pattern10 = r'\{(.+?)\}'


def re_findall(html, regex):
    match = re.findall(regex, html)
    return match


def re_compile(html, regex):
    match = re.compile(regex).findall(html)
    return match


def unpacked(html):
    from resources.lib.modules import jsunpack
    unpacked = ''
    if jsunpack.detect(html):
        unpacked = jsunpack.unpack(html)
    return unpacked


def unpacked2(html):
    from resources.lib.modules import jsunpack
    packed_data = ''
    if jsunpack.detect(html):
        for match in re.finditer(r'''(eval\s*\(function\(p,a,c,k,e,.*?)</script>''', html, re.DOTALL | re.I):
            r = match.group(1)
            t = re.findall(r'(eval\s*\(function\(p,a,c,k,e,)', r, re.DOTALL | re.IGNORECASE)
            if len(t) == 1:
                if jsunpack.detect(r):
                    packed_data += jsunpack.unpack(r)
            else:
                t = r.split('eval')
                t = ['eval' + x for x in t if x]
                for r in t:
                    if jsunpack.detect(r):
                        packed_data += jsunpack.unpack(r)
    return packed_data


def unjuiced2(html):
    from resources.lib.modules import unjuice2
    unjuiced = ''
    if unjuice2.test(html):
        for match in re.finditer(r'(_juicycodes\(.+?[;\n<])', html, re.DOTALL | re.I):
            if unjuice2.test(match.group(1)):
                unjuiced += unjuice2.run(match.group(1))
    return unjuiced


def parseDOM(html, name='', attrs=None, ret=False):
    if attrs:
        attrs = dict((key, re.compile(value + ('$' if value else ''))) for key, value in six.iteritems(attrs))
    results = dom_parser.parse_dom(html, name, attrs, ret)
    if ret:
        results = [result.attrs[ret.lower()] for result in results]
    else:
        results = [result.content for result in results]
    return results


def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)


def remove_codes(string):
    remove = re.compile(r'<.+?>')
    string = re.sub(remove, '', string)
    return string


def replace_html_entities(string):
    List = [['&lt;', '<'], ['&#60;', '<'], ['&gt;', '>'], ['&#62;', '>'],
        ['&amp;', '&'], ['&#38;', '&'], ['&#038;', '&'],
        ['&quot;',' "'], ['&#34;',' "'], ["&apos;", "'"], ["&#39;", "'"], ['\\/', '/']
    ]
    for item in List:
        string = string.replace(item[0], item[1])
    return string


#.replace('\xa0', '')
def replaceHTMLCodes(txt):
    txt = re.sub(r"(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", txt)
    txt = unescape(txt)
    txt = txt.replace("&lt;", "<")
    txt = txt.replace("&#60;", "<")
    txt = txt.replace("&gt;", ">")
    txt = txt.replace("&#62;", ">")
    txt = txt.replace("&amp;", "&")
    txt = txt.replace("&#38;", "&")
    txt = txt.replace("&#038;", "&")
    txt = txt.replace("&quot;", "\"")
    txt = txt.replace("&#34;", "\"")
    txt = txt.replace("&apos;", "\'")
    txt = txt.replace("&#39;", "\'")
    txt = txt.replace("&nbsp;", "")
    txt = txt.replace('&#8230;', '...')
    txt = txt.replace('&#8217;', '\'')
    txt = txt.replace('&#8211;', '-')
    txt = txt.replace("%2B", "+")
    txt = txt.replace("\\/", "/")
    txt = txt.replace("\/", "/")
    txt = txt.replace("\\", "")
    txt = txt.replace('///', '//')
    txt = txt.strip()
    return six.ensure_str(txt)


def clean_html(txt):
    txt = txt.replace('&quot;', '\"')
    txt = txt.replace('&amp;', '&')
    txt = txt.replace('\\n','')
    txt = txt.replace('\\t', '')
    txt = txt.replace('\\', '')
    txt = ' '.join(txt.split())
    return six.ensure_str(txt)


def removeNonAscii(s):
    return "".join(i for i in s if ord(i) < 128)


def byteify(data, ignore_dicts=False):
    if isinstance(data, six.text_type) and six.PY2:
        return data.encode('utf-8')
    if isinstance(data, list):
        return [byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return dict([(byteify(key, ignore_dicts=True), byteify(value, ignore_dicts=True)) for key, value in six.iteritems(data)])
    return data


def json_loads_as_str(json_text):
    return byteify(json.loads(json_text, object_hook=byteify), ignore_dicts=True)


