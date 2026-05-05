# -*- coding: utf-8 -*-

import simplejson as json

from resources.lib.modules import control

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database


def addFavorite(meta, content):
    try:
        item = dict()
        meta = json.loads(meta)
        try:
            id = meta['imdb']
        except:
            id = meta['tmdb']
        if 'title' in meta:
            title = item['title'] = meta['title']
        if 'tvshowtitle' in meta:
            title = item['title'] = meta['tvshowtitle']
        if 'year' in meta:
            item['year'] = meta['year']
        if 'poster' in meta:
            item['poster'] = meta['poster']
        if 'fanart' in meta:
            item['fanart'] = meta['fanart']
        if 'imdb' in meta:
            item['imdb'] = meta['imdb']
        if 'tmdb' in meta:
            item['tmdb'] = meta['tmdb']
        if 'tvdb' in meta:
            item['tvdb'] = meta['tvdb']
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.favoritesFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS %s (""id TEXT, ""items TEXT, ""UNIQUE(id)"");" % content)
        dbcur.execute("DELETE FROM %s WHERE id = '%s'" % (content, id))
        dbcur.execute("INSERT INTO %s Values (?, ?)" % content, (id, repr(item)))
        dbcon.commit()
        control.refresh()
        control.infoDialog('Added to MyFavorites', heading=title, icon=item['poster'])
    except:
        return


def deleteFavorite(meta, content):
    try:
        meta = json.loads(meta)
        if 'title' in meta:
            title = meta['title']
        if 'tvshowtitle' in meta:
            title = meta['tvshowtitle']
        if 'poster' in meta:
            poster = meta['poster']
        else:
            poster = control.addonThumb()
        try:
            dbcon = database.connect(control.favoritesFile)
            dbcur = dbcon.cursor()
            try:
                dbcur.execute("DELETE FROM %s WHERE id = '%s'" % (content, meta['imdb']))
            except:
                pass
            try:
                dbcur.execute("DELETE FROM %s WHERE id = '%s'" % (content, meta['tmdb']))
            except:
                pass
            dbcon.commit()
        except:
            pass
        control.refresh()
        control.infoDialog('Removed From MyFavorites', heading=title, icon=poster)
    except:
        return


def getFavorites(content):
    try:
        dbcon = database.connect(control.favoritesFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM %s" % content)
        items = dbcur.fetchall()
        items = [(i[0].encode('utf-8'), eval(i[1].encode('utf-8'))) for i in items]
    except:
        items = []
    return items


