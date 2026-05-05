# -*- coding: utf-8 -*-
#
# trakt_cache.py - short-TTL Trakt-only cache + helpers
# -----------------------------------------------------
# WHY THIS MODULE EXISTS
# ----------------------
# The generic ``modules.cache`` stores *every* cached payload (TMDb art,
# meta, provider links, Trakt lists) in a single ``cache`` table with
# whatever TTL the caller passes (usually hours, from the add-on's
# "addon.caching_timeout" setting - default 12h).  Two consequences:
#
#   1. The user-lists directory (``userlists_trakt`` / ``userlists_trakt_liked``
#      in indexers/movies.py, tvshows.py and episodes.py) was **not** cached
#      at all - every time the directory opened, we re-walked every page of
#      ``/users/me/lists`` and ``/users/likes/lists``.  With a few hundred
#      liked lists that's >10 paginated Trakt round-trips per click.
#
#   2. Even if we added it to the generic 12h cache, stale Trakt data would
#      hang around far too long - users who just added/renamed a list on
#      trakt.tv wouldn't see the change until the shared cache expired.
#
# So we keep a small dedicated cache in its own ``trakt_cache`` SQLite
# table with a short TTL (default 5 minutes, 2 minutes for rapidly-changing
# history views).  A brand-new "Refresh Trakt Cache" menu item (added to
# the bottom of the My Trakt menu - see navigator.py) drops **just** this
# table, so users can force a manual resync without blowing away the 12h
# TMDb/meta caches.
#
# The cache key is the same md5(function-name + args) scheme the generic
# cache uses - see ``modules.cache._hash_function`` - so switching a call
# site over is a one-line change.

import time
import pickle
import zlib

from resources.lib.modules import cache as _base_cache
from resources.lib.modules import control
from resources.lib.modules import log_utils

try:
    from sqlite3 import dbapi2 as db, OperationalError, Binary
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError, Binary


# Dedicated SQLite table sitting inside the same cache DB file as the
# generic cache (``control.cacheFile``).  Keeping it in the same file
# means we don't add yet another DB handle / file to the user's data
# directory; dropping *our* table never touches any of the other caches.
_TABLE = 'trakt_cache'

# TTL defaults (seconds).  Exposed at module level so future tuning is a
# one-line change.
TTL_LISTS_SEC = 5 * 60      # 5 min - user-lists directory, watchlist, favorites
TTL_HISTORY_SEC = 2 * 60    # 2 min - history changes every time you play something


def _conn():
    control.makeFile(control.dataPath)
    conn = db.connect(control.cacheFile)
    conn.row_factory = _base_cache._dict_factory
    return conn


def _ensure_table(cur):
    cur.execute(
        "CREATE TABLE IF NOT EXISTS %s "
        "(key TEXT PRIMARY KEY, value BINARY, date INTEGER)" % _TABLE
    )


def _get(key):
    try:
        cur = _conn().cursor()
        _ensure_table(cur)
        cur.execute("SELECT * FROM %s WHERE key = ?" % _TABLE, [key])
        return cur.fetchone()
    except OperationalError:
        return None
    except Exception:
        return None


def _put(key, value):
    try:
        cur = _conn().cursor()
        _ensure_table(cur)
        now = int(time.time())
        upd = cur.execute(
            "UPDATE %s SET value=?, date=? WHERE key=?" % _TABLE,
            (value, now, key),
        )
        if upd.rowcount == 0:
            cur.execute(
                "INSERT INTO %s VALUES (?, ?, ?)" % _TABLE, (key, value, now)
            )
        cur.connection.commit()
    except Exception as e:
        log_utils.log('trakt_cache._put failed: %s' % e)


def get(function, ttl_seconds, *args, **kwargs):
    """Drop-in equivalent to ``cache.get`` but with a *seconds* TTL kept in
    our dedicated ``trakt_cache`` table.

    If the cached value is fresh we return it immediately (zero Trakt
    network calls).  If it is stale / missing we call ``function`` and
    store the fresh result.  On Trakt failure (fresh_result is falsy) we
    *return the stale cache anyway* - matches the defensive behaviour of
    ``modules.cache.get`` so a transient 502 doesn't suddenly show an
    empty directory.
    """
    key = _base_cache._hash_function(function, *args, **kwargs)
    row = _get(key)
    if row:
        try:
            age = int(time.time()) - int(row['date'])
            if age < int(ttl_seconds):
                return pickle.loads(zlib.decompress(row['value']))
        except Exception:
            pass

    try:
        fresh = function(*args, **kwargs)
    except Exception as e:
        log_utils.log('trakt_cache.get function call failed: %s' % e)
        fresh = None

    if not fresh:
        # Return the stale cache if we have one - better than an empty list
        if row:
            try:
                return pickle.loads(zlib.decompress(row['value']))
            except Exception:
                return None
        return fresh

    try:
        _put(key, Binary(zlib.compress(pickle.dumps(fresh))))
    except Exception as e:
        log_utils.log('trakt_cache.get: could not store cache: %s' % e)
    return fresh


def clear():
    """Wipe *only* the Trakt short-TTL cache table.  Bound to the new
    "Refresh Trakt Cache" menu item so users can manually force a resync
    without nuking the generic/TMDb/meta caches."""
    try:
        cur = _conn().cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % _TABLE)
        try:
            cur.execute("VACUUM")
        except Exception:
            pass
        cur.connection.commit()
        return True
    except Exception as e:
        log_utils.log('trakt_cache.clear failed: %s' % e)
        return False
