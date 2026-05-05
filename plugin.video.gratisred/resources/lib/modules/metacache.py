# -*- coding: utf-8 -*-

import time
import six

from resources.lib.modules import control
#from resources.lib.modules import log_utils

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database


def fetch(items, lang='en'):
    try:
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        check = dbcur.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='meta';").fetchone()
        if not check:
            return items
        t2 = int(time.time())
        for i in range(0, len(items)):
            try:
                dbcur.execute("SELECT * FROM meta WHERE (imdb = '%s' and lang = '%s' and not imdb = '0') or (tmdb = '%s' and lang = '%s' and not tmdb = '0')" % (items[i]['imdb'], lang, items[i]['tmdb'], lang))
                match = dbcur.fetchone()
                if match:
                    t1 = int(match[5])
                    update = (abs(t2 - t1) / 3600) >= 720
                    if update:
                        continue
                    item = eval(six.ensure_str(match[4]))
                    item = dict((k,v) for k, v in six.iteritems(item) if not v == '0')
                    items[i].update(item)
                    items[i].update({'metacache': True})
            except:
                pass
        return items
    except:
        #log_utils.log('fetch', 1)
        return items


def insert(meta):
    try:
        control.makeFile(control.dataPath)
        dbcon = database.connect(control.metacacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("CREATE TABLE IF NOT EXISTS meta (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""lang TEXT, ""item TEXT, ""time TEXT, ""UNIQUE(imdb, tmdb, tvdb, lang)"");")
        t = int(time.time())
        for m in meta:
            try:
                if not "lang" in m:
                    m["lang"] = 'en'
                i = repr(m['item'])
                try:
                    dbcur.execute("DELETE * FROM meta WHERE (imdb = '%s' and lang = '%s' and not imdb = '0') or (tvdb = '%s' and lang = '%s' and not tvdb = '0' or (tmdb = '%s' and lang = '%s' and not tmdb = '0'))" % (m['imdb'], m['lang'], m['tvdb'], m['lang'], m['tmdb'], m['lang']))
                except:
                    pass
                dbcur.execute("INSERT OR REPLACE INTO meta Values (?, ?, ?, ?, ?, ?)", (m['imdb'], m['tmdb'], m['tvdb'], m['lang'], i, t))
            except:
                pass
        dbcon.commit()
    except:
        #log_utils.log('insert', 1)
        pass


