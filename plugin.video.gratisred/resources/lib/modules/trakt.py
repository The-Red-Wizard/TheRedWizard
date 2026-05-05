# -*- coding: utf-8 -*-

import re
import time

import requests
from requests.compat import json, str
#import simplejson as json
from six import ensure_str, ensure_text
from six.moves.urllib_parse import urljoin, quote_plus

from resources.lib.modules import cache
from resources.lib.modules import cleandate
from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import log_utils


# ---------------------------------------------------------------------------
# PAGINATION HELPER
# ---------------------------------------------------------------------------
# Why: several Trakt endpoints the add-on uses (``/users/me/favorites/*``,
# ``/users/me/collection/*``, some legacy callers) and the local SQLite
# favorites DB return the *entire* collection in a single payload.  With
# large accounts that means the directory freezes Kodi for several
# seconds while every row is rendered, even though the user only ever
# looks at the first page.  This helper produces the current page slice
# and a ``next_page`` integer (or None) that callers can turn into a
# "Next Page" directory entry - exact same UX the existing server-side
# paginated views already have.  Keeping it here (rather than copying
# the logic into every indexer) means it can be reused from movies.py,
# tvshows.py, episodes.py and modules.favorites consistently.
def paginate(items, page=1, page_size=None):
    """Slice ``items`` for directory pagination.

    Returns (page_items, next_page_number_or_None).  ``page`` is 1-based
    to match Trakt's own ``page=1`` convention.  ``page_size`` defaults to
    the add-on's "items.per.page" setting (falling back to 40 if unset /
    invalid) so the directory behaviour matches the rest of the add-on.
    """
    try:
        page = int(page) if page else 1
    except Exception:
        page = 1
    if page < 1:
        page = 1
    if not page_size:
        try:
            page_size = int(control.setting('items.per.page'))
        except Exception:
            page_size = 0
        if not page_size or page_size <= 0:
            page_size = 40
    items = items or []
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    next_page = page + 1 if end < len(items) else None
    return page_items, next_page

BASE_URL = 'https://api.trakt.tv'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
V2_API_KEY = '33ea6bfa2b06c9cfa3e408fc6b4cc30484f31b90733df3508fd09ce512f47982'
CLIENT_SECRET = '4a294afdab95894be977dc79c9715224dc87a4a88d74944507945ca58bf719b2'


def getTraktCredentialsInfo():
    user = control.setting('trakt.user').strip()
    token = control.setting('trakt.token')
    refresh = control.setting('trakt.refresh')
    if (user == '' or token == '' or refresh == ''):
        return False
    return True


def __getTraktALT(url, post=None):
    try:
        url = urljoin(BASE_URL, url) if not url.startswith(BASE_URL) else url
        post = json.dumps(post) if post else None
        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': '2'}
        if getTraktCredentialsInfo():
            headers.update({'Authorization': 'Bearer %s' % control.setting('trakt.token')})
        result = client.request(url, post=post, headers=headers, output='extended', error=True)
        result = client_utils.byteify(result)
        resp_code = result[1]
        resp_header = result[2]
        result = result[0]
        if resp_code in ['423', '500', '502', '503', '504', '520', '521', '522', '524']:
            log_utils.log('Trakt Error: %s' % str(resp_code))
            control.infoDialog('Trakt Error: ' + str(resp_code), sound=True)
            return
        elif resp_code in ['429']:
            log_utils.log('Trakt Rate Limit Reached: %s' % str(resp_code))
            control.infoDialog('Trakt Rate Limit Reached: ' + str(resp_code), sound=True)
            return
        elif resp_code in ['404']:
            log_utils.log('Trakt Object Not Found : %s' % str(resp_code))
            return
        if resp_code not in ['401', '405', '403']:
            return result, resp_header
        oauth = urljoin(BASE_URL, '/oauth/token')
        opost = {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'redirect_uri': REDIRECT_URI, 'grant_type': 'refresh_token', 'refresh_token': control.setting('trakt.refresh')}
        result = client.request(oauth, post=json.dumps(opost), headers=headers)
        result = client_utils.json_loads_as_str(result)
        token, refresh = result['access_token'], result['refresh_token']
        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)
        headers['Authorization'] = 'Bearer %s' % token
        result = client.request(url, post=post, headers=headers, output='extended', error=True)
        result = client_utils.byteify(result)
        return result[0], result[2]
    except:
        pass


def __getTrakt(url, post=None):
    # ---------------------------------------------------------------------
    # FIX (Trakt lists missing): the original implementation returned a bare
    # ``None`` on any server / rate-limit / transport error.  Every caller in
    # this module (e.g. ``getTraktAsJson``) immediately unpacks the result
    # with ``r, res_headers = __getTrakt(url)`` which raises a
    # ``TypeError: cannot unpack non-iterable NoneType object`` the moment
    # Trakt hiccups.  That exception is then swallowed by the caller's own
    # blanket ``try/except`` and the user just sees an *empty* directory –
    # i.e. the "block" symptom where lists silently fail to load.
    #
    # We now ALWAYS return a 2-tuple ``(body_or_None, headers_dict)`` so
    # tuple-unpacking never blows up.  Transient 5xx / 429 are logged only
    # (no more spammy "Trakt Error 502" pop-up that previously discouraged
    # the caller from retrying).  A single short retry with the server's
    # ``Retry-After`` value is attempted on 429 before giving up.
    # ---------------------------------------------------------------------
    try:
        url = urljoin(BASE_URL, url) if not url.startswith(BASE_URL) else url
        post = json.dumps(post) if post else None
        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': '2'}
        if getTraktCredentialsInfo():
            headers.update({'Authorization': 'Bearer %s' % control.setting('trakt.token')})
        if not post:
            r = requests.get(url, headers=headers, timeout=30)
        else:
            r = requests.post(url, data=post, headers=headers, timeout=30)
        r.encoding = 'utf-8'
        resp_code = str(r.status_code)
        resp_header = r.headers
        result = r.text
        if resp_code in ['423', '500', '502', '503', '504', '520', '521', '522', '524']:
            # Log only - popping a modal for every transient gateway error
            # was both noisy and, combined with the old ``return`` below,
            # caused list views to appear empty.
            log_utils.log('Trakt Error: %s on %s' % (str(resp_code), url))
            return None, resp_header
        elif resp_code in ['429']:
            # Rate-limited.  Trakt sends a ``Retry-After`` header (seconds).
            # Do one polite short wait + retry so large list enumerations
            # (which legitimately hit the API many times) don't terminate
            # prematurely and drop the remaining pages.
            wait = 2
            try:
                wait = max(1, min(10, int(resp_header.get('Retry-After', '2'))))
            except Exception:
                wait = 2
            log_utils.log('Trakt Rate Limit %s - sleeping %ss then retrying %s' % (resp_code, wait, url))
            time.sleep(wait)
            if not post:
                r = requests.get(url, headers=headers, timeout=30)
            else:
                r = requests.post(url, data=post, headers=headers, timeout=30)
            r.encoding = 'utf-8'
            if str(r.status_code) == '200':
                return r.text, r.headers
            return None, r.headers
        elif resp_code in ['404']:
            log_utils.log('Trakt Object Not Found : %s' % str(resp_code))
            return None, resp_header
        if resp_code not in ['401', '405', '403']:
            return result, resp_header
        # 401/403/405 => access token expired, try refreshing once and replay.
        oauth = urljoin(BASE_URL, '/oauth/token')
        opost = {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'redirect_uri': REDIRECT_URI, 'grant_type': 'refresh_token', 'refresh_token': control.setting('trakt.refresh')}
        result = requests.post(oauth, data=json.dumps(opost), headers=headers, timeout=30).json()
        token, refresh = result['access_token'], result['refresh_token']
        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)
        headers['Authorization'] = 'Bearer %s' % token
        if not post:
            r = requests.get(url, headers=headers, timeout=30)
        else:
            r = requests.post(url, data=post, headers=headers, timeout=30)
        r.encoding = 'utf-8'
        return r.text, r.headers
    except Exception as e:
        # Network / DNS / SSL failure: still return a well-formed tuple so
        # that downstream ``r, res_headers = __getTrakt(...)`` never explodes.
        log_utils.log('Trakt request failed for %s : %s' % (url, e))
        return None, {}


def _released_key(item):
    if 'released' in item:
        return item['released'] or '0'
    elif 'first_aired' in item:
        return item['first_aired'] or '0'
    else:
        return '0'


def sort_list(sort_key, sort_direction, list_data):
    reverse = False if sort_direction == 'asc' else True
    if sort_key == 'rank':
        return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
    elif sort_key == 'added':
        return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
    elif sort_key == 'title':
        return sorted(list_data, key=lambda x: x[x['type']].get('title'), reverse=reverse)
    elif sort_key == 'released':
        return sorted(list_data, key=lambda x: _released_key(x[x['type']]), reverse=reverse)
    elif sort_key == 'runtime':
        return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
    elif sort_key == 'popularity':
        return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
    elif sort_key == 'percentage':
        return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
    elif sort_key == 'votes':
        return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
    else:
        return list_data


def getTraktAsJson(url, post=None):
    try:
        r, res_headers = __getTrakt(url, post)
        # ``__getTrakt`` may now legitimately return ``(None, headers)`` on
        # 404/5xx; guard the JSON decode so callers get ``None`` rather than
        # a silently-swallowed exception (which previously looked to users
        # like "Trakt isn't returning all my lists").
        if not r:
            return None
        r = client_utils.json_loads_as_str(r)
        if 'X-Sort-By' in res_headers and 'X-Sort-How' in res_headers:
            r = sort_list(res_headers['X-Sort-By'], res_headers['X-Sort-How'], r)
        return r
    except:
        pass


def getTraktAsJsonPaged(url, page_size=1000):
    """
    Fetch a Trakt endpoint that supports pagination and return *all* results
    concatenated, following every page reported by the ``X-Pagination-Page-Count``
    response header.

    WHY THIS FUNCTION EXISTS
    ------------------------
    Trakt paginates almost every "list" endpoint (``/users/me/lists``,
    ``/users/likes/lists``, ``/users/me/watchlist/*``, ``/users/me/history/*``
    etc.).  The maximum allowed ``limit`` per page is **1000** – anything
    larger is either clamped or rejected.  Without walking the pages you
    only ever see the first chunk, which is exactly the user-visible bug
    ("Trakt doesn't get all its lists – some kind of block").

    The helper:
      * forces a sane ``limit`` (default 1000, Trakt's documented maximum),
      * starts at ``page=1`` and increments until
        ``X-Pagination-Page-Count`` is reached (or the server stops
        returning items),
      * merges every page's JSON array into one flat list,
      * preserves Trakt's server-side sort when only a single page is
        returned (so behaviour is unchanged for small accounts),
      * hard-caps at 50 pages (50 000 items) as a safety belt in case a
        buggy server sends absurd header values.
    """
    try:
        # Build the URL with explicit limit/page.  We respect any query
        # string the caller already provided so things like
        # ``?extended=full`` or ``?type=list`` survive untouched.
        split = url.split('?', 1)
        base = split[0]
        existing = dict()
        if len(split) == 2 and split[1]:
            for kv in split[1].split('&'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    existing[k] = v
        # Remove the useless "limit=1000000" value (or any out-of-range
        # limit) that the legacy URL builders use; Trakt clamps these and
        # the clamp varies per endpoint, so we replace with the documented
        # maximum of 1000.
        try:
            limit = int(existing.get('limit', str(page_size)))
            if limit <= 0 or limit > 1000:
                limit = page_size
        except Exception:
            limit = page_size
        existing['limit'] = str(limit)

        merged = []
        current_page = 1
        max_pages = 50  # safety belt, see docstring
        while current_page <= max_pages:
            existing['page'] = str(current_page)
            qs = '&'.join('%s=%s' % (k, v) for k, v in existing.items())
            page_url = '%s?%s' % (base, qs)

            r, res_headers = __getTrakt(page_url, None)
            if not r:
                # Transport/5xx error on this page: stop but return what we
                # already have rather than dropping the whole enumeration.
                break
            try:
                data = client_utils.json_loads_as_str(r)
            except Exception:
                break
            if not isinstance(data, list):
                # Unexpected payload (e.g. an error dict); bail.
                return data
            merged.extend(data)

            # Determine total pages from Trakt's response headers.  If the
            # endpoint doesn't paginate (``/users/me/lists`` for example,
            # which is non-paginated on most accounts) the header will be
            # missing and we stop after the first page – exactly the old
            # behaviour.
            try:
                total_pages = int(res_headers.get('X-Pagination-Page-Count', '1'))
            except Exception:
                total_pages = 1
            if current_page >= total_pages:
                break
            if len(data) < limit:
                # Server returned fewer items than we asked for => we've
                # hit the end regardless of what the header claims.
                break
            current_page += 1

        # Honour Trakt's sort hints only when the server returned a single
        # page; for multi-page merges the per-page order is already
        # consistent and re-sorting would discard the natural order of
        # "most recently liked first" etc.
        if current_page == 1 and res_headers and 'X-Sort-By' in res_headers and 'X-Sort-How' in res_headers:
            merged = sort_list(res_headers['X-Sort-By'], res_headers['X-Sort-How'], merged)
        return merged
    except Exception as e:
        log_utils.log('getTraktAsJsonPaged failed for %s : %s' % (url, e))
        return []


def authTrakt():
    try:
        if getTraktCredentialsInfo() == True:
            if control.yesnoDialog('An account already exists.' + '[CR]' + 'Do you want to reset?', heading='Trakt'):
                control.setSetting(id='trakt.user', value='')
                control.setSetting(id='trakt.authed', value='')
                control.setSetting(id='trakt.token', value='')
                control.setSetting(id='trakt.refresh', value='')
            raise Exception()
        result = getTraktAsJson('/oauth/device/code', {'client_id': V2_API_KEY})
        verification_url = ensure_text('1) Visit : [COLOR skyblue]%s[/COLOR]' % result['verification_url'])
        user_code = ensure_text('2) When prompted enter : [COLOR skyblue]%s[/COLOR]' % result['user_code'])
        expires_in = int(result['expires_in'])
        device_code = result['device_code']
        interval = result['interval']
        progressDialog = control.progressDialog
        progressDialog.create('Trakt')
        for i in range(0, expires_in):
            try:
                percent = int(100 * float(i) / int(expires_in))
                progressDialog.update(max(1, percent), verification_url + '[CR]' + user_code)
                if progressDialog.iscanceled():
                    break
                time.sleep(1)
                if not float(i) % interval == 0:
                    raise Exception()
                r = getTraktAsJson('/oauth/device/token', {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'code': device_code})
                if 'access_token' in r:
                    break
            except:
                pass
        try:
            progressDialog.close()
        except:
            pass
        token, refresh = r['access_token'], r['refresh_token']
        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2, 'Authorization': 'Bearer %s' % token}
        result = client.request(urljoin(BASE_URL, '/users/me'), headers=headers)
        result = client_utils.json_loads_as_str(result)
        user = result['username']
        authed = '' if user == '' else str('yes')
        control.setSetting(id='trakt.user', value=user)
        control.setSetting(id='trakt.authed', value=authed)
        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)
        raise Exception()
    except:
        control.openSettings(query='2.3')


def getTraktIndicatorsInfo():
    indicators = control.setting('indicators') if getTraktCredentialsInfo() == False else control.setting('indicators.alt')
    indicators = True if indicators == '1' else False
    return indicators


def getTraktAddonMovieInfo():
    try:
        scrobble = control.addon('script.trakt').getSetting('scrobble_movie')
    except:
        scrobble = ''
    try:
        ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
    except:
        ExcludeHTTP = ''
    try:
        authorization = control.addon('script.trakt').getSetting('authorization')
    except:
        authorization = ''
    if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '':
        return True
    else:
        return False


def getTraktAddonEpisodeInfo():
    try:
        scrobble = control.addon('script.trakt').getSetting('scrobble_episode')
    except:
        scrobble = ''
    try:
        ExcludeHTTP = control.addon('script.trakt').getSetting('ExcludeHTTP')
    except:
        ExcludeHTTP = ''
    try:
        authorization = control.addon('script.trakt').getSetting('authorization')
    except:
        authorization = ''
    if scrobble == 'true' and ExcludeHTTP == 'false' and not authorization == '':
        return True
    else:
        return False


def slug(name):
    name = name.strip()
    name = name.lower()
    name = re.sub(r'[^a-z0-9_]', '-', name)
    name = re.sub(r'--+', '-', name)
    if name.endswith('-'):
        name = name.rstrip('-')
    return name


def manager(name, imdb, tmdb, content):
    try:
        post = {"movies": [{"ids": {"imdb": imdb}}]} if content == 'movie' else {"shows": [{"ids": {"tmdb": tmdb}}]}
        items = [('Add to [B]Collection[/B]', '/sync/collection')]
        items += [('Remove from [B]Collection[/B]', '/sync/collection/remove')]
        items += [('Add to [B]Watchlist[/B]', '/sync/watchlist')]
        items += [('Remove from [B]Watchlist[/B]', '/sync/watchlist/remove')]
        items += [('Add to [B]new List[/B]', '/users/me/lists/%s/items')]
        result = getTraktAsJson('/users/me/lists')
        lists = [(i['name'], i['ids']['slug']) for i in result]
        lists = [lists[i//2] for i in range(len(lists)*2)]
        for i in range(0, len(lists), 2):
            lists[i] = ((ensure_str('Add to [B]%s[/B]' % lists[i][0])), '/users/me/lists/%s/items' % lists[i][1])
        for i in range(1, len(lists), 2):
            lists[i] = ((ensure_str('Remove from [B]%s[/B]' % lists[i][0])), '/users/me/lists/%s/items/remove' % lists[i][1])
        items += lists
        select = control.selectDialog([i[0] for i in items], 'Trakt Manager')
        if select == -1:
            return
        elif select == 4:
            t = 'Add to [B]new List[/B]'
            k = control.keyboard('', t) ; k.doModal()
            new = k.getText() if k.isConfirmed() else None
            if (new == None or new == ''):
                return
            result = __getTrakt('/users/me/lists', post={"name": new, "privacy": "private"})[0]
            try:
                slug = client_utils.json_loads_as_str(result)['ids']['slug']
            except:
                return control.infoDialog('Trakt Manager', heading=str(name), sound=True, icon='ERROR')
            result = __getTrakt(items[select][1] % slug, post=post)[0]
        else:
            result = __getTrakt(items[select][1], post=post)[0]
        icon = control.infoLabel('ListItem.Icon') if not result == None else 'ERROR'
        control.infoDialog('Trakt Manager', heading=str(name), sound=True, icon=icon)
    except:
        return


def getActivity():
    try:
        i = getTraktAsJson('/sync/last_activities')
        activity = []
        activity.append(i['movies']['collected_at'])
        activity.append(i['episodes']['collected_at'])
        activity.append(i['movies']['watchlisted_at'])
        activity.append(i['shows']['watchlisted_at'])
        activity.append(i['seasons']['watchlisted_at'])
        activity.append(i['episodes']['watchlisted_at'])
        activity.append(i['lists']['updated_at'])
        activity.append(i['lists']['liked_at'])
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        activity = sorted(activity, key=int)[-1]
        return activity
    except:
        pass


def getWatchedActivity():
    try:
        i = getTraktAsJson('/sync/last_activities')
        activity = []
        activity.append(i['movies']['watched_at'])
        activity.append(i['episodes']['watched_at'])
        activity = [int(cleandate.iso_2_utc(i)) for i in activity]
        activity = sorted(activity, key=int)[-1]
        return activity
    except:
        pass


def syncMovies(user):
    try:
        if getTraktCredentialsInfo() == False:
            return
        indicators = getTraktAsJson('/users/me/watched/movies')
        indicators = [i['movie']['ids'] for i in indicators]
        indicators = [str(i['imdb']) for i in indicators if 'imdb' in i]
        return indicators
    except:
        pass


def cachesyncMovies(timeout=0):
    indicators = cache.get(syncMovies, timeout, control.setting('trakt.user').strip())
    return indicators


def timeoutsyncMovies():
    timeout = cache.timeout(syncMovies, control.setting('trakt.user').strip())
    return timeout


def syncTVShows(user):
    try:
        if getTraktCredentialsInfo() == False:
            return
        indicators = getTraktAsJson('/users/me/watched/shows?extended=full')
        indicators = [(i['show']['ids']['tmdb'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], [])) for i in indicators]
        indicators = [(str(i[0]), int(i[1]), i[2]) for i in indicators]
        return indicators
    except:
        pass


def cachesyncTVShows(timeout=0):
    indicators = cache.get(syncTVShows, timeout, control.setting('trakt.user').strip())
    return indicators


def timeoutsyncTVShows():
    timeout = cache.timeout(syncTVShows, control.setting('trakt.user').strip())
    if not timeout:
        timeout = 0
    return timeout


def syncSeason(imdb):
    try:
        if getTraktCredentialsInfo() == False:
            return
        indicators = getTraktAsJson('/shows/%s/progress/watched?specials=false&hidden=false' % imdb)
        indicators = indicators['seasons']
        indicators = [(i['number'], [x['completed'] for x in i['episodes']]) for i in indicators]
        indicators = ['%01d' % int(i[0]) for i in indicators if not False in i[1]]
        return indicators
    except:
        pass


def markMovieAsWatched(imdb):
    if not imdb.startswith('tt'):
        imdb = 'tt' + imdb
    return __getTrakt('/sync/history', {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markMovieAsNotWatched(imdb):
    if not imdb.startswith('tt'):
        imdb = 'tt' + imdb
    return __getTrakt('/sync/history/remove', {"movies": [{"ids": {"imdb": imdb}}]})[0]


def markTVShowAsWatched(imdb):
    return __getTrakt('/sync/history', {"shows": [{"ids": {"imdb": imdb}}]})[0]


def markTVShowAsNotWatched(imdb):
    return __getTrakt('/sync/history/remove', {"shows": [{"ids": {"imdb": imdb}}]})[0]


def markEpisodeAsWatched(imdb, season, episode):
    season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
    return __getTrakt('/sync/history', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"imdb": imdb}}]})[0]


def markEpisodeAsNotWatched(imdb, season, episode):
    season, episode = int('%01d' % int(season)), int('%01d' % int(episode))
    return __getTrakt('/sync/history/remove', {"shows": [{"seasons": [{"episodes": [{"number": episode}], "number": season}], "ids": {"imdb": imdb}}]})[0]


def getMovieTranslation(id, lang, full=False):
    url = '/movies/%s/translations/%s' % (id, lang)
    try:
        item = getTraktAsJson(url)[0]
        return item if full else item.get('title')
    except:
        pass


def getTVShowTranslation(id, lang, season='', episode='', full=False):
    if season and episode:
        url = '/shows/%s/seasons/%s/episodes/%s/translations/%s' % (id, season, episode, lang)
    else:
        url = '/shows/%s/translations/%s' % (id, lang)
    try:
        item = getTraktAsJson(url)[0]
        return item if full else item.get('title')
    except:
        pass


def getMovieAliases(id):
    try:
        return getTraktAsJson('/movies/%s/aliases' % id)
    except:
        return []


def getTVShowAliases(id):
    try:
        return getTraktAsJson('/shows/%s/aliases' % id)
    except:
        return []


def getMovieSummary(id, full=False):
    try:
        url = '/movies/%s' % id
        if full:
            url += '?extended=full'
        return getTraktAsJson(url)
    except:
        return


def getTVShowSummary(id, full=False):
    try:
        url = '/shows/%s' % id
        if full:
            url += '?extended=full'
        return getTraktAsJson(url)
    except:
        return


def getSeasonsSummary(id, full=False, episodes=False):  #Uses imdb_id, full or episodes but not both.
    try:
        url = '/shows/%s/seasons' % id
        if full:
            url += '?extended=full'
        if episodes:
            url += '?extended=episodes'
        return getTraktAsJson(url)
    except:
        return


def getEpisodeSummary(id, season, episode='', full=False):
    try:
        if not episode:
            url = '/shows/%s/seasons/%s' % (id, season)
            #url += '?translations=en'
        else:
            url = '/shows/%s/seasons/%s/episodes/%s' % (id, season, episode)
        if full:
            url += '?extended=full'
        return getTraktAsJson(url)
    except:
        return


#/shows/game-of-thrones/seasons/1/people
#/shows/game-of-thrones/seasons/1/people?extended=guest_stars

#/shows/game-of-thrones/seasons/1/episodes/1/people
#/shows/game-of-thrones/seasons/1/episodes/1/people?extended=guest_stars


def getPeople(id, content_type, full=False): #Uses imdb_id
    try:
        url = '/%s/%s/people' % (content_type, id)
        if full:
            url += '?extended=full'
        return getTraktAsJson(url)
    except:
        return


def getStudio(id, content_type): #Uses imdb_id
    try:
        url = '/%s/%s/studios' % (content_type, id)
        return getTraktAsJson(url)
    except:
        return


def getGenre(content, type, type_id):
    try:
        r = getTraktAsJson('/search/%s/%s?type=%s&extended=full' % (type, type_id, content))
        return r[0].get(content, {}).get('genres', [])
    except:
        return []


def SearchMovie(title, year='', full=False):
    try:
        url = '/search/movie?query=%s' % quote_plus(title)
        if year:
            url += '&year=%s' % year
        if full:
            url += '&extended=full'
        return getTraktAsJson(url)
    except:
        return


def SearchTVShow(title, year='', full=False):
    try:
        url = '/search/show?query=%s' % quote_plus(title)
        if year:
            url += '&year=%s' % year
        if full:
            url += '&extended=full'
        return getTraktAsJson(url)
    except:
        return


def SearchEpisode(title, season, episode, full=False):
    try:
        url = '/search/%s/seasons/%s/episodes/%s' % (title, season, episode)
        if full:
            url += '&extended=full'
        return getTraktAsJson(url)
    except:
        return


def SearchAll(title, year='', full=False):
    try:
        return SearchMovie(title, year, full) + SearchTVShow(title, year, full)
    except:
        return


