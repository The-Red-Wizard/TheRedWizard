import os
import time
import uuid
import random
import json
from datetime import datetime
from base64 import b64decode, b64encode
from collections import OrderedDict
from hashlib import md5
from future.moves.urllib.parse import urljoin, urlencode, urlparse, parse_qs, quote
from future.builtins import bytes

from .peewee import SqliteDatabase, Model, IntegerField, TextField, ForeignKeyField, chunked
import requests

import pyamf
from pyamf import remoting
from pyamf.flex import messaging

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes
import warnings

warnings.simplefilter("ignore")
db = SqliteDatabase(None, pragmas={"foreign_keys": 1})


class BaseModel(Model):
    class Meta:
        database = db


class Config(BaseModel):
    data_age = IntegerField(default=time.time)
    updated = IntegerField()
    api_url = TextField()
    api_referer = TextField()
    cat_key = TextField()
    img_url = TextField(default="http://img.rapidstreams.io/1/data/images/")
    token_url_21 = TextField()
    token_url_23 = TextField()
    token_url_33 = TextField()
    token_url_34 = TextField()
    token_url_38 = TextField()
    token_url_44 = TextField()
    token_url_45 = TextField()
    token_url_48 = TextField()
    token_url_51 = TextField()
    token_url_52 = TextField()
    token_url_54 = TextField()


class User(BaseModel):
    device_id = TextField(default=uuid.uuid4)
    device_name = TextField(default="Amazon AFTN")
    android_id = TextField(default=uuid.uuid4().hex[:16])
    api_level = TextField(default="28")
    apk_name = TextField(default="com.rpstreamz.live")
    apk_cert = TextField(default="E6:1B:D0:74:7E:4B:CA:AA:2F:C6:CD:D2:BB:99:21:93")
    apk_version = TextField(default="2.9.6 (22)")
    apk_build = TextField(default="22")
    provider = TextField(default="7")
    user_id = TextField(default="")
    channels_updated = IntegerField(default=0)
    vod_updated = IntegerField(default=0)


class LiveCategory(BaseModel):
    cat_id = IntegerField(primary_key=True)
    cat_name = TextField()
    cat_image = TextField(null=True)
    last_modified = IntegerField(default=0)


class LiveChannel(BaseModel):
    channel_id = IntegerField(primary_key=True)
    cat_id = ForeignKeyField(LiveCategory, backref="channel")
    channel_image = TextField(null=True)
    channel_name = TextField()
    channel_updated = IntegerField(default=0)


class LiveStream(BaseModel):
    stream_id = IntegerField(primary_key=True)
    channel_id = ForeignKeyField(LiveChannel, backref="stream")
    name = TextField(null=True)
    token = TextField(null=True)
    referer = TextField(null=True)
    user_agent = TextField(null=True)
    url = TextField(null=True)


class LiveEvents(BaseModel):
    updated = IntegerField()
    events = TextField()


class RSTV(object):
    def __init__(self, cache_dir):
        self.user_agent = "Dalvik/2.1.0 (Linux; U; Android 5.1; AFTM Build/LMY47O)"
        self.player_user_agent = "Lavf/57.83.100"
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": self.user_agent})
        DB = os.path.join(cache_dir, "rstv3.db")
        db.init(DB)
        db.connect()
        db.create_tables([Config, User, LiveCategory, LiveChannel, LiveStream, LiveEvents], safe=True)
        if Config.select().where(Config.data_age + 8 * 60 * 60 > int(time.time())).count() == 0:
            try:
                self.config = self.update_config()
                print("update_config")
            except requests.exceptions.RequestException:
                self.config = Config.select()[0]
                _next_update = self.config.data_age + 60 * 60
                self.config.data_age = _next_update
                self.config.save()
        else:
            self.config = Config.select()[0]

        if User.select().count() == 0:
            self.user = self.register_user()
        else:
            self.user = User.select()[0]

    def __del__(self):
        db.close()
        self.s.close()

    def dec_aes_cbc_single(self, msg, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return unpad(cipher.decrypt(msg), 16).decode("utf-8")

    def enc_aes_cbc_single(self, msg, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return b64encode(cipher.encrypt(pad(msg.encode("utf-8"), 16))).decode("utf-8")

    def enc_aes_cbc_open(self, msg, key):
        rand_iv = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC, iv=rand_iv)
        return b64encode(rand_iv + cipher.encrypt(pad(msg.encode("utf-8"), 16))).decode("utf-8")

    def enc_aes_cbc_rand(self, msg):
        msg_bytes = msg.encode("utf-8")
        rand_key = get_random_bytes(32)
        rand_iv = get_random_bytes(16)
        rand_cipher = AES.new(rand_key, AES.MODE_CBC, iv=rand_iv)
        c_bytes = rand_cipher.encrypt(pad(msg_bytes, 16))
        return b64encode(rand_key + rand_iv + c_bytes).decode("utf-8")

    def dec_aes_cbc_rand(self, msg):
        b_msg = b64decode(msg)
        key = b_msg[:32]
        iv = b_msg[32 : 32 + 16]
        ct = b_msg[32 + 16 :]
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return unpad(cipher.decrypt(ct), 16).decode("utf-8")

    def custom_base64(self, encoded):
        custom_translate = bytes.maketrans(
            b"zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210+/",
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
        )
        return b64decode(encoded.encode("utf-8").translate(custom_translate)).decode("utf-8")

    def fetch_config(self):
        url = "https://api.backendless.com/A8C02132-F661-4092-FF63-B411E2324300/B0BACC3C-3F61-42C9-9FCB-04E0BA6A3E37/binary"
        msg = messaging.RemotingMessage(
            clientId=None,
            destination="GenericDestination",
            correlationId=None,
            source="com.backendless.services.persistence.PersistenceService",
            operation="first",
            messageRefType=None,
            headers={"application-type": "ANDROID", "api-version": "1.0"},
            timestamp=0,
            body=["ConfigAlpha"],
            timeToLive=0,
            messageId=None,
        )
        request_form = remoting.Envelope(pyamf.AMF3)
        request_form["null"] = remoting.Request(target="null", body=[msg])
        r = self.s.post(
            url,
            data=remoting.encode(request_form).getvalue(),
            headers={"Content-Type": "application/x-amf"},
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        res = remoting.decode(r.content)
        return res.bodies[0][1].body.body

    def update_config(self):
        def b64x2(s):
            return b64decode(b64decode(s[1:]).decode("utf-8"))

        key_name = "QXBwX2ludmVudG9y"
        key_key = b"wfekojemipesdtyx"
        key_iv = b"\00" * 16

        new_config = self.fetch_config()
        if Config.select().count() > 0:
            old_config = Config.select()[0]
            if old_config.updated == int(time.mktime(new_config["updated"].timetuple())):
                old_config.data_age = int(time.time())
                old_config.save()
                return old_config

        config_key = self.dec_aes_cbc_single(b64x2(new_config[key_name]), key_key, key_iv).encode("utf-8")
        config_iv = b"634B8K25E7H3F11B"

        Config.delete().execute()
        config = Config()
        config.updated = int(time.mktime(new_config["updated"].timetuple()))
        config.api_url = self.dec_aes_cbc_single(
            b64decode(new_config["eW9va2F5X09zbm92bmFfcG90"]), config_key, config_iv
        )
        config.cat_key = self.dec_aes_cbc_single(b64decode(new_config["Z29vZ2xlX2JhbmRlaXJh"]), config_key, config_iv)
        config.api_referer = b64decode(new_config["SXNpc2VrZWxvX3Nlc2lzdGltdV95ZXppbm9tYm9sbzAw"][1:])
        config.token_url_21 = self.dec_aes_cbc_single(b64decode(new_config["Y2FsYWFtb19pa3Mw"]), config_key, config_iv)
        config.token_url_23 = self.dec_aes_cbc_single(b64decode(new_config["dGhlX3RlYXMw"]), config_key, config_iv)
        config.token_url_33 = self.dec_aes_cbc_single(
            b64decode(new_config["ZmFtYW50YXJhbmFfdGF0aTAw"]), config_key, config_iv
        )
        config.token_url_34 = self.dec_aes_cbc_single(
            b64decode(new_config["ZGVjcnlwdGV1cl9MaWVu"]), config_key, config_iv
        )
        config.token_url_38 = self.dec_aes_cbc_single(b64decode(new_config["YmVsZ2lfMzgw"]), config_key, config_iv)
        config.token_url_44 = self.dec_aes_cbc_single(b64decode(new_config["YmVsa2lpdW1uXzk2"]), config_key, config_iv)
        config.token_url_45 = self.dec_aes_cbc_single(
            b64decode(new_config["bmdhZGVrcmlwUGF0YWxpbmFzazQ1"]), config_key, config_iv
        )
        config.token_url_48 = self.dec_aes_cbc_single(b64decode(new_config["Ym9ya3lsd3VyXzQ4"]), config_key, config_iv)
        config.token_url_51 = self.dec_aes_cbc_single(b64decode(new_config["cHJlZmVjdHVyZTUx"]), config_key, config_iv)
        config.token_url_52 = self.dec_aes_cbc_single(b64decode(new_config["d2lsYXlhaDUx"]), config_key, config_iv)
        config.token_url_54 = self.dec_aes_cbc_single(b64decode(new_config["Ym9rYXJpc2hvbDc3"]), config_key, config_iv)
        config.save()

        return config

    def id_token(self, user):
        ms_time = str(int(time.time() * 1000))
        token = [
            md5(ms_time.encode("utf-8")).hexdigest().encode("utf-8"),
            b64encode(user.apk_name.encode("utf-8")),
            b64encode(user.apk_cert.encode("utf-8")),
            b64encode(user.device_name.encode("utf-8")),
            b64encode(user.api_level.encode("utf-8")),
            b64encode(user.apk_build.encode("utf-8")),
            b64encode(ms_time.encode("utf-8")),
            b64encode(str(user.device_id).encode("utf-8")),
            b"1",
        ]
        return b64encode(b"|".join(token)).decode("utf-8")

    def allow_token(self, user):
        ms_time = str(int(time.time()) * 1000)
        token = [md5(ms_time.encode("utf-8")).hexdigest(), user.apk_name, user.apk_cert, ms_time, user.user_id, "7"]
        return b64encode("$".join(token).encode("utf-8"))

    def events_allow_token(self, user):
        ms_time = str(int(time.time()) * 1000)
        token = [
            md5(ms_time.encode("utf-8")).hexdigest(),
            user.apk_name,
            user.apk_cert,
            ms_time,
            user.user_id,
            user.apk_build,
        ]
        return b64encode("$".join(token).encode("utf-8"))

    def modified_token(self, i):
        utc = datetime.utcnow()
        timestamp = int(datetime.timestamp(datetime(utc.year, utc.month, utc.day, utc.hour, utc.minute)))
        token = []
        for i, c in enumerate(str(timestamp ^ i)):
            token.append(c)
            token.append(str(i))
        return "".join(token)

    def category_meta(self, category):
        token = [
            str(category.cat_id),
            str(category.last_modified),
            category.cat_name,
            str(int(time.time()) * 1000),
            self.user.apk_name,
        ]
        return b64encode("$".join(token).encode("utf-8")).decode("utf-8")

    def resolve_image(self, image):
        return (urljoin(self.config.img_url, quote(image)), {"User-Agent": "okhttp/3.10.0"})

    def get_api_key(self):
        _key = "".join([a + str(random.getrandbits(48) % 9 + 1) for a in "z5Zg7fp3bWBTfCCd"])
        return "{0}.{1}".format(_key, int(time.time() * 1000))

    def get_category_key(self, category):
        _key = "".join([a + str(random.getrandbits(48) % 9 + 1) for a in "z5Zg7fp3bWBTfCCd"])
        token = [_key, str(int(time.time()) * 1000), str(category.cat_id), category.cat_name]
        return b64encode("$".join(token).encode("utf-8")).decode("utf-8")

    def register_user(self):
        user = User()
        post_data = {
            "api_level": user.api_level,
            "device_name": user.device_name,
            "android_id": user.android_id,
            "key": self.enc_aes_cbc_rand(self.get_api_key()),
            "version": user.apk_version,
            "id": self.id_token(user),
            "source": "backendless",
            "bug": "false",
            "pro": "true",
        }
        post_dump = json.dumps(post_data, separators=(",", ":"))
        post_encoded = urlencode({"_": self.enc_aes_cbc_rand(post_dump)}) + "&"
        content_length = len(post_encoded)
        headers = OrderedDict(
            [
                ("Referer", self.config.api_referer),
                ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                ("User-Agent", self.user_agent),
                ("Connection", "Keep-Alive"),
                ("Accept-Encoding", "gzip, deflate"),
                ("Content-Length", str(content_length)),
            ]
        )
        req = requests.Request("POST", urljoin(self.config.api_url, "adduser.rs/"), data=post_encoded)
        prepped = self.s.prepare_request(req)
        prepped.headers = headers
        r = self.s.send(prepped, timeout=10)
        r.raise_for_status()
        res = r.json()
        if "user_id" in res:
            user.user_id = res.get("user_id")

        user.save()
        return user

    def fetch_categories(self):
        post_data = {
            "key": b64encode(self.get_api_key().encode("utf-8")).decode("utf-8"),
            "user_id": self.id_token(self.user),
            "id": self.user.user_id,
            "cert": self.user.apk_cert,
            "version": self.user.apk_build,
            "check": "2",
            "pro": "true",
        }
        post_dump = json.dumps(post_data, separators=(",", ":"))
        post_encoded = urlencode({"_": self.enc_aes_cbc_rand(post_dump)}) + "&"
        content_length = len(post_encoded)
        headers = OrderedDict(
            [
                ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                ("User-Agent", self.user_agent),
                ("Connection", "Keep-Alive"),
                ("Accept-Encoding", "gzip, deflate"),
                ("Content-Length", str(content_length)),
            ]
        )
        req = requests.Request("POST", urljoin(self.config.api_url, "categories/"), data=post_encoded)
        prepped = self.s.prepare_request(req)
        prepped.headers = headers
        r = self.s.send(prepped, timeout=10)
        r.raise_for_status()
        return r.json()

    def fetch_live_events(self):
        post_data = {"ALLOW": self.events_allow_token(self.user)}
        post_encoded = urlencode(post_data)
        content_length = len(post_encoded)
        headers = OrderedDict(
            [
                ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                ("User-Agent", self.user_agent),
                ("Connection", "Keep-Alive"),
                ("Accept-Encoding", "gzip"),
                ("Content-Length", str(content_length)),
            ]
        )
        req = requests.Request("POST", urljoin(self.config.api_url, "events.rs/"), data=post_encoded)
        prepped = self.s.prepare_request(req)
        prepped.headers = headers
        r = self.s.send(prepped, timeout=15)
        r.raise_for_status()
        res = r.json()
        events = {}
        for day in res.keys():
            event_day = []
            for event in res[day]:
                event_day.append(
                    {
                        "start": event["trats"],
                        "end": event["dne"],
                        "sport": self.custom_base64(event["lkjlkjbz"]),
                        "match": self.custom_base64(event["SDvZfvfp"]),
                        "streams": event["zfdhxfjgk"],
                    }
                )
            events[day] = event_day
        return events

    def get_live_events(self):
        if LiveEvents.select().where(LiveEvents.updated + 10 * 60 > int(time.time())).count() == 0:
            LiveEvents.delete().execute()
            new_events = LiveEvents()
            new_events.events = self.fetch_live_events()
            new_events.updated = int(time.time())
            new_events.save()
            return json.loads(new_events.events, strict=False)
        else:
            return json.loads(LiveEvents.select()[0].events, strict=False)

    def fetch_live_channels(self, category):
        enc_cat = self.enc_aes_cbc_open(str(category.cat_id), self.config.cat_key.encode("utf-8"))
        post_data = {
            "key": self.get_category_key(category),
            "user_id": self.id_token(self.user),
            "id": self.user.user_id,
            "cert": self.user.apk_cert,
            "version": self.user.apk_build,
            "bug": "false",
            "meta": self.category_meta(category),
        }
        post_dump = json.dumps(post_data, separators=(",", ":"))
        post_encoded = urlencode({"_": self.enc_aes_cbc_rand(post_dump)}) + "&"
        content_length = len(post_encoded)
        headers = OrderedDict(
            [
                ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                ("User-Agent", self.user_agent),
                ("Connection", "Keep-Alive"),
                ("Accept-Encoding", "gzip, deflate"),
                ("Content-Length", str(content_length)),
            ]
        )
        req = requests.Request("POST", urljoin(self.config.api_url, "channels/{0}".format(enc_cat)), data=post_encoded)
        prepped = self.s.prepare_request(req)
        prepped.headers = headers
        r = self.s.send(prepped, timeout=15)
        r.raise_for_status()
        return r.json()

    def update_live_categories(self):
        res = self.fetch_categories()
        self.config.img_url = self.dec_aes_cbc_single(
            b64decode(res.get("lckanscas", "")), b"55UCcS4j8B2gc6bj", b"\00" * 16
        )
        self.config.save()

        def categories(res):
            for category in res["hjfgjdruo"]:
                yield {
                    "cat_id": category["dic"],
                    "cat_name": self.custom_base64(category["kjadalhlkh"]),
                    "cat_image": self.custom_base64(category["kadosahihnc"]),
                    "last_modified": category["lhsoidfhkjd"],
                }

        print("update_live_categories")
        with db.atomic():
            for batch in chunked(categories(res), 79):
                LiveCategory.replace_many(batch).execute()

    def update_live_channels(self, category):
        def stream_filter(stream):
            if stream["token"] in ["", "1", "34"]:
                return True
            else:
                return False

        ch_key = b"55UCcS4j8B2gc6Ak"
        ch_iv = b"\00" * 16
        res = self.fetch_live_channels(category)

        def channels(res):
            for channel in res["zfzdsgdsasd"]:
                yield {
                    "channel_id": channel["id"],
                    "cat_id": channel["cat_id"],
                    "channel_image": channel["hdfbaetrd"],
                    "channel_name": channel["fgjsvsger"],
                    "channel_updated": category.last_modified,
                }

        def streams(res):
            for channel in res["zfzdsgdsasd"]:
                for stream in channel["channel_streams"]:
                    yield {
                        "channel_id": channel["id"],
                        "stream_id": int(b64decode(stream["zkbdvlksdnvas"][1:])),
                        "name": b64decode(stream.get("dkahsdlfk", "")[1:]).decode("utf-8"),
                        "token": self.custom_base64(stream.get("xoiuouop", "")),
                        "referer": stream.get("bvnbxvsbvui", ""),
                        "user_agent": self.custom_base64(stream.get("ljhahaeaoi", "")),
                        "url": self.dec_aes_cbc_single(
                            b64decode(self.custom_base64(stream["YmF0YW5pZHpv"])), ch_key, ch_iv
                        ),
                    }

        print("update_live_channels")
        with db.atomic():
            cat_channels = [v.channel_id for v in LiveChannel.select().where(LiveChannel.cat_id == category.cat_id)]
            LiveStream.delete().where(LiveStream.channel_id.in_(cat_channels)).execute()
            LiveChannel.delete().where(LiveChannel.cat_id == category.cat_id).execute()

            for batch in chunked(channels(res), 79):
                LiveChannel.replace_many(batch).execute()
            for batch in chunked(filter(stream_filter, streams(res)), 79):
                LiveStream.replace_many(batch).execute()

    def get_live_categories(self):
        current_time = int(time.time())
        if self.user.channels_updated + 8 * 60 * 60 < current_time:
            self.update_live_categories()
            self.user.channels_updated = current_time
            self.user.save()

        return LiveCategory.select().order_by(LiveCategory.cat_name)

    def get_live_category(self, cat_id):
        current_time = int(time.time())
        if self.user.channels_updated + 8 * 60 * 60 < current_time:
            self.update_live_categories()
            self.user.channels_updated = current_time
            self.user.save()

        category = LiveCategory.select().where(LiveCategory.cat_id == cat_id).first()
        if category.channel.count() == 0:
            self.update_live_channels(category)
        else:
            if category.channel[0].channel_updated != category.last_modified:
                self.update_live_channels(category)

        return LiveCategory.select().where(LiveCategory.cat_id == cat_id).first()

    def get_live_channel(self, cat_id, channel_id):
        current_time = int(time.time())
        if self.user.channels_updated + 8 * 60 * 60 < current_time:
            self.update_live_categories()
            self.user.channels_updated = current_time
            self.user.save()

        category = LiveCategory.select().where(LiveCategory.cat_id == cat_id).first()
        if category.channel.count() == 0:
            self.update_live_channels(category)
        else:
            if category.channel[0].channel_updated != category.last_modified:
                self.update_live_channels(category)

        return LiveChannel.select().where(LiveChannel.channel_id == channel_id).first()

    def get_live_link(self, link):
        post_data = {"v": parse_qs(urlparse(link).query)["id"][0], "ALLOW": self.events_allow_token(self.user)}
        post_encoded = urlencode(post_data)
        content_length = len(post_encoded)
        headers = OrderedDict(
            [
                ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                ("User-Agent", self.user_agent),
                ("Connection", "Keep-Alive"),
                ("Accept-Encoding", "gzip"),
                ("Content-Length", str(content_length)),
            ]
        )
        req = requests.Request("POST", link, data=post_encoded)
        prepped = self.s.prepare_request(req)
        prepped.headers = headers
        r = self.s.send(prepped, timeout=15)
        r.raise_for_status()
        return json.loads(b64decode(r.text.strip()[3:]).decode("utf-8"))

    def resolve_stream(self, stream):
        headers = {}
        player_headers = {}
        if stream.user_agent:
            headers["User-Agent"] = stream.user_agent
            player_headers["User-Agent"] = stream.user_agent
        else:
            headers["User-Agent"] = self.user_agent
            player_headers["User-Agent"] = self.player_user_agent
        if stream.referer:
            headers["Referer"] = stream.referer
            player_headers["Referer"] = stream.referer

        if stream.token == "":
            """direct"""
            return (stream.url, player_headers)
        elif stream.token == "1":
            """main"""
            headers["Referer"] = "rapidstreamz"
            post_data = {"referer": "rapidstreamz", "meta": self.enc_aes_cbc_rand(self.user.user_id)}
            r = self.s.post(self.config.token_url_21, data=post_data, headers=headers)
            r.raise_for_status()
            return (stream.url + r.text, player_headers)
        elif stream.token == "2":
            """youtube"""
            pass
        elif stream.token == "18":
            """canlitv"""
            pass
        elif stream.token == "34":
            """scrape"""
            _url, _headers, _data, _method, _site = b64decode(stream.url[1:]).decode("utf-8").split("|")
            _headers = _headers.split(",")
            for i, t in enumerate(_headers):
                if t == "referer":
                    headers["Referer"] = _headers[i + 1]
                if t == "user-agent":
                    headers["User-Agent"] = _headers[i + 1]
            r = self.s.get(_url, headers=headers)
            r.raise_for_status()
            res = r.text
            post_data = {"stream_url": stream.url, "token": 34, "response_body": res}
            r_headers = {"Modified": self.modified_token(1234567), "User-Agent": self.user_agent}
            r = self.s.post(
                self.config.token_url_34, headers=r_headers, data={"data": json.dumps(post_data, separators=(",", ":"))}
            )
            r.raise_for_status()
            return (r.json()["stream_url"], player_headers)
        elif stream.token == "43":
            """bdiptv"""
            ms_time = str(int(time.time()) * 1000)
            token = [
                md5(ms_time.encode("utf-8")).hexdigest(),
                self.user.apk_name,
                self.user.apk_cert,
                "lastEventsTime",
                self.user.user_id,
                "7",
                "[B@efbadad",  # ???
            ]
            allow_token = b64encode("$".join(token).decode("utf-8"))
            post_data = {"v": "", "ALLOW": allow_token}
            r = self.s.post(stream.url, data=post_data)
            r.raise_for_status()
