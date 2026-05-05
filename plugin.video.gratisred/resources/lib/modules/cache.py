# -*- coding: utf-8 -*-

import re
import os
import time
import hashlib

import json
import pickle
import zlib

import six
from kodi_six import xbmc, xbmcvfs, xbmcaddon

from ast import literal_eval as evaluate
import xml.etree.ElementTree as ET

from resources.lib.modules import control
from resources.lib.modules import log_utils

try:
    from sqlite3 import dbapi2 as db, OperationalError, Binary
except ImportError:
    from pysqlite2 import dbapi2 as db, OperationalError, Binary

if six.PY2:
    str = unicode
elif six.PY3:
    str = unicode = basestring = str

cache_table = 'cache'
kodi_version = control.getKodiVersion()


def _generate_md5_OLD(*args): # Old Code
    md5_hash = hashlib.md5()
    [md5_hash.update(six.ensure_binary(arg, errors='replace')) for arg in args]
    return str(md5_hash.hexdigest())

def _generate_md5(*args, **kwargs):
    md5_hash = hashlib.md5()
    [md5_hash.update(str(arg) if six.PY2 else str(arg).encode()) for arg in args]
    md5_hash.update(json.dumps(kwargs) if six.PY2 else json.dumps(kwargs).encode())
    return md5_hash.hexdigest()


def _get_function_name(function_instance):
    return re.sub(r'.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function_instance))


def _hash_function_OLD(function_instance, *args): # Old Code
    return _get_function_name(function_instance) + _generate_md5(args)

def _hash_function(function_instance, *args, **kwargs):
    return _get_function_name(function_instance) + _generate_md5(*args, **kwargs)


def _dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def _get_connection():
    control.makeFile(control.dataPath)
    conn = db.connect(control.cacheFile)
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor():
    conn = _get_connection()
    return conn.cursor()


def _get_connection_meta():
    control.makeFile(control.dataPath)
    conn = db.connect(control.metacacheFile)
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_meta():
    conn = _get_connection_meta()
    return conn.cursor()


def _get_connection_providers():
    control.makeFile(control.dataPath)
    conn = db.connect(control.providercacheFile)
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_providers():
    conn = _get_connection_providers()
    return conn.cursor()


def _get_connection_search():
    control.makeFile(control.dataPath)
    conn = db.connect(control.searchFile)
    conn.row_factory = _dict_factory
    return conn


def _get_connection_cursor_search():
    conn = _get_connection_search()
    return conn.cursor()


def _is_cache_valid(cached_time, cache_timeout):
    now = int(time.time())
    diff = now - cached_time
    return (cache_timeout * 3600) > diff


def _find_cache_version():
    versionFile = os.path.join(control.dataPath, 'cache.v')
    try:
        if six.PY2:
            with open(versionFile, 'rb') as fh:
                oldVersion = fh.read()
        elif six.PY3:
            with open(versionFile, 'r') as fh:
                oldVersion = fh.read()
    except:
        oldVersion = '0'
    try:
        curVersion = control.addon('plugin.video.gratisred').getAddonInfo('version')
        if oldVersion != curVersion:
            if six.PY2:
                with open(versionFile, 'wb') as fh:
                    fh.write(curVersion)
            elif six.PY3:
                with open(versionFile, 'w') as fh:
                    fh.write(curVersion)
            return True
        else:
            return False
    except:
        return False


def get_OLD(function_, duration, *args, **table): # Old Code
    try:
        response = None
        f = repr(function_)
        f = re.sub(r'.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', f)
        a = hashlib.md5()
        for i in args:
            a.update(six.ensure_binary(i, errors='replace'))
        a = str(a.hexdigest())
    except Exception:
        pass
    try:
        table = table['table']
    except Exception:
        table = 'rel_list'
    try:
        control.makeFile(control.dataPath)
        dbcon = db.connect(control.cacheFile)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT * FROM {tn} WHERE func = '{f}' AND args = '{a}'".format(tn=table, f=f, a=a))
        match = dbcur.fetchone()
        try:
            response = evaluate(match[2].encode('utf-8'))
        except AttributeError:
            response = evaluate(match[2])
        t1 = int(match[3])
        t2 = int(time.time())
        update = (abs(t2 - t1) / 3600) >= int(duration)
        if not update:
            return response
    except Exception:
        pass
    try:
        r = function_(*args)
        if (r is None or r == []) and response is not None:
            return response
        elif r is None or r == []:
            return r
    except Exception:
        return
    try:
        r = repr(r)
        t = int(time.time())
        dbcur.execute("CREATE TABLE IF NOT EXISTS {} (""func TEXT, ""args TEXT, ""response TEXT, ""added TEXT, ""UNIQUE(func, args)"");".format(table))
        dbcur.execute("DELETE FROM {0} WHERE func = '{1}' AND args = '{2}'".format(table, f, a))
        dbcur.execute("INSERT INTO {} Values (?, ?, ?, ?)".format(table), (f, a, r, t))
        dbcon.commit()
    except Exception:
        pass
    try:
        return evaluate(r.encode('utf-8'))
    except Exception:
        return evaluate(r)

def get(function, duration, *args, **kwargs):
    # type: (function, int, object) -> object or None
    """
    Gets cached value for provided function with optional arguments, or executes and stores the result
    :param function: Function to be executed
    :param duration: Duration of validity of cache in hours
    :param args: Optional arguments for the provided function
    :param kwargs: Optional keyword arguments for the provided function
    """
    key = _hash_function(function, *args, **kwargs)
    cache_result = cache_get(key)
    if cache_result:
        if _is_cache_valid(cache_result['date'], duration):
            return pickle.loads(zlib.decompress(cache_result['value']))
    fresh_result = function(*args, **kwargs)
    if not fresh_result:
        # If the cache is old, but we didn't get fresh result, return the old cache.
        if cache_result:
            return pickle.loads(zlib.decompress(cache_result['value']))
        return None
    cache_insert(key, Binary(zlib.compress(pickle.dumps(fresh_result))))
    return fresh_result


def cache_get(key):
    try:
        cursor = _get_connection_cursor()
        cursor.execute("SELECT * FROM %s WHERE key = ?" % cache_table, [key])
        return cursor.fetchone()
    except OperationalError:
        return None


def cache_insert_OLD(key, value): # Old Code
    cursor = _get_connection_cursor()
    now = int(time.time())
    cursor.execute("CREATE TABLE IF NOT EXISTS %s (key TEXT, value TEXT, date INTEGER, UNIQUE(key))" % cache_table)
    update_result = cursor.execute("UPDATE %s SET value=?,date=? WHERE key=?" % cache_table, (value, now, key))
    if update_result.rowcount == 0:
        cursor.execute("INSERT INTO %s Values (?, ?, ?)" % cache_table, (key, value, now))
    cursor.connection.commit()

def cache_insert(key, value):
    # type: (str, str) -> None
    cursor = _get_connection_cursor()
    now = int(time.time())
    cursor.execute("CREATE TABLE IF NOT EXISTS %s (key TEXT, value BINARY, date INTEGER, UNIQUE(key))" % cache_table)
    cursor.execute("CREATE UNIQUE INDEX if not exists index_key ON %s (key)" % cache_table)
    update_result = cursor.execute("UPDATE %s SET value=?,date=? WHERE key=?" % cache_table, (value, now, key))
    if update_result.rowcount == 0:
        cursor.execute("INSERT INTO %s Values (?, ?, ?)" % cache_table, (key, value, now))
    cursor.connection.commit()


def remove(function, *args, **kwargs):
    key = _hash_function(function, *args, **kwargs)
    cursor = _get_connection_cursor()
    cursor.execute("DELETE FROM %s WHERE key = ?" % cache_table, [key])
    cursor.connection.commit()


#def timeout(function_, *args): # Old Code
def timeout(function, *args, **kwargs):
    try:
        #key = _hash_function(function_, args) # Old Code
        key = _hash_function(function, *args, **kwargs)
        result = cache_get(key)
        return int(result['date'])
    except Exception:
        return None


def clean_settings():
    current_user_settings = []
    removed_settings = []
    active_settings = []
    def _make_content(dict_object):
        if kodi_version >= 18:
            content = '<settings version="2">'
            for item in dict_object:
                if item['id'] in active_settings:
                    if 'default' in item and 'value' in item:
                        content += '\n    <setting id="%s" default="%s">%s</setting>' % (item['id'], item['default'], item['value'])
                    elif 'default' in item:
                        content += '\n    <setting id="%s" default="%s"></setting>' % (item['id'], item['default'])
                    elif 'value' in item:
                        content += '\n    <setting id="%s">%s</setting>' % (item['id'], item['value'])
                    else:
                        content += '\n    <setting id="%s"></setting>'
                else:
                    removed_settings.append(item)
        else:
            content = '<settings>'
            for item in dict_object:
                if item['id'] in active_settings:
                    if 'value' in item:
                        content += '\n    <setting id="%s" value="%s" />' % (item['id'], item['value'])
                    else:
                        content += '\n    <setting id="%s" value="" />' % item['id']
                else:
                    removed_settings.append(item)
        content += '\n</settings>'
        return content
    try:
        root = ET.parse(control.settingsPath).getroot()
        for item in root.findall('./category/setting'):
            setting_id = item.get('id')
            if setting_id:
                active_settings.append(setting_id)
        root = ET.parse(control.settingsFile).getroot()
        for item in root:
            dict_item = {}
            setting_id = item.get('id')
            setting_default = item.get('default')
            if kodi_version >= 18:
                setting_value = item.text
            else:
                setting_value = item.get('value')
            dict_item['id'] = setting_id
            if setting_value:
                dict_item['value'] = setting_value
            if setting_default:
                dict_item['default'] = setting_default
            current_user_settings.append(dict_item)
        new_content = _make_content(current_user_settings)
        nfo_file = control.openFile(control.settingsFile, 'w')
        nfo_file.write(new_content)
        nfo_file.close()
        control.infoDialog('Clean Settings: %s Old Settings Removed' % (str(len(removed_settings))))
    except:
        log_utils.log('clean_settings', 1)
        control.infoDialog('Clean Settings: Error Cleaning Settings')
        return


def cache_clear():
    try:
        cursor = _get_connection_cursor()
        for t in [cache_table, 'rel_list', 'rel_lib']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_meta():
    try:
        cursor = _get_connection_cursor_meta()
        for t in ['meta']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_providers():
    try:
        cursor = _get_connection_cursor_providers()
        for t in ['rel_src', 'rel_url']:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_search(select):
    try:
        cursor = _get_connection_cursor_search()
        if select == 'all':
            table = ['movies', 'tvshow', 'people', 'keywords', 'companies', 'collections']
        elif not isinstance(select, list):
            table = [select]
        for t in table:
            try:
                cursor.execute("DROP TABLE IF EXISTS %s" % t)
                cursor.execute("VACUUM")
                cursor.commit()
            except:
                pass
    except:
        pass


def cache_clear_all():
    cache_clear()
    cache_clear_meta()
    cache_clear_providers()


def cache_version_check():
    if _find_cache_version():
        cache_clear_all()
        clean_settings()
        control.sleep(1000)
        if control.setting('addon.notifcations') == 'true' and control.setting('addon.enable_notifcations') == 'true':
            control.setSetting('addon.notifcations', 'false')
        control.infoDialog('Version Check - AutoClean: Process Complete', sound=True, icon='INFO')
        control.checkArtwork()
        if control.setting('show.changelog') == 'true':
            control.sleep(3000)
            log_utils.changelog()


