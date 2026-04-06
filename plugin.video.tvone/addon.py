# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 RACC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import sys
from xbmcgui import ListItem
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from routing import Plugin

import os
import time
from socket import gethostbyname
from future.moves.urllib.parse import urlencode, urlparse
from requests.exceptions import RequestException
from resources.lib.uktvnow import UKTVNow
from resources.lib.spfire import UKTVNow as SPFire

try:
    from xbmcvfs import translatePath
except ImportError:
    from kodi_six.xbmc import translatePath

addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo("name")
USER_DATA_DIR = translatePath(addon.getAddonInfo("profile"))
data_time = int(addon.getSetting("data_time") or "0")
cache_time = int(addon.getSetting("cache_time") or "0")
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[{0}] {1}".format(plugin.name, msg), level=level)


def xbmc_curl_encode(url):
    return "{0}|{1}".format(url[0], urlencode(url[1]))


def resolve_stream_host(stream):
    _parsed = urlparse(stream[0])
    _host = _parsed.netloc.split(":")
    _host[0] = gethostbyname(_host[0])
    _resolved = _parsed._replace(netloc=":".join(_host)).geturl()
    stream[1]["!Host"] = _parsed.netloc
    return (_resolved, stream[1])


TV = UKTVNow(USER_DATA_DIR)
current_time = int(time.time())
if current_time - data_time > cache_time * 60 * 60:
    try:
        TV.update_channels()
        addon.setSetting("data_time", str(current_time))
        log("[{0}] Channels updated".format(current_time))
    except (ValueError, RequestException) as e:
        if data_time == 0:
            """No data"""
            log(e.message)
            dialog = xbmcgui.Dialog()
            dialog.notification(plugin.name, repr(e.message), xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(plugin.handle, False)
        else:
            """Data update failed"""
            log("[{0}] Channels update fail, data age: {1}".format(current_time, data_time))
            log(e.message)

SP = SPFire(USER_DATA_DIR)
current_time = int(time.time())
if current_time - data_time > cache_time * 60 * 60:
    try:
        SP.update_channels()
        addon.setSetting("data_time", str(current_time))
        log("[{0}] Channels updated".format(current_time))
    except (ValueError, RequestException) as e:
        if data_time == 0:
            """No data"""
            log(e.message)
            dialog = xbmcgui.Dialog()
            dialog.notification(plugin.name, repr(e.message), xbmcgui.NOTIFICATION_ERROR)
            xbmcplugin.endOfDirectory(plugin.handle, False)
        else:
            """Data update failed"""
            log("[{0}] Channels update fail, data age: {1}".format(current_time, data_time))
            log(e.message)


@plugin.route("/")
def root():
    list_items = []
    for cat in SP.get_categories():
        li = ListItem("F " + cat.cat_name, offscreen=True)
        url = plugin.url_for(list_sp_channels, cat_id=cat.cat_id)
        list_items.append((url, li, True))
    for cat in TV.get_categories():
        li = ListItem(cat.cat_name, offscreen=True)
        url = plugin.url_for(list_channels, cat_id=cat.cat_id)
        list_items.append((url, li, True))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/list_channels/<cat_id>")
def list_channels(cat_id=None):
    list_items = []
    for channel in TV.get_channels_by_category(cat_id):
        title = "{0} - {1}".format(channel.country, channel.channel_name.rstrip(".,-"))
        image = TV.image_url(channel.img)
        li = ListItem(title, offscreen=True)
        li.setProperty("IsPlayable", "true")
        li.setArt({"thumb": image, "icon": image})
        li.setInfo(type="Video", infoLabels={"Title": title, "mediatype": "video"})
        url = plugin.url_for(play, pk_id=channel.pk_id)
        list_items.append((url, li, False))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/list_sp_channels/<cat_id>")
def list_sp_channels(cat_id=None):
    list_items = []
    for channel in SP.get_channels_by_category(cat_id):
        title = "{0} - {1}".format(channel.country, channel.channel_name.rstrip(".,-"))
        image = SP.image_url(channel.img)
        li = ListItem(title, offscreen=True)
        li.setProperty("IsPlayable", "true")
        li.setArt({"thumb": image, "icon": image})
        li.setInfo(type="Video", infoLabels={"Title": title, "mediatype": "video"})
        url = plugin.url_for(play_sp, pk_id=channel.pk_id)
        list_items.append((url, li, False))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/play_sp/<pk_id>/play.pvr")
def play_sp(pk_id):
    channel = SP.get_channel_by_id(pk_id)
    title = "{0} - {1}".format(channel.country, channel.channel_name.rstrip(".,-"))
    image = SP.image_url(channel.img)
    try:
        links = SP.get_channel_links(pk_id)
        if addon.getSetting("autoplay") == "true":
            stream = links[0]
        elif len(links) > 1:
            dialog = xbmcgui.Dialog()
            ret = dialog.select("Choose Stream", [l[0] for l in links])
            stream = links[ret]
        else:
            stream = links[0]
        if "playlist.m3u8" in stream[0]:
            stream_plugin = addon.getSetting("stream_plugin")
            if stream_plugin == "inputstream.adaptive":
                stream[1]["connection"] = "keep-alive"
                li = ListItem(title, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
                if sys.version_info[0] == 2:
                    li.setProperty("inputstreamaddon", "inputstream.adaptive")
                else:
                    li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                li.setProperty("inputstream.adaptive.stream_headers", urlencode(stream[1]))
                li.setProperty("inputstream.adaptive.license_key", "|" + urlencode(stream[1]))
            elif stream_plugin == "ffmpeg":
                stream = resolve_stream_host(stream)
                stream[1]["Connection"] = "keep-alive"
                li = ListItem(title, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
        else:
            li = ListItem(title, path=xbmc_curl_encode(stream))
        li.setArt({"thumb": image, "icon": image})
        xbmcplugin.setResolvedUrl(plugin.handle, True, li)
    except (ValueError, RequestException) as e:
        log(e.message)
        dialog = xbmcgui.Dialog()
        dialog.notification(plugin.name, repr(e.message), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(plugin.handle, False, ListItem())


@plugin.route("/play/<pk_id>/play.pvr")
def play(pk_id):
    channel = TV.get_channel_by_id(pk_id)
    title = "{0} - {1}".format(channel.country, channel.channel_name.rstrip(".,-"))
    image = TV.image_url(channel.img)
    try:
        links = TV.get_channel_links(pk_id)
        if addon.getSetting("autoplay") == "true":
            stream = links[0]
        elif len(links) > 1:
            dialog = xbmcgui.Dialog()
            ret = dialog.select("Choose Stream", [l[0] for l in links])
            stream = links[ret]
        else:
            stream = links[0]
        if "playlist.m3u8" in stream[0]:
            stream_plugin = addon.getSetting("stream_plugin")
            if stream_plugin == "inputstream.adaptive":
                stream[1]["connection"] = "keep-alive"
                li = ListItem(title, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
                if sys.version_info[0] == 2:
                    li.setProperty("inputstreamaddon", "inputstream.adaptive")
                else:
                    li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                li.setProperty("inputstream.adaptive.stream_headers", urlencode(stream[1]))
                li.setProperty("inputstream.adaptive.license_key", "|" + urlencode(stream[1]))
            elif stream_plugin == "ffmpeg":
                stream = resolve_stream_host(stream)
                stream[1]["Connection"] = "keep-alive"
                li = ListItem(title, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
        else:
            li = ListItem(title, path=xbmc_curl_encode(stream))
        li.setArt({"thumb": image, "icon": image})
        xbmcplugin.setResolvedUrl(plugin.handle, True, li)
    except (ValueError, RequestException) as e:
        log(e.message)
        dialog = xbmcgui.Dialog()
        dialog.notification(plugin.name, repr(e.message), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(plugin.handle, False, ListItem())


if __name__ == "__main__":
    plugin.run(sys.argv)
    del TV
