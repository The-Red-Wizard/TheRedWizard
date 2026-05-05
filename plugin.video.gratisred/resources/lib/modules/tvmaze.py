# -*- coding: utf-8 -*-
"""
Lightweight TVmaze API wrapper used by indexers/tvshows.py and
indexers/episodes.py.  TVmaze has no API key and no rate-limit auth so
all calls are anonymous GETs.

Public API documented at:  https://www.tvmaze.com/api
"""

import requests
from six.moves.urllib_parse import urlencode

HEADERS = {'Content-Type': 'application/json;charset=utf-8'}
BASE = 'https://api.tvmaze.com'


class tvMaze:
    def __init__(self, show_id=None):
        self.api_url = BASE + '/%s%s'
        self.show_id = show_id


    def showID(self, show_id=None):
        if show_id is not None:
            self.show_id = show_id
            return show_id
        return self.show_id


    def request(self, endpoint, query=None):
        try:
            if query is not None:
                query = '?' + urlencode(query)
            else:
                query = ''
            request_url = self.api_url % (endpoint, query)
            response = requests.get(request_url, headers=HEADERS, timeout=15).json()
            return response
        except Exception:
            pass
        return {}


    def showLookup(self, type, id):
        try:
            result = self.request('lookup/shows', {type: id})
            if 'id' in result:
                self.show_id = result['id']
            return result
        except Exception:
            pass
        return {}


    def shows(self, show_id=None, embed=None):
        try:
            if not self.showID(show_id):
                raise Exception("showID Error.")
            result = self.request('shows/%d' % int(self.show_id))
            if 'id' in result:
                self.show_id = result['id']
            return result
        except Exception:
            pass
        return {}


    def showSeasons(self, show_id=None):
        try:
            if not self.showID(show_id):
                raise Exception("showID Error.")
            result = self.request('shows/%d/seasons' % int(self.show_id))
            if len(result) > 0 and 'id' in result[0]:
                return result
        except Exception:
            pass
        return []


    def showEpisodeList(self, show_id=None, specials=False):
        try:
            if not self.showID(show_id):
                raise Exception("showID Error.")
            result = self.request(
                'shows/%d/episodes' % int(self.show_id),
                {'specials': 1} if specials else None,
            )
            if len(result) > 0 and 'id' in result[0]:
                return result
        except Exception:
            pass
        return []


    # -------- index-style helpers used by the new TVmaze sections --------

    def page(self, page=0):
        try:
            result = self.request('shows', {'page': int(page)})
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []


    def schedule(self, country='US', date=None):
        try:
            q = {}
            if country:
                q['country'] = country
            if date:
                q['date'] = date
            result = self.request('schedule', q)
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []


    def webSchedule(self, date=None):
        try:
            q = {}
            if date:
                q['date'] = date
            result = self.request('schedule/web', q)
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []


    def updates(self, since='day'):
        try:
            result = self.request('updates/shows', {'since': since})
            if isinstance(result, dict):
                return result
        except Exception:
            pass
        return {}


    def search(self, query):
        try:
            result = self.request('search/shows', {'q': query})
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []


    def searchPeople(self, query):
        try:
            result = self.request('search/people', {'q': query})
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []
