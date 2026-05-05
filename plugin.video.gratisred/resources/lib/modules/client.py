# -*- coding: utf-8 -*-

import re
import sys
import gzip
import random
import time

import requests
import simplejson as json
import six
from six.moves import range as x_range, urllib_parse

from resources.lib.modules import control
from resources.lib.modules import dom_parser
from resources.lib.modules import log_utils

try: # Py2
    from urlparse import urlparse, urljoin
    from urllib import quote, urlencode, quote_plus, addinfourl
    import cookielib
    import urllib2
    from cStringIO import StringIO
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape
    HTTPError = urllib2.HTTPError
except ImportError: # Py3:
    from http import cookiejar as cookielib
    from html import unescape
    import urllib.request as urllib2
    from io import StringIO
    from urllib.parse import urlparse, urljoin, quote, urlencode, quote_plus
    from urllib.response import addinfourl
    from urllib.error import HTTPError
finally:
    urlopen = urllib2.urlopen
    Request = urllib2.Request

if six.PY2:
    _str = str
    str = unicode
    unicode = unicode
    basestring = basestring
    def bytes(b, encoding="ascii"):
        return _str(b)
elif six.PY3:
    bytes = bytes
    str = unicode = basestring = str


#CERT_FILE = control.transPath('special://xbmc/system/certs/cacert.pem')

_COOKIE_HEADER = "Cookie"
_HEADER_RE = re.compile(r"^([\w\d-]+?)=(.*?)$")

UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0'
OldUserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'
MobileUserAgent = 'Mozilla/5.0 (Android 10; Mobile; rv:83.0) Gecko/83.0 Firefox/83.0'

dnt_headers = {
    'User-Agent': UserAgent,
    'Accept': '*/*',
    'Accept-Encoding': 'identity;q=1, *;q=0',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'DNT': '1'
}


def _strip_url(url):
    if url.find('|') == -1:
        return (url, {})
    headers = url.split('|')
    target_url = headers.pop(0)
    out_headers = {}
    for h in headers:
        m = _HEADER_RE.findall(h)
        if not len(m):
            continue
        out_headers[m[0][0]] = urllib_parse.unquote_plus(m[0][1])
    return (target_url, out_headers)


def _url_with_headers(url, headers):
    if not len(headers.keys()):
        return url
    headers_arr = ["%s=%s" % (key, urllib_parse.quote_plus(value)) for key, value in six.iteritems(headers)]
    return "|".join([url] + headers_arr)


def strip_cookie_url(url):
    url, headers = _strip_url(url)
    if _COOKIE_HEADER in headers.keys():
        del headers[_COOKIE_HEADER]
    return _url_with_headers(url, headers)


def _add_request_header(_request, headers):
    try:
        if not headers:
            headers = {}
        if six.PY2:
            scheme = _request.get_type()
            host = _request.get_host()
        else:
            scheme = urllib_parse.urlparse(_request.get_full_url()).scheme
            host = _request.host
        referer = headers.get('Referer') if 'Referer' in headers else '%s://%s/' % (scheme, host)
        _request.add_unredirected_header('Host', host)
        _request.add_unredirected_header('Referer', referer)
        for key in headers:
            _request.add_header(key, headers[key])
    except:
        return


def _get_result(response, limit=None):
    if limit == '0':
        result = response.read(224 * 1024)
    elif limit:
        result = response.read(int(limit) * 1024)
    else:
        result = response.read(5242880)
    try:
        encoding = response.info().getheader('Content-Encoding')
    except:
        encoding = None
    if encoding == 'gzip':
        result = gzip.GzipFile(fileobj=StringIO(result)).read()
        #result = gzip.GzipFile(fileobj=six.BytesIO(result)).read() #ALT Way Saved.
    return result


def _basic_request(url, headers=None, post=None, timeout='10', limit=None):
    try:
        try:
            headers.update(headers)
        except:
            headers = {}
        if post is not None:
            post = post if six.PY2 else post.encode()
        request = Request(url, data=post)
        _add_request_header(request, headers)
        response = urlopen(request, timeout=int(timeout))
        return _get_result(response, limit)
    except:
        return


def request(url, close=True, redirect=True, error=False, verify=True, post=None, headers=None, mobile=False, XHR=False,
            limit=None, referer=None, cookie=None, compression=False, output='', timeout='10', as_bytes=False):
    try:
        url = six.ensure_text(url, errors='ignore')
    except Exception:
        pass
    if isinstance(post, dict):
        post = bytes(urlencode(post), encoding='utf-8')
    elif isinstance(post, str) and six.PY3:
        post = bytes(post, encoding='utf-8')
    try:
        handlers = []
        if output == 'cookie' or output == 'extended' or close is not True:
            cookies = cookielib.LWPCookieJar()
            handlers += [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies)]
            opener = urllib2.build_opener(*handlers)
            urllib2.install_opener(opener)
        try:
            import platform
            is_XBOX = platform.uname()[1] == 'XboxOne'
        except Exception:
            is_XBOX = False
        if not verify and sys.version_info >= (2, 7, 12):
            try:
                import ssl
                ssl_context = ssl._create_unverified_context()
                handlers += [urllib2.HTTPSHandler(context=ssl_context)]
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)
            except Exception:
                pass
        elif verify and ((2, 7, 8) < sys.version_info < (2, 7, 12) or is_XBOX):
            try:
                import ssl
                try:
                    import _ssl
                    CERT_NONE = _ssl.CERT_NONE
                except Exception:
                    CERT_NONE = ssl.CERT_NONE
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = CERT_NONE
                handlers += [urllib2.HTTPSHandler(context=ssl_context)]
                opener = urllib2.build_opener(*handlers)
                urllib2.install_opener(opener)
            except Exception:
                pass
        try:
            headers.update(headers)
        except Exception:
            headers = {}
        if 'User-Agent' in headers:
            pass
        elif mobile is not True:
            headers['User-Agent'] = UserAgent
        else:
            headers['User-Agent'] = MobileUserAgent
        if 'Referer' in headers:
            pass
        elif referer is None:
            headers['Referer'] = '%s://%s/' % (urlparse(url).scheme, urlparse(url).netloc)
        else:
            headers['Referer'] = referer
        if not 'Accept-Language' in headers:
            headers['Accept-Language'] = 'en-US,en'
        if 'X-Requested-With' in headers:
            pass
        elif XHR is True:
            headers['X-Requested-With'] = 'XMLHttpRequest'
        if 'Cookie' in headers:
            pass
        elif cookie is not None:
            headers['Cookie'] = cookie
        if 'Accept-Encoding' in headers:
            pass
        elif compression and limit is None:
            headers['Accept-Encoding'] = 'gzip'
        if redirect is False:
            class NoRedirectHandler(urllib2.HTTPRedirectHandler):
                def http_error_302(self, reqst, fp, code, msg, head):
                    infourl = addinfourl(fp, head, reqst.get_full_url())
                    infourl.status = code
                    infourl.code = code
                    return infourl
                http_error_300 = http_error_302
                http_error_301 = http_error_302
                http_error_303 = http_error_302
                http_error_307 = http_error_302
            opener = urllib2.build_opener(NoRedirectHandler())
            urllib2.install_opener(opener)
            try:
                del headers['Referer']
            except Exception:
                pass
        req = urllib2.Request(url, data=post, headers=headers)
        try:
            response = urllib2.urlopen(req, timeout=int(timeout))
        except HTTPError as response:
            #log_utils.log('request-HTTPError (%s): %s' % (response.code, url))
            if response.code == 503:
                if 'cf-browser-verification' in response.read(5242880):
                    log_utils.log('client - url with cloudflare: ' + repr(url))
                    #log_utils.log('client - cfScrape Exception', 1)
                elif error is False:
                    return
            elif error is False:
                return
        if output == 'cookie':
            try:
                result = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
            except Exception:
                pass
        elif output == 'response':
            if limit == '0':
                result = (str(response.code), response.read(224 * 1024))
            elif limit is not None:
                result = (str(response.code), response.read(int(limit) * 1024))
            else:
                result = (str(response.code), response.read(5242880))
        elif output == 'chunk':
            try:
                content = int(response.headers['Content-Length'])
            except Exception:
                content = (2049 * 1024)
            if content < (2048 * 1024):
                return
            result = response.read(16 * 1024)
        elif output == 'extended':
            try:
                cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in cookies])
            except Exception:
                pass
            content = response.headers
            result_url = response.geturl()
            result = response.read(5242880)
            if not as_bytes:
                result = six.ensure_text(result, errors='ignore')
            return result, headers, content, cookie, result_url
        elif output == 'geturl':
            result = response.geturl()
        elif output == 'headers':
            content = response.headers
            if close:
                response.close()
            return content
        elif output == 'file_size':
            try:
                content = int(response.headers['Content-Length'])
            except Exception:
                content = '0'
            response.close()
            return content
        elif output == 'json':
            content = json.loads(response.read(5242880))
            response.close()
            return content
        else:
            if limit == '0':
                result = response.read(224 * 1024)
            elif limit is not None:
                if isinstance(limit, int):
                    result = response.read(limit * 1024)
                else:
                    result = response.read(int(limit) * 1024)
            else:
                result = response.read(5242880)
        if close is True:
            response.close()
        if not as_bytes:
            result = six.ensure_text(result, errors='ignore')
        return result
    except Exception as e:
        #log_utils.log('request-Error: (%s) => %s' % (str(e), url))
        #log_utils.log('request', 1)
        return


def _flaresolverr_url():
    """Read FlareSolverr endpoint from addon settings.  Empty -> disabled."""
    try:
        url = (control.setting('flaresolverr.url') or '').strip()
    except Exception:
        url = ''
    return url


def _is_cf_challenge(page):
    """Detect a Cloudflare managed-challenge / IUAM / interstitial response.
    Cloudflare's modern managed-challenge can be returned with status 200,
    403 or 503, so we can't rely on the status code alone - we always
    inspect the `cf-mitigated` / `Server` headers and the body for the
    'Just a moment...' interstitial."""
    try:
        if page is None:
            return False
        srv = (page.headers.get('Server') or '').lower() if hasattr(page, 'headers') else ''
        mit = (page.headers.get('cf-mitigated') or '').lower() if hasattr(page, 'headers') else ''
        body = getattr(page, 'text', '') or ''
        # Strong signal: CF explicitly tells us this is a challenge.
        if mit == 'challenge':
            return True
        # Body-level detection - covers status 200 interstitials and CF-protected
        # sites whose origin server uses non-standard codes.
        head = body[:2000]
        if ('Just a moment' in head or 'cf-chl' in head or
                'challenge-platform' in head or '__cf_chl_' in head):
            return True
        # Fallback: classic 403/503 from a CF-fronted server.
        code = getattr(page, 'status_code', 0)
        if code in (403, 503) and 'cloudflare' in srv:
            return True
        return False
    except Exception:
        return False


class _FsrResponse(object):
    """Minimal duck-typed Response so callers can keep using .text / .status_code / .headers / .url."""
    __slots__ = ('text', 'status_code', 'headers', 'url', 'encoding', 'content', 'cookies', 'user_agent')
    def __init__(self, text, status_code, headers, url, cookies=None, user_agent=None):
        self.text = text or ''
        self.status_code = int(status_code or 0)
        self.headers = headers or {}
        self.url = url or ''
        self.encoding = 'utf-8'
        self.cookies = cookies or []
        self.user_agent = user_agent or ''
        try:
            self.content = self.text.encode('utf-8', 'replace')
        except Exception:
            self.content = b''


# Process-wide cookie cache populated when FlareSolverr solves a CF challenge.
# Key: lowercase host (e.g. 'srstop.link', 'bstsrs.in')
# Val: {'cookie_header': 'name1=v1; name2=v2', 'user_agent': '...', 'expires': epoch_seconds}
# Cloudflare ties cf_clearance to the originating User-Agent, so we must reuse
# FlareSolverr's User-Agent verbatim for cookies to remain valid.
_flare_cookie_cache = {}
# 25 minutes - well below cf_clearance default lifetime, refresh proactively.
_FLARE_CACHE_TTL = 25 * 60


def _host_key(target_url):
    try:
        host = (urllib_parse.urlparse(target_url).hostname or '').lower()
        # Strip leading 'www.' so subdomains share the same clearance cookie.
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def _get_flare_cookies(target_url):
    """Return (cookie_header, user_agent) for `target_url`, or (None, None)."""
    host = _host_key(target_url)
    if not host:
        return None, None
    entry = _flare_cookie_cache.get(host)
    if not entry:
        return None, None
    if entry.get('expires', 0) < time.time():
        _flare_cookie_cache.pop(host, None)
        return None, None
    return entry.get('cookie_header'), entry.get('user_agent')


def _store_flare_cookies(target_url, cookies, user_agent):
    """Save cookies returned by FlareSolverr keyed by host."""
    host = _host_key(target_url)
    if not host or not cookies:
        return
    pairs = []
    for c in cookies:
        try:
            n = c.get('name')
            v = c.get('value', '')
            if n:
                pairs.append('%s=%s' % (n, v))
        except Exception:
            continue
    if not pairs:
        return
    _flare_cookie_cache[host] = {
        'cookie_header': '; '.join(pairs),
        'user_agent': user_agent or UserAgent,
        'expires': time.time() + _FLARE_CACHE_TTL,
    }


def _flaresolverr_request(fsr_url, target_url, post=None, timeout=30):
    """Route a request through a self-hosted FlareSolverr instance.
    Returns a _FsrResponse on success, None on failure."""
    try:
        endpoint = fsr_url.rstrip('/')
        if not endpoint.endswith('/v1'):
            endpoint = endpoint + '/v1'
        body = {
            'cmd': 'request.post' if post else 'request.get',
            'url': target_url,
            'maxTimeout': max(int(timeout) * 1000, 30000),
        }
        if post:
            try:
                body['postData'] = urllib_parse.urlencode(post) if isinstance(post, dict) else str(post)
            except Exception:
                body['postData'] = str(post)
        r = requests.post(endpoint, json=body, timeout=int(timeout) + 10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get('status') != 'ok':
            return None
        sol = data.get('solution') or {}
        cookies = sol.get('cookies') or []
        user_agent = sol.get('userAgent') or ''
        # Persist cf_clearance et al so subsequent requests on the same host
        # bypass the CF challenge directly via plain `requests` - no need to
        # round-trip through FlareSolverr each time (which is slow and would
        # blow past providers.timeout when multiple scrapers run in parallel).
        _store_flare_cookies(target_url, cookies, user_agent)
        return _FsrResponse(
            text=sol.get('response', ''),
            status_code=sol.get('status', 0),
            headers=sol.get('headers', {}) or {},
            url=sol.get('url', target_url),
            cookies=cookies,
            user_agent=user_agent,
        )
    except Exception:
        return None


def scrapePage(url, referer=None, headers=None, post=None, cookie=None, timeout='10'):
    try:
        if not url:
            return
        url =  "https:" + url if url.startswith('//') else url
        # Reuse FlareSolverr-issued cookies (cf_clearance et al) if the host has
        # been solved recently.  Cloudflare ties cf_clearance to the originating
        # User-Agent, so override UA with the one FlareSolverr used.
        flare_cookie, flare_ua = _get_flare_cookies(url)
        with requests.Session() as session:
            if headers:
                session.headers.update(headers)
            if (referer and not 'Referer' in session.headers):
                session.headers.update({'Referer': referer})
            else:
                elements = urllib_parse.urlparse(url)
                base = '%s://%s' % (elements.scheme, (elements.netloc or elements.path))
                session.headers.update({'Referer': base})
            if (cookie and not 'Cookie' in session.headers): # not tested yet, just placed as a idea reminder.
                session.headers.update({'Cookie': cookie})
            if not 'User-Agent' in session.headers:
                session.headers.update({'User-Agent': UserAgent})
            if flare_cookie:
                # Merge with any caller-supplied Cookie header.
                existing = session.headers.get('Cookie') or session.headers.get(_COOKIE_HEADER) or ''
                merged = (existing + '; ' + flare_cookie).strip('; ') if existing else flare_cookie
                session.headers['Cookie'] = merged
                if flare_ua:
                    session.headers['User-Agent'] = flare_ua
            if post:
                page = session.post(url, data=post, timeout=int(timeout))
            else:
                page = session.get(url, timeout=int(timeout))
            ###################################################################
            # Cloudflare auto-bypass via self-hosted FlareSolverr (opt-in).
            # If the response is a CF challenge AND the user has filled in the
            # `flaresolverr.url` setting, retry through FlareSolverr so any
            # CF-protected provider (bstsrs.in, srstop.link, etc) can scrape.
            # The FlareSolverr response cookies are cached per-host so the
            # next request on the same host uses plain `requests` - critical
            # when several scrapers (bstsrs + srstop) run in parallel against
            # the shared providers.timeout.
            if _is_cf_challenge(page):
                fsr = _flaresolverr_url()
                if fsr:
                    fsr_resp = _flaresolverr_request(fsr, url, post=post, timeout=int(timeout))
                    if fsr_resp is not None and fsr_resp.status_code and fsr_resp.status_code < 400:
                        return fsr_resp
            ###################################################################
            page.encoding = 'utf-8'
            #page.raise_for_status()  # Commented out to make trakt progress option work properly again lol
        return page
    except Exception as e:
        #log_utils.log('scrapePage-Error: (%s) => %s' % (str(e), url))
        #log_utils.log('scrapePage', 1)
        return


def url_ok(url): #  Old Code Saved.
    r = scrapePage(url)
    if r.status_code == 200 or r.status_code == 301:
        return True
    else:
        return False


