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
from __future__ import unicode_literals, absolute_import

import sys
from xbmcgui import ListItem
from kodi_six import xbmcgui, xbmcaddon, xbmcplugin
from routing import Plugin
import os
from socket import gethostbyname
from future.moves.urllib.parse import urlencode, urlparse
from resources.lib.rstv import RSTV

try:
    from xbmcvfs import translatePath
except ImportError:
    from kodi_six.xbmc import translatePath

addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo("name")
USER_DATA_DIR = translatePath(addon.getAddonInfo("profile"))
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)
TV = RSTV(USER_DATA_DIR)


def xbmc_curl_encode(url):
    return "{0}|{1}".format(url[0], urlencode(url[1]))


def resolve_stream_host(stream):
    _parsed = urlparse(stream[0])
    _host = _parsed.netloc.split(":")
    _host[0] = gethostbyname(_host[0])
    _resolved = _parsed._replace(netloc=":".join(_host)).geturl()
    stream[1]["!Host"] = _parsed.netloc
    return (_resolved, stream[1])


@plugin.route("/")
def root():
    list_items = []
    for item in TV.get_live_categories():
        li = ListItem(item.cat_name)
        image = xbmc_curl_encode(TV.resolve_image(item.cat_image))
        li.setArt({"thumb": image, "icon": image})
        url = plugin.url_for(list_channels, cat=item.cat_id)
        list_items.append((url, li, True))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/list_channels/<cat>")
def list_channels(cat):
    list_items = []
    for item in TV.get_live_category(int(cat)).channel:
        if item.stream.count() == 0:
            continue
        li = ListItem(item.channel_name)
        li.setProperty("IsPlayable", "true")
        li.setInfo(type="Video", infoLabels={"Title": item.channel_name, "mediatype": "video"})
        image = xbmc_curl_encode(TV.resolve_image(item.channel_image))
        li.setArt({"thumb": image, "icon": image})
        url = plugin.url_for(play, cat_id=item.cat_id, channel_id=item.channel_id)
        list_items.append((url, li, False))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route("/play/<cat_id>/<channel_id>/play.pvr")
def play(cat_id, channel_id):
    item = TV.get_live_channel(cat_id, channel_id)
    if item.stream.count() > 1:
        select_list = []
        for stream in item.stream:
            if stream.name:
                select_list.append(stream.name)
            else:
                select_list.append("Stream {0} {1}".format(stream.token, stream.stream_id))
        dialog = xbmcgui.Dialog()
        ret = dialog.select("Choose Stream", select_list)
        if ret >= 0:
            selected_stream = item.stream[ret]
        else:
            selected_stream = ""
    else:
        selected_stream = item.stream[0]

    if selected_stream:
        image = xbmc_curl_encode(TV.resolve_image(item.channel_image))
        stream = TV.resolve_stream(selected_stream)
        if ".m3u8" in stream[0]:
            stream_plugin = addon.getSetting("stream_plugin")
            if stream_plugin == "inputstream.adaptive":
                stream[1]["connection"] = "keep-alive"
                li = ListItem(item.channel_name, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
                if sys.version_info[0] == 2:
                    li.setProperty("inputstreamaddon", "inputstream.adaptive")
                else:
                    li.setProperty("inputstream", "inputstream.adaptive")
                li.setProperty("inputstream.adaptive.manifest_type", "hls")
                li.setProperty("inputstream.adaptive.stream_headers", urlencode(stream[1]))
                li.setProperty("inputstream.adaptive.manifest_headers", urlencode(stream[1]))
                li.setProperty("inputstream.adaptive.license_key", "|" + urlencode(stream[1]))
            elif stream_plugin == "ffmpeg":
                # stream = resolve_stream_host(stream)
                li = ListItem(item.channel_name, path=xbmc_curl_encode(stream))
                li.setContentLookup(False)
                li.setMimeType("application/vnd.apple.mpegurl")
        else:
            li = ListItem(item.channel_name, path=xbmc_curl_encode(stream))
        li.setArt({"thumb": image, "icon": image})
        xbmcplugin.setResolvedUrl(plugin.handle, True, li)
    else:
        xbmcplugin.setResolvedUrl(plugin.handle, False, ListItem())


if __name__ == "__main__":
    plugin.run(sys.argv)
    del TV
