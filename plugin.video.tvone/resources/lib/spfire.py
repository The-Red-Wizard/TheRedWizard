# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 RACC
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

import os
import requests
from . import peewee as pw
from base64 import b64encode, b64decode
from binascii import a2b_hex
from Cryptodome.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from Cryptodome.Cipher import DES
from Cryptodome.PublicKey import RSA
from Cryptodome.Util.Padding import unpad
from future.moves.urllib.parse import quote as orig_quote
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter
from warnings import simplefilter

simplefilter("ignore")


def quote(s, safe=""):
    return orig_quote(s.encode("utf-8"), safe.encode("utf-8"))


db = pw.SqliteDatabase(None)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Category(BaseModel):
    cat_id = pw.IntegerField(unique=True)
    cat_name = pw.TextField()


class Channel(BaseModel):
    pk_id = pw.IntegerField(unique=True)
    img = pw.TextField()
    country = pw.TextField()
    channel_name = pw.TextField()
    cat_name = pw.TextField()
    cat_id = pw.ForeignKeyField(Category, to_field="cat_id", backref="channels")
    link_to_play = pw.IntegerField()


class UKTVNow:
    def __init__(self, cache_dir):
        DB = os.path.join(cache_dir, "spfire1.db")
        db.init(DB)
        db.connect()
        db.create_tables([Channel, Category], safe=True)
        self.base_url = "https://spfire.work/tv/index.php"
        self.user_agent = "Dalvik/2.1.0 (Linux; U; Android 5.1.1; AFTS Build/LVY48F)"
        self.player_user_agent = "mediaPlayerhttp/1.4 (Linux;Android 9) ExoPlayerLib/2.10.0"
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": "USER-AGENT-tvmob-APP-V2", "Accept-Encoding": "gzip"})
        retries = Retry(total=5, backoff_factor=0)
        retryable_adapter = HTTPAdapter(max_retries=retries)
        self.s.mount("https://", retryable_adapter)

    def __del__(self):
        db.close()
        self.s.close()

    def image_url(self, img):
        return "https://spfire.work/tv/{0}|User-Agent={1}".format(quote(img, "/"), quote(self.user_agent))

    def stream_url(self, link):
        if link.startswith("http"):
            return (link, {"User-Agent": self.player_user_agent})
        else:
            return (link, {})

    @staticmethod
    def payload():
        _pubkey = RSA.importKey(
            a2b_hex(
                "30819f300d06092a864886f70d010101050003818d003081890281"
                "8100bfa5514aa0550688ffde568fd95ac9130fcdd8825bdecc46f1"
                "8f6c6b440c3685cc52ca03111509e262dba482d80e977a938493ae"
                "aa716818efe41b84e71a0d84cc64ad902e46dbea2ec61071958826"
                "4093e20afc589685c08f2d2ae70310b92c04f9b4c27d79c8b5dbb9"
                "bd8f2003ab6a251d25f40df08b1c1588a4380a1ce8030203010001"
            )
        )
        _msg = a2b_hex(
            "7b224d4435223a22695757786f45684237686167747948392b58563052513d3d5c6e222c22534"
            "84131223a2242577761737941713841327678435c2f5450594a74434a4a544a66593d5c6e227d"
        )
        cipher = Cipher_PKCS1_v1_5.new(_pubkey)
        return b64encode(cipher.encrypt(_msg))

    def api_request(self, case, channel_id=None):
        headers = {"app-token": "9120163167c05aed85f30bf88495bd89"}
        data = {"payload": self.payload(), "username": "603803577"}
        if channel_id:
            data["type"] = "channel"
            data["channel_id"] = channel_id
        params = {"case": case}
        r = self.s.post(self.base_url, headers=headers, params=params, data=data, timeout=5, verify=False)
        r.raise_for_status()
        resp = r.json()
        print(resp)
        if resp["success"] == 1:
            return resp["msg"]
        else:
            raise ValueError(resp["msg"])

    def update_channels(self):
        _channels = self.api_request("get_all_channels")["channels"]
        print(_channels)
        _category_list = []
        _categories = []
        for c in _channels:
            if c.get("cat_id") not in _category_list:
                _category_list.append(c.get("cat_id"))
                _categories.append({"cat_id": c.get("cat_id"), "cat_name": c.get("cat_name")})
        with db.atomic():
            Category.replace_many(_categories).execute()
            if len(_channels) > 2:
                """Data fetch successful delete old data"""
                Channel.delete().execute()
            for batch in pw.chunked(_channels, 100):
                Channel.replace_many(batch).execute()

    def get_categories(self):
        return Category.select()

    def get_channels_by_category(self, cat_id):
        return Category.get(Category.cat_id == cat_id).channels

    def get_channel_by_id(self, pk_id):
        return Channel.get(Channel.pk_id == pk_id)

    def get_channel_links(self, pk_id):
        _channel = self.api_request("get_channel_link_with_token_latest", pk_id)["channel"][0]
        links = []
        for stream in _channel.keys():
            if "stream" in stream or "chrome_cast" in stream:
                _crypt_link = _channel[stream]
                if _crypt_link:
                    d = DES.new(b"98221122", DES.MODE_ECB)
                    link = unpad(d.decrypt(b64decode(_crypt_link)), 8).decode("utf-8")
                    if not link == "dummytext" and link not in links:
                        links.append(link)
        return [self.stream_url(l) for l in links]
