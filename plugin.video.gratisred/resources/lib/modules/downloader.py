# -*- coding: utf-8 -*-

import re
import os
import sys
import inspect

import simplejson as json
from kodi_six import xbmc, xbmcgui, xbmcvfs
from six.moves import urllib_parse, urllib_request


def download(name, image, url):
    if url == None:
        return
    from resources.lib.modules import cleantitle
    from resources.lib.modules import control
    try:
        headers = dict(urllib_parse.parse_qsl(url.rsplit('|', 1)[1]))
    except:
        headers = dict('')
    url = url.split('|')[0]
    content = re.compile(r'(.+?)\sS(\d*)E\d*$').findall(name)
    try:
        transname = name.translate(None, r'\/:*?"<>|').strip('.')
    except:
        transname = name.translate(str.maketrans('', '', r'\/:*?"<>|')).strip('.')
    transname = cleantitle.normalize(transname)
    levels = ['../../../..', '../../..', '../..', '..']
    if len(content) == 0:
        dest = control.setting('movie.download.path')
        dest = control.transPath(dest)
        for level in levels:
            try:
                control.makeFile(os.path.abspath(os.path.join(dest, level)))
            except:
                pass
        control.makeFile(dest)
        dest = os.path.join(dest, transname)
        control.makeFile(dest)
    else:
        dest = control.setting('tv.download.path')
        dest = control.transPath(dest)
        for level in levels:
            try:
                control.makeFile(os.path.abspath(os.path.join(dest, level)))
            except:
                pass
        control.makeFile(dest)
        try:
            transtvshowtitle = content[0][0].translate(None, r'\/:*?"<>|').strip('.')
        except:
            transtvshowtitle = content[0][0].translate(str.maketrans('', '', r'\/:*?"<>|')).strip('.')
        dest = os.path.join(dest, transtvshowtitle)
        control.makeFile(dest)
        dest = os.path.join(dest, 'Season %01d' % int(content[0][1]))
        control.makeFile(dest)
    ext = os.path.splitext(urllib_parse.urlparse(url).path)[1][1:]
    if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']:
        ext = 'mp4'
    dest = os.path.join(dest, transname + '.' + ext)
    sysheaders = urllib_parse.quote_plus(json.dumps(headers))
    sysurl = urllib_parse.quote_plus(url)
    systitle = urllib_parse.quote_plus(name)
    sysimage = urllib_parse.quote_plus(image)
    sysdest = urllib_parse.quote_plus(dest)
    script = inspect.getfile(inspect.currentframe())
    cmd = 'RunScript(%s, %s, %s, %s, %s, %s)' % (script, sysurl, sysdest, systitle, sysimage, sysheaders)
    xbmc.executebuiltin(cmd)


def getResponse(url, headers, size):
    try:
        if size > 0:
            size = int(size)
            headers['Range'] = 'bytes=%d-' % size
        req = urllib_request.Request(url, headers=headers)
        resp = urllib_request.urlopen(req, timeout=30)
        return resp
    except:
        return None


def done(title, dest, downloaded):
    playing = xbmc.Player().isPlaying()
    text = xbmcgui.Window(10000).getProperty('GEN-DOWNLOADED')
    if len(text) > 0:
        text += '[CR]'
    if downloaded:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR forestgreen]Download Completed[/COLOR]')
    else:
        text += '%s : %s' % (dest.rsplit(os.sep)[-1], '[COLOR red]Download Failed[/COLOR]')
    xbmcgui.Window(10000).setProperty('GEN-DOWNLOADED', text)
    if (not downloaded) or (not playing): 
        xbmcgui.Dialog().ok(title, text)
        xbmcgui.Window(10000).clearProperty('GEN-DOWNLOADED')


def doDownload(url, dest, title, image, headers):
    headers = json.loads(urllib_parse.unquote_plus(headers))
    url = urllib_parse.unquote_plus(url)
    title = urllib_parse.unquote_plus(title)
    image = urllib_parse.unquote_plus(image)
    dest = urllib_parse.unquote_plus(dest)
    file = dest.rsplit(os.sep, 1)[-1]
    resp = getResponse(url, headers, 0)
    if not resp:
        xbmcgui.Dialog().ok(title, dest + '[CR]' + 'Download failed' + '[CR]' + 'No response from server')
        return
    try:
        content = int(resp.headers['Content-Length'])
    except:
        content = 0
    try:
        resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
    except:
        resumable = False
    if resumable:
        print("Download is resumable")
    if content < 1:
        xbmcgui.Dialog().ok(title, file + '[CR]' + 'Unknown filesize' + '[CR]' + 'Unable to download')
        return
    size = 1024 * 1024
    mb = content / (1024 * 1024)
    if content < size:
        size = content
    total = 0
    notify = 0
    errors = 0
    count = 0
    resume = 0
    sleep = 0
    if not xbmcgui.Dialog().yesno(title + ' - Confirm Download', file + '[CR]' + 'Complete file is %dMB' % mb + '[CR]' + 'Continue with download?'):
        return
    print('Download File Size : %dMB %s ' % (mb, dest))
    f = xbmcvfs.File(dest, 'w')
    chunk = None
    chunks = []
    while True:
        downloaded = total
        for c in chunks:
            downloaded += len(c)
        percent = min(100 * downloaded / content, 100)
        if percent >= notify:
            xbmcgui.Dialog().notification('Download Progress: ' + str(int(percent)) + '% - ' + title, dest, image, 5000, False)
            print('Download percent : %s %s %dMB downloaded : %sMB File Size : %sMB' % (str(percent)+'%', dest, mb, downloaded / 1000000, content / 1000000))
            notify += 10
        chunk = None
        error = False
        try:
            chunk = resp.read(size)
            if not chunk:
                if percent < 99:
                    error = True
                else:
                    while len(chunks) > 0:
                        c = chunks.pop(0)
                        f.write(c)
                        del c
                    f.close()
                    print('%s download complete' % (dest))
                    return done(title, dest, True)
        except Exception as e:
            print(str(e))
            error = True
            sleep = 10
            errno = 0
            if hasattr(e, 'errno'):
                errno = e.errno
            if errno == 10035: #'A non-blocking socket operation could not be completed immediately'
                pass
            if errno == 10054: #'An existing connection was forcibly closed by the remote host'
                errors = 10 #'force resume'
                sleep = 30
            if errno == 11001: #'getaddrinfo failed'
                errors = 10 #'force resume'
                sleep = 30
        if chunk:
            errors = 0
            chunks.append(chunk)
            if len(chunks) > 5:
                c = chunks.pop(0)
                f.write(c)
                total += len(c)
                del c
        if error:
            errors += 1
            count += 1
            print('%d Error(s) whilst downloading %s' % (count, dest))
            xbmc.sleep(sleep*1000)
        if (resumable and errors > 0) or errors >= 10:
            if (not resumable and resume >= 50) or resume >= 500:
                print('%s download canceled - too many error whilst downloading' % (dest))
                return done(title, dest, False)
            resume += 1
            errors = 0
            if resumable:
                chunks = []
                print('Download resumed (%d) %s' % (resume, dest))
                resp = getResponse(url, headers, total)
            else:
                pass


if __name__ == '__main__':
    if 'downloader.py' in sys.argv[0]:
        doDownload(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])


