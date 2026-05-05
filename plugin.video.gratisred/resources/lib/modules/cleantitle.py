# -*- coding: utf-8 -*-

import re
import unicodedata

from six import ensure_str, ensure_text, PY2
from six.moves.urllib_parse import unquote

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control

andToggle = control.setting('sourcefilter.and') or 'false'


def normalize(title):
    try:
        if PY2:
            try:
                return title.decode('ascii').encode("utf-8")
            except:
                pass
            return str(''.join(c for c in unicodedata.normalize('NFKD', title.decode('utf-8')) if not unicodedata.combining(c)))
        return u''.join(c for c in unicodedata.normalize('NFKD', ensure_text(title)) if not unicodedata.combining(c))
    except:
        return title


def get_title(title, sep=' '):
    if not title:
        return
    title = unquote(title)
    title = client_utils.replaceHTMLCodes(title)
    title = title.replace('&', 'and').replace('.html', '').replace('_', sep)
    title = normalize(title)
    title = re.sub(r'[^\w\%s]+' % sep, sep, title)
    title = re.sub(r'\%s{2,}' % sep, sep, title)
    title = title.strip(sep)
    return title


def get(title):
    if not title:
        return
    title = unquote(title)
    title = client_utils.replaceHTMLCodes(title)
    title = title.replace('&', 'and').replace('_', '')
    title = normalize(title)
    title = re.sub(r'<.*?>', '', title).lower()
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'[^\w]+', '', title)
    return title


def getsearch(title):
    if not title:
        return
    title = ensure_str(title, errors='ignore')
    title = title.lower()
    title = re.sub(r'&#(\d+);', '', title)
    title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&').replace('–', '-')
    title = re.sub(r'\\\|/|-|–|:|;|!|\*|\?|"|\'|<|>|\|', '', title)
    return title


def geturl(title):
    if not title:
        return
    title = ensure_str(title, errors='ignore')
    title = title.lower()
    title = title.rstrip()
    try:
        title = title.translate(None, r':*?"\'\.<>|&!,')
    except:
        title = title.translate(str.maketrans('', '', r':*?"\'\.<>|&!,'))
    title = title.replace('!', '')
    title = title.replace('/', '-')
    title = title.replace(' ', '-')
    title = title.replace('–', '-')
    title = title.replace('--', '-')
    return title


def get_under(title):
    if not title:
        return
    title = getsearch(title)
    title = title.replace(' ', '_')
    title = title.replace('__', '_')
    return title


def get_dash(title):
    if not title:
        return
    title = getsearch(title)
    title = title.replace(' ', '-')
    title = title.replace('--', '-')
    return title


def get_plus(title):
    if not title:
        return
    title = getsearch(title)
    title = title.replace(' ', '+')
    title = title.replace('++', '+')
    return title


def get_utf8(title):
    if not title:
        return
    title = getsearch(title)
    title = title.replace(' ', '%20')
    title = title.replace('%20%20', '%20')
    return title


def match_alias(title, aliases):
    try:
        for alias in aliases:
            if get(title) == get(alias['title']):
                return True
        return False
    except:
        return False


def match_year(item, year, premiered=None):
    try:
        if premiered == None:
            check1 = [(int(year))]
            check2 = [(int(year)-1), (int(year)), (int(year)+1)]
        else:
            check1 = [(int(year)), (int(premiered))]
            check2 = [(int(year)-1), (int(year)), (int(year)+1), (int(premiered)-1), (int(premiered)), (int(premiered)+1)]
        if any(str(y) in str(item) for y in check1):
            return True
        if any(str(y) in str(item) for y in check2):
            return True
        return False
    except:
        return False


def scene_title(title, imdb, year):
    title = normalize(title)
    title = ensure_str(title, errors='ignore')
    title = title.replace('&', 'AAANNNDDD').replace('-', ' ').replace('–', ' ').replace('/', ' ').replace('*', ' ').replace('.', ' ')
    #title = re.sub(r'[^A-Za-z0-9 ]+', '', title)
    title = re.sub(r'[^\w\s]+', '', title)
    title = re.sub(r' {2,}', ' ', title).strip()
    if andToggle == 'true':
        title = title.replace('AAANNNDDD', '&')
    else:
        title = title.replace('AAANNNDDD', 'and')
    if title.startswith('Birdman or') and year == '2014':
        title = 'Birdman'
    if title == 'Birds of Prey and the Fantabulous Emancipation of One Harley Quinn' and year == '2020':
        title = 'Birds of Prey'
    if title == "Roald Dahls The Witches" and year == '2020':
        title = 'The Witches'
    return title, imdb, year


def scene_tvtitle(title, imdb, year, season, episode):
    title = normalize(title)
    title = ensure_str(title, errors='ignore')
    title = title.replace('&', 'AAANNNDDD').replace('-', ' ').replace('–', ' ').replace('/', ' ').replace('*', ' ').replace('.', ' ')
    #title = re.sub(r'[^A-Za-z0-9 ]+', '', title)
    title = re.sub(r'[^\w\s]+', '', title)
    title = re.sub(r' {2,}', ' ', title).strip()
    if andToggle == 'true':
        title = title.replace('AAANNNDDD', '&')
    else:
        title = title.replace('AAANNNDDD', 'and')
    if title in ['The Haunting', 'The Haunting of Bly Manor', 'The Haunting of Hill House'] and year == '2018':
        if season == '1':
            title = 'The Haunting of Hill House'
        elif season == '2':
            title = 'The Haunting of Bly Manor'
            year = '2020'
            season = '1'
    if title in ['Cosmos', 'Cosmos A Spacetime Odyssey', 'Cosmos Possible Worlds'] and year == '2014':
        if season == '1':
            title = 'Cosmos A Spacetime Odyssey'
        elif season == '2':
            title = 'Cosmos Possible Worlds'
            year = '2020'
            season = '1'
    if 'Special Victims Unit' in title:
        title = title.replace('Special Victims Unit', 'SVU')
    if title == 'Cobra Kai' and year == '1984':
        year = '2018'
    if title == 'The End of the F ing World':
        title = 'The End of the Fucking World'
    if title == 'M A S H':
        title = 'MASH'
    if title == 'Lupin' and year == '2021':
        if season == '1' and int(episode) > 5:
            season = '2'
            episode = str(int(episode) - 5)
    if title == 'Bleach' and year == '2004':
        if season == '2':
            title = 'Bleach: Thousand-Year Blood War'
            #title = 'Bleach: Sennen Kessen-hen'
            year = '2022'
            season = '1'
            imdb = 'tt14986406'
    #if title == ('King and Maxwell' or 'King & Maxwell'):
        #title = 'King & Maxwell'
    #if title == 'The Office' and year == '2001':
        #title = 'The Office UK'
    #if title == 'House': #Isnt really needed but gives more accurate results this way. might just add it to the scrapers it works on.
        #title = 'House M.D.'
    return title, imdb, year, season, episode


