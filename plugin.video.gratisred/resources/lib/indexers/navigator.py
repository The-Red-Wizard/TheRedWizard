# -*- coding: utf-8 -*-

import os
import sys

from resources.lib.modules import control
from resources.lib.modules import trakt
from resources.lib.modules import tmdb_utils
from resources.lib.modules import log_utils

try:
    #from infotagger.listitem import ListItemInfoTag
    from resources.lib.modules.listitem import ListItemInfoTag
except:
    pass

sysaddon = sys.argv[0]
syshandle = int(sys.argv[1])
#control.moderator()

tmdbCredentials = tmdb_utils.getTMDbCredentialsInfo()
traktCredentials = trakt.getTraktCredentialsInfo()
traktIndicators = trakt.getTraktIndicatorsInfo()

kodi_version = control.getKodiVersion()


class navigator:
    def root(self):
        # Persistent 'What's New' entry — visible until the user opens/dismisses it.
        try:
            from resources.lib.modules import changelog_notice
            if changelog_notice.has_pending_notice():
                self.addDirectoryItem('[COLOR gold][B]What\'s New[/B] (Click to View Changelog)[/COLOR]',
                                      'show_changelog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
                self.addDirectoryItem('[COLOR grey][I]Dismiss "What\'s New" banner[/I][/COLOR]',
                                      'dismiss_changelog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        except Exception:
            pass
        self.addDirectoryItem('Movies', 'movies_menu', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('TV Shows', 'tvshows_menu', 'tvshows.png', 'DefaultTVShows.png')
        #if (traktIndicators == True and not control.setting('episode.widget.alt') == '0') or (traktIndicators == False and not control.setting('episode.widget') == '0'):
            #self.addDirectoryItem(self.episode_widget(), 'episode_widget', 'latest-episodes.png', 'DefaultRecentlyAddedEpisodes.png')
        #if not control.setting('lists.widget') == '0':
        self.addDirectoryItem('My Stuff', 'mylists_menu', 'mymovies.png', 'DefaultSets.png')
        #self.addDirectoryItem('More Stuff', 'moreplugs_menu', 'tools.png', 'DefaultSets.png')
        self.addDirectoryItem('Tools', 'tools_menu', 'tools.png', 'DefaultAddonProgram.png')
        if not control.setting('dev.widget') == 'false':
            self.addDirectoryItem('Developer Tools', 'devtools_menu', 'tools.png', 'DefaultAddonProgram.png')
        self.endDirectory(cached=False)


    #def episode_widget(self):
        #widgetChoice = 'Episodes (Widget) [I]- %s[/I]'
        #if traktIndicators == True:
            #setting = control.setting('episode.widget.alt')
        #else:
            #setting = control.setting('episode.widget')
        #if setting == '1':
            #return widgetChoice % 'TVmaze Calendar'
        #elif setting == '2':
            #return widgetChoice % 'Trakt Progress'
        #elif setting == '3':
            #return widgetChoice % 'Trakt Episodes'
        #else:
            #return 'Disabled'


    #def moreplugs(self):
        #self.addDirectoryItem('Sky Channels', 'sky_channels_menu', 'channels.png', 'DefaultSets.png')
        #self.addDirectoryItem('TVpassport Channels', 'tvpassport_menu', 'channels.png', 'DefaultSets.png')
        #self.addDirectoryItem('Flixed Channels', 'flixed_menu', 'channels.png', 'DefaultSets.png')
        #self.addDirectoryItem('GdrivePlayer', 'gdriveplayer.root', 'channels.png', 'DefaultSets.png')
        #self.addDirectoryItem('WatchOnline (Dedicated Sites)', 'watchonline_menu', 'channels.png', 'DefaultSets.png')
        #if not control.condVisibility('System.HasAddon(plugin.video.json_iptv)'):
        #    self.addDirectoryItem('Install Json IPTV', 'installAddon&id=plugin.video.json_iptv', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #else:
        #    self.addDirectoryItem('Open Json IPTV', 'plugin://plugin.video.json_iptv/?action=open_root', 'most-popular.png', 'DefaultAddonProgram.png', isAction=False)
        #self.endDirectory()


    def movies(self):
        self.addDirectoryItem('Explore TMDb', 'movies_tmdb_menu', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Explore Trakt', 'movies_trakt_menu', 'trakt.png', 'DefaultMovies.png')
        self.addDirectoryItem('TV Passport Channels', 'tvpassport_menu', 'channels.png', 'DefaultSets.png')
        self.addDirectoryItem('Search Tools', 'search_movies_menu', 'search.png', 'DefaultFolder.png')
        self.endDirectory()


    def tvshows(self):
        self.addDirectoryItem('Explore TMDb', 'tvshows_tmdb_menu', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Explore Trakt', 'tvshows_trakt_menu', 'trakt.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Explore TVmaze', 'tvshows_tvmaze_menu', 'networks.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Search Tools', 'search_tvshows_menu', 'search.png', 'DefaultFolder.png')
        self.endDirectory()


    def movieTMDb(self):
        self.addDirectoryItem('In Theatres', 'movies&url=tmdb_in_theatres', 'latest-movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('Now Playing', 'movies&url=tmdb_now_playing', 'in-theaters.png', 'DefaultMovies.png')
        self.addDirectoryItem('Popular', 'movies&url=tmdb_popular', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Top Rated', 'movies&url=tmdb_toprated', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem('Upcoming', 'movies&url=tmdb_upcoming', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem('Trending Daily', 'movies&url=tmdb_trending_day', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem('Trending Weekly', 'movies&url=tmdb_trending_week', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem('Featured', 'movies&url=tmdb_featured', 'featured.png', 'DefaultMovies.png')
        self.addDirectoryItem('Premiere', 'movies&url=tmdb_premiere', 'latest-movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('Views', 'movies&url=tmdb_views', 'most-voted.png', 'DefaultMovies.png')
        self.addDirectoryItem('Years', 'movies_tmdb_years', 'years.png', 'DefaultMovies.png')
        self.addDirectoryItem('Decades', 'movies_tmdb_decades', 'years.png', 'DefaultMovies.png')
        self.addDirectoryItem('Genres', 'movies_tmdb_genres', 'genres.png', 'DefaultMovies.png')
        self.addDirectoryItem('Languages', 'movies_tmdb_languages', 'languages.png', 'DefaultMovies.png')
        self.addDirectoryItem('Certifications', 'movies_tmdb_certifications', 'certificates.png', 'DefaultMovies.png')
        self.addDirectoryItem('Popular Companies', 'movies_tmdb_popular_companies', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Popular Keywords', 'movies_tmdb_popular_keywords', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Popular People', 'movies_tmdb_popular_people', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections', 'movies_tmdb_collections_menu', 'tmdb.png', 'DefaultVideoPlaylists.png')
        self.addDirectoryItem('Movie Lists', 'movies_tmdb_userlists_menu', 'tmdb.png', 'DefaultVideoPlaylists.png')
        self.endDirectory()


    def tvTMDb(self):
        self.addDirectoryItem('Airing Today', 'tvshows&url=tmdb_airing', 'airing-today.png', 'DefaultTVShows.png')
        self.addDirectoryItem('On The Air', 'tvshows&url=tmdb_active', 'returning-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Popular', 'tvshows&url=tmdb_popular', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Top Rated', 'tvshows&url=tmdb_toprated', 'highly-rated.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Trending Daily', 'tvshows&url=tmdb_trending_day', 'highly-rated.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Trending Weekly', 'tvshows&url=tmdb_trending_week', 'highly-rated.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Featured', 'tvshows&url=tmdb_featured', 'featured.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Premiere', 'tvshows&url=tmdb_premiere', 'new-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Views', 'tvshows&url=tmdb_views', 'most-voted.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Years', 'tvshows_tmdb_years', 'years.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Decades', 'tvshows_tmdb_decades', 'years.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Networks', 'tvshows_tmdb_networks', 'networks.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Genres', 'tvshows_tmdb_genres', 'genres.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Languages', 'tvshows_tmdb_languages', 'languages.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Popular Companies', 'tvshows_tmdb_popular_companies', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Popular Keywords', 'tvshows_tmdb_popular_keywords', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Popular People', 'tvshows_tmdb_popular_people', 'tmdb.png', 'DefaultTVShows.png')
        #self.addDirectoryItem('Collections', 'tvshows_tmdb_collections_menu', 'tmdb.png', 'DefaultVideoPlaylists.png')
        self.addDirectoryItem('TV Show Lists', 'tvshows_tmdb_userlists_menu', 'tmdb.png', 'DefaultVideoPlaylists.png')
        self.endDirectory()


    def movieTrakt(self):
        self.addDirectoryItem('Most Popular', 'movies&url=trakt_popular', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Featured', 'movies&url=trakt_featured', 'featured.png', 'DefaultMovies.png')
        self.addDirectoryItem('Box Office', 'movies&url=trakt_boxoffice', 'box-office.png', 'DefaultMovies.png')
        self.addDirectoryItem('Trending', 'movies&url=trakt_trending', 'people-watching.png', 'DefaultMovies.png')
        self.addDirectoryItem('Anticipated', 'movies&url=trakt_anticipated', 'latest-movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('Movie Mosts', 'movies_trakt_moviemosts', 'trakt.png', 'DefaultMovies.png')
        self.endDirectory()


    def tvTrakt(self):
        self.addDirectoryItem('Most Popular', 'tvshows&url=trakt_popular', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Featured', 'tvshows&url=trakt_featured', 'featured.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Trending', 'tvshows&url=trakt_trending', 'people-watching.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Anticipated', 'tvshows&url=trakt_anticipated', 'new-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Premiere', 'tvshows&url=trakt_premieres', 'new-tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('TV Show Mosts', 'tvshows_trakt_showmosts', 'trakt.png', 'DefaultTVShows.png')
        self.endDirectory()


    def tmdbMovieCollections(self):
        self.addDirectoryItem('Collections List: All', 'movies_tmdb_collections&url=all', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Alphabetical', 'movies_tmdb_collections_alphabetical_menu', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Genres', 'movies_tmdb_collections_genres_menu', 'tmdb.png', 'DefaultMovies.png')
        self.endDirectory()


    def tmdbMovieCollectionsAlphabetical(self):
        self.addDirectoryItem('Collections List: 1 (#-Am)', 'movies_tmdb_collections&url=page1', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 2 (Am-Be)', 'movies_tmdb_collections&url=page2', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 3 (Be-Ch)', 'movies_tmdb_collections&url=page3', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 4 (Ch-De)', 'movies_tmdb_collections&url=page4', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 5 (De-Es)', 'movies_tmdb_collections&url=page5', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 6 (Es-Gi)', 'movies_tmdb_collections&url=page6', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 7 (Gl-Ho)', 'movies_tmdb_collections&url=page7', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 8 (Ho-Ki)', 'movies_tmdb_collections&url=page8', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 9 (Ki-Ma)', 'movies_tmdb_collections&url=page9', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 10 (Mc-Ni)', 'movies_tmdb_collections&url=page10', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 11 (Ni-Ps)', 'movies_tmdb_collections&url=page11', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 12 (Pu-Se)', 'movies_tmdb_collections&url=page12', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 13 (Se-St)', 'movies_tmdb_collections&url=page13', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 14 (St-Th)', 'movies_tmdb_collections&url=page14', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 15 (Th-Th)', 'movies_tmdb_collections&url=page15', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 16 (Th-Th)', 'movies_tmdb_collections&url=page16', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 17 (Th-Un)', 'movies_tmdb_collections&url=page17', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: 18 (Un-Zu)', 'movies_tmdb_collections&url=page18', 'tmdb.png', 'DefaultMovies.png')
        self.endDirectory()


    def tmdbMovieCollectionsGenres(self):
        self.addDirectoryItem('Collections List: Action', 'movies_tmdb_collections_genres&url=Action', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Adventure', 'movies_tmdb_collections_genres&url=Adventure', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Animation', 'movies_tmdb_collections_genres&url=Animation', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Comedy', 'movies_tmdb_collections_genres&url=Comedy', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Crime', 'movies_tmdb_collections_genres&url=Crime', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Documentary', 'movies_tmdb_collections_genres&url=Documentary', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Drama', 'movies_tmdb_collections_genres&url=Drama', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Family', 'movies_tmdb_collections_genres&url=Family', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Fantasy', 'movies_tmdb_collections_genres&url=Fantasy', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: History', 'movies_tmdb_collections_genres&url=History', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Horror', 'movies_tmdb_collections_genres&url=Horror', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Music', 'movies_tmdb_collections_genres&url=Music', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Mystery', 'movies_tmdb_collections_genres&url=Mystery', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Romance', 'movies_tmdb_collections_genres&url=Romance', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Science Fiction', 'movies_tmdb_collections_genres&url=Science Fiction', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: TV Movie', 'movies_tmdb_collections_genres&url=TV Movie', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Thriller', 'movies_tmdb_collections_genres&url=Thriller', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: War', 'movies_tmdb_collections_genres&url=War', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections List: Western', 'movies_tmdb_collections_genres&url=Western', 'tmdb.png', 'DefaultMovies.png')
        self.endDirectory()


    def tmdbMovieLists(self):
        self.addDirectoryItem('Actor Collections', 'movies_tmdb_userlists&url=tmdbActorCollections', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('DC vs Marvel', 'movies_tmdb_userlists&url=tmdbDCvsMarvel', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Holidays', 'movies_tmdb_userlists&url=tmdbHolidays', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Assortment of Lists', 'movies_tmdb_userlists&url=tmdbAssortment', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections', 'movies_tmdb_userlists&url=tmdbCollections', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections Dupes', 'movies_tmdb_userlists&url=tmdbCollectionsDupes', 'tmdb.png', 'DefaultMovies.png')
        self.addDirectoryItem('Jew Movies', 'movies&url=tmdb_jewmovies', 'tmdb.png', 'DefaultMovies.png')
        self.endDirectory()


    def tmdbShowLists(self):
        self.addDirectoryItem('TV Show Lists', 'tvshows_tmdb_userlists', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Hulu Originals', 'tvshows&url=tmdb_huluorig', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Netflix Originals', 'tvshows&url=tmdb_netflixorig', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Amazon Originals', 'tvshows&url=tmdb_amazonorig', 'tmdb.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Jew Top 250 TV Shows', 'tvshows&url=tmdb_jew250tv', 'tmdb.png', 'DefaultTVShows.png')
        self.endDirectory()


    def movieMosts(self):
        self.addDirectoryItem('Most Played This Week', 'movies&url=trakt_played1', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Played This Month', 'movies&url=trakt_played2', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Played This Year', 'movies&url=trakt_played3', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Played All Time', 'movies&url=trakt_played4', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Collected This Week', 'movies&url=trakt_collected1', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Collected This Month', 'movies&url=trakt_collected2', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Collected This Year', 'movies&url=trakt_collected3', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Collected All Time', 'movies&url=trakt_collected4', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Watched This Week', 'movies&url=trakt_watched1', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Watched This Month', 'movies&url=trakt_watched2', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Watched This Year', 'movies&url=trakt_watched3', 'most-popular.png', 'DefaultMovies.png')
        self.addDirectoryItem('Most Watched All Time', 'movies&url=trakt_watched4', 'most-popular.png', 'DefaultMovies.png')
        self.endDirectory()


    def showMosts(self):
        self.addDirectoryItem('Most Played This Week', 'tvshows&url=trakt_played1', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Played This Month', 'tvshows&url=trakt_played2', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Played This Year', 'tvshows&url=trakt_played3', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Played All Time', 'tvshows&url=trakt_played4', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Collected This Week', 'tvshows&url=trakt_collected1', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Collected This Month', 'tvshows&url=trakt_collected2', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Collected This Year', 'tvshows&url=trakt_collected3', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Collected All Time', 'tvshows&url=trakt_collected4', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Watched This Week', 'tvshows&url=trakt_watched1', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Watched This Month', 'tvshows&url=trakt_watched2', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Watched This Year', 'tvshows&url=trakt_watched3', 'most-popular.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Most Watched All Time', 'tvshows&url=trakt_watched4', 'most-popular.png', 'DefaultTVShows.png')
        self.endDirectory()


    def tvTVmaze(self):
        # Rebuilt for 1.0.2 - all entries now hit api.tvmaze.com (no
        # more HTML scraping) and most are brand new.
        self.addDirectoryItem('Most Popular Shows',          'tvshows&url=tvmaze_popular',           'most-popular.png',     'DefaultTVShows.png')
        self.addDirectoryItem('Premiering Today (US TV)',    'calendar&url=tvmaze_premieres_today',  'new-tvshows.png',      'DefaultRecentlyAddedEpisodes.png')
        self.addDirectoryItem('Streaming Today',             'calendar&url=tvmaze_streaming_today',  'latest-episodes.png',  'DefaultRecentlyAddedEpisodes.png')
        self.addDirectoryItem('New Episodes (US TV)',        'calendar&url=tvmaze_added',            'latest-episodes.png',  'DefaultRecentlyAddedEpisodes.png', queue=True)
        self.addDirectoryItem('TV Calendar (last 30 days)',  'calendars',                            'calendar.png',         'DefaultRecentlyAddedEpisodes.png')
        self.addDirectoryItem('Recently Updated Shows',      'tvshows_tvmaze_updates_menu',          'latest-movies.png',    'DefaultTVShows.png')
        self.addDirectoryItem('Networks',                    'tvshows_tvmaze_networks',              'networks.png',         'DefaultTVShows.png')
        self.addDirectoryItem('Web Channels',                'tvshows_tvmaze_webchannels',           'networks.png',         'DefaultTVShows.png')
        self.addDirectoryItem('Genres',                      'tvshows_tvmaze_genres',                'genres.png',           'DefaultTVShows.png')
        self.addDirectoryItem('Countries',                   'tvshows_tvmaze_countries',             'languages.png',        'DefaultTVShows.png')
        self.endDirectory()


    def tvTVmazeUpdates(self):
        self.addDirectoryItem('Updated in the last day',   'tvshows&url=tvmaze_updates_day',   'latest-movies.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Updated in the last week',  'tvshows&url=tvmaze_updates_week',  'latest-movies.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Updated in the last month', 'tvshows&url=tvmaze_updates_month', 'latest-movies.png', 'DefaultTVShows.png')
        self.endDirectory()


    def mylists(self):
        self.addDirectoryItem('My Trakt', 'my_trakt_menu', 'trakt.png', 'DefaultSets.png')
        self.addDirectoryItem('My TMDb', 'my_tmdb_menu', 'tmdb.png', 'DefaultSets.png')
        self.addDirectoryItem('My Userlists', 'my_userlists_menu', 'userlists.png', 'DefaultSets.png')
        self.addDirectoryItem('My Favorites', 'favoritesNavigator', 'most-popular.png', 'DefaultFolder.png')
        self.addDirectoryItem('My Library', 'library_menu', 'mymovies.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem('My Downloads', 'download_menu', 'downloads.png', 'DefaultFolder.png')
        self.endDirectory()


    def mytrakt(self):
        self.addDirectoryItem('My Trakt Movies', 'my_trakt_movies_menu', 'trakt.png', 'DefaultSets.png')
        self.addDirectoryItem('My Trakt TV Shows', 'my_trakt_tvshows_menu', 'trakt.png', 'DefaultSets.png')
        # "Refresh Trakt Cache" - manual override for the new 5 min
        # short-TTL cache (see modules/trakt_cache.py).  Placed at the
        # bottom of the My Trakt menu so it's visible the moment a user
        # suspects Trakt data is stale (list added / removed upstream)
        # without hunting through the global cache-clear menus.
        # ``isFolder=False`` because it's an action, not navigation.
        self.addDirectoryItem('Refresh Trakt Cache', 'refresh_trakt_cache', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.endDirectory()


    def mytraktmovies(self):
        if traktCredentials == True:
            self.addDirectoryItem('Library', 'movies&url=trakt_collection', 'trakt.png', 'DefaultMovies.png', queue=True, context=('Add to Library', 'movies_to_library&url=trakt_collection'))
            self.addDirectoryItem('Watchlist', 'movies&url=trakt_watchlist', 'trakt.png', 'DefaultMovies.png', queue=True, context=('Add to Library', 'movies_to_library&url=trakt_watchlist'))
            self.addDirectoryItem('Favorites', 'movies&url=trakt_favorites', 'trakt.png', 'DefaultMovies.png', queue=True, context=('Add to Library', 'movies_to_library&url=trakt_favorites'))
        if traktIndicators == True:
            self.addDirectoryItem('In Progress', 'movies&url=trakt_ondeck', 'trakt.png', 'DefaultMovies.png', queue=True)
            self.addDirectoryItem('History', 'movies&url=trakt_history', 'trakt.png', 'DefaultMovies.png', queue=True)
            self.addDirectoryItem('Watched', 'movies&url=trakt_watchedlist', 'trakt.png', 'DefaultMovies.png')
        self.endDirectory()


    def mytrakttvshows(self):
        if traktCredentials == True:
            self.addDirectoryItem('Library', 'tvshows&url=trakt_collection', 'trakt.png', 'DefaultTVShows.png', context=('Add to Library', 'tvshows_to_library&url=trakt_collection'))
            self.addDirectoryItem('Watchlist', 'tvshows&url=trakt_watchlist', 'trakt.png', 'DefaultTVShows.png', context=('Add to Library', 'tvshows_to_library&url=trakt_watchlist'))
            self.addDirectoryItem('Favorites', 'tvshows&url=trakt_favorites', 'trakt.png', 'DefaultTVShows.png', context=('Add to Library', 'tvshows_to_library&url=trakt_favorites'))
        if traktIndicators == True:
            self.addDirectoryItem('Upcoming Episodes', 'calendar&url=trakt_mycalendar', 'trakt.png', 'DefaultRecentlyAddedEpisodes.png', queue=True)
            self.addDirectoryItem('Continue Watching', 'calendar&url=trakt_progress', 'trakt.png', 'DefaultRecentlyAddedEpisodes.png', queue=True)
            self.addDirectoryItem('In Progress Episodes', 'calendar&url=trakt_ondeck', 'trakt.png', 'DefaultTVShows.png')
            self.addDirectoryItem('History', 'calendar&url=trakt_history', 'trakt.png', 'DefaultTVShows.png', queue=True)
            self.addDirectoryItem('Watched', 'tvshows&url=trakt_watchedlist', 'trakt.png', 'DefaultTVShows.png')
        self.endDirectory()


    def mytmdb(self):
        self.addDirectoryItem('My TMDb Movies', 'my_tmdb_movies_menu', 'tmdb.png', 'DefaultSets.png')
        self.addDirectoryItem('My TMDb TV Shows', 'my_tmdb_tvshows_menu', 'tmdb.png', 'DefaultSets.png')
        self.endDirectory()


    def mytmdbmovies(self):
        if tmdbCredentials == True:
            self.addDirectoryItem('Favorites', 'movies&url=tmdb_favorites', 'tmdb.png', 'DefaultMovies.png', queue=True)
            self.addDirectoryItem('Watchlist', 'movies&url=tmdb_watchlist', 'tmdb.png', 'DefaultMovies.png', queue=True)
        self.endDirectory()


    def mytmdbtvshows(self):
        if tmdbCredentials == True:
            self.addDirectoryItem('Favorites', 'tvshows&url=tmdb_favorites', 'tmdb.png', 'DefaultTVShows.png')
            self.addDirectoryItem('Watchlist', 'tvshows&url=tmdb_watchlist', 'tmdb.png', 'DefaultTVShows.png')
        self.endDirectory()


    def myuserlists(self):
        self.addDirectoryItem('Movie UserLists', 'my_userlists_movies_menu', 'mymovies.png', 'DefaultMovies.png')
        self.addDirectoryItem('TV Show UserLists', 'my_userlists_tvshows_menu', 'mytvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Episode UserLists', 'episodes_userlists', 'mytvshows.png', 'DefaultTVShows.png')
        self.endDirectory()


    def myuserlistsmovies(self):
        self.addDirectoryItem('Trakt UserLists', 'movies_userlists_trakt', 'trakt.png', 'DefaultMovies.png')
        self.addDirectoryItem('Trakt Liked UserLists', 'movies_userlists_trakt_liked', 'trakt.png', 'DefaultMovies.png')
        self.addDirectoryItem('TMDb UserLists', 'movies_userlists_tmdb', 'tmdb.png', 'DefaultMovies.png')
        self.endDirectory()


    def myuserliststvshows(self):
        self.addDirectoryItem('Trakt UserLists', 'tvshows_userlists_trakt', 'trakt.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Trakt Liked UserLists', 'tvshows_userlists_trakt_liked', 'trakt.png', 'DefaultTVShows.png')
        self.addDirectoryItem('TMDb UserLists', 'tvshows_userlists_tmdb', 'tmdb.png', 'DefaultTVShows.png')
        self.endDirectory()


    def search_setting_widget(self, the_setting):
        setting = control.setting(the_setting) or '0'
        if setting == '1':
            return 'Trakt'
        else:
            return 'TMDb'


    def search_movies(self):
        movies_setting_label = self.search_setting_widget('search.movies.source')
        self.addDirectoryItem('Movies (%s)' % movies_setting_label, 'movies_search&select=movies', 'search.png', 'DefaultMovies.png')
        self.addDirectoryItem('People (TMDb)', 'movies_search&select=people', 'people-search.png', 'DefaultMovies.png')
        self.addDirectoryItem('Keywords (TMDb)', 'movies_search&select=keywords', 'search.png', 'DefaultMovies.png')
        self.addDirectoryItem('Companies (TMDb)', 'movies_search&select=companies', 'search.png', 'DefaultMovies.png')
        self.addDirectoryItem('Collections (TMDb)', 'movies_search&select=collections', 'search.png', 'DefaultMovies.png')
        self.endDirectory()


    def search_tvshows(self):
        tvshows_setting_label = self.search_setting_widget('search.tvshows.source')
        self.addDirectoryItem('TV Shows (%s)' % tvshows_setting_label, 'tvshows_search&select=tvshow', 'search.png', 'DefaultTVShows.png')
        self.addDirectoryItem('People (TMDb)', 'tvshows_search&select=people', 'people-search.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Keywords (TMDb)', 'tvshows_search&select=keywords', 'search.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Companies (TMDb)', 'tvshows_search&select=companies', 'search.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Collections (TMDb)', 'tvshows_search&select=collections', 'search.png', 'DefaultTVShows.png')
        self.endDirectory()


    def favorites(self):
        self.addDirectoryItem('Movie Favorites', 'movieFavorites', 'highly-rated.png', 'DefaultMovies.png')
        self.addDirectoryItem('TV Show Favorites', 'tvFavorites', 'highly-rated.png', 'DefaultTVShows.png')
        self.endDirectory()


    def library(self):
        movie_library = control.setting('library.movie')
        if len(control.listDir(movie_library)[0]) > 0:
            self.addDirectoryItem('Library Movie Folder', movie_library, 'movies.png', 'DefaultMovies.png', isAction=False)
        tv_library = control.setting('library.tv')
        if len(control.listDir(tv_library)[0]) > 0:
            self.addDirectoryItem('Library TV Show Folder', tv_library, 'tvshows.png', 'DefaultTVShows.png', isAction=False)
        self.addDirectoryItem('Library Settings', 'open_settings&query=6.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Update Library', 'update_library&query=tool', 'library_update.png', 'DefaultAddonProgram.png', isFolder=False)
        if traktCredentials == True:
            self.addDirectoryItem('Import Trakt Movie Collection...', 'movies_to_library&url=trakt_collection', 'trakt.png', 'DefaultMovies.png', isFolder=False)
            self.addDirectoryItem('Import Trakt Movie Watchlist...', 'movies_to_library&url=trakt_watchlist', 'trakt.png', 'DefaultMovies.png', isFolder=False)
            self.addDirectoryItem('Import Trakt TV Show Collection...', 'tvshows_to_library&url=trakt_collection', 'trakt.png', 'DefaultTVShows.png', isFolder=False)
            self.addDirectoryItem('Import Trakt TV Show Watchlist...', 'tvshows_to_library&url=trakt_watchlist', 'trakt.png', 'DefaultTVShows.png', isFolder=False)
        self.endDirectory()


    def downloads(self):
        movie_downloads = control.setting('movie.download.path')
        if len(control.listDir(movie_downloads)[0]) > 0:
            self.addDirectoryItem('Downloads Movie Folder', movie_downloads, 'movies.png', 'DefaultMovies.png', isAction=False)
        tv_downloads = control.setting('tv.download.path')
        if len(control.listDir(tv_downloads)[0]) > 0:
            self.addDirectoryItem('Downloads TV Show Folder', tv_downloads, 'tvshows.png', 'DefaultTVShows.png', isAction=False)
        self.endDirectory()


    def tools(self):
        self.addDirectoryItem('Settings', 'open_settings&query=0.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Cleaning Tools', 'cleantools_menu', 'tools.png', 'DefaultAddonProgram.png')
        #self.addDirectoryItem('Provider Settings', 'open_settings&query=4.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('ResolveURL Settings', 'open_resolveurl_settings', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Setup ViewTypes', 'views_menu', 'tools.png', 'DefaultAddonProgram.png')
        #self.addDirectoryItem('Authorize TMDb', 'auth_tmdb', 'tmdb.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Authorize Trakt', 'auth_trakt', 'trakt.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('[COLOR red]Changelog[/COLOR]', 'changelog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('[COLOR orange]Scrubs v2 Changelog[/COLOR]', 'scrubsv2_changelog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #if control.condVisibility('System.HasAddon(plugin.program.lazylinks)'):
        #    self.addDirectoryItem('Open LazyLinks', 'plugin://plugin.program.lazylinks', 'tools.png', 'DefaultAddonProgram.png', isAction=False)
        self.addDirectoryItem('Optional Installs', 'installs_menu', 'tools.png', 'DefaultAddonProgram.png')
        self.endDirectory()


    def devtools(self):
        #self.addDirectoryItem('Testing', 'testing', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem('In Theatres', 'movies&url=tmdb_in_theatres', 'latest-movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('Test Movies (TMDb)', 'movies&url=tmdb_jewtestmovies', 'movies.png', 'DefaultMovies.png')
        self.addDirectoryItem('Test TV Shows (TMDb)', 'tvshows&url=tmdb_jewtestshows', 'tvshows.png', 'DefaultTVShows.png')
        self.addDirectoryItem('Provider Domains', 'get_provider_domains', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Provider Settings', 'open_settings&query=4.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('View Debug Log', 'view_debuglog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear Debug Log', 'clear_debuglog', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Cleaning Tools', 'cleantools_menu', 'tools.png', 'DefaultAddonProgram.png')
        self.addDirectoryItem('Force Open SideMenu/SlideMenu', 'open_sidemenu', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.endDirectory()


    def cleantools(self):
        self.addDirectoryItem('Clear All Cache', 'clear_all_cache', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear Providers', 'clear_sources', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear Meta Cache', 'clear_meta_cache', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear Cache', 'clear_cache', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear ResolveURL Cache', 'clear_resolveurl_cache', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear All Search Cache', 'clear_search_cache&select=all', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clean Old Settings', 'clean_settings', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.addDirectoryItem('Clear ViewTypes', 'clear_viewtypes', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.endDirectory()


    def cleantools_widget(self):
        try:
            items = [('[B]Clear All Cache[/B]', 'clear_all_cache')]
            items += [('[B]Clear Providers[/B]', 'clear_sources')]
            items += [('[B]Clear Meta Cache[/B]', 'clear_meta_cache')]
            items += [('[B]Clear Cache[/B]', 'clear_cache')]
            items += [('[B]Clear ResolveURL Cache[/B]', 'clear_resolveurl_cache')]
            items += [('[B]Clear All Search Cache[/B]', 'clear_search_cache&select=all')]
            items += [('[B]Clean Old Settings[/B]', 'clean_settings')]
            items += [('[B]Clear ViewTypes[/B]', 'clear_viewtypes')]
            if not control.setting('addon.debug') == 'false':
                items += [('[B]Clear Debug Log[/B]', 'clear_debuglog')]
                items += [('[B]View Debug Log[/B]', 'view_debuglog')]
            select = control.selectDialog([i[0] for i in items], 'Cleaning Tools')
            if select == -1:
                return
            control.execute('RunPlugin(%s?action=%s)' % (sysaddon, items[select][1]))
        except:
            return


    def installsmenu(self):
        #if not control.condVisibility('System.HasAddon(plugin.program.lazylinks)'):
        #    self.addDirectoryItem('plugin.program.lazylinks - Install Addon', 'installAddon&id=plugin.program.lazylinks', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #else:
        #    self.addDirectoryItem('plugin.program.lazylinks - Open Addon', 'plugin://plugin.program.lazylinks', 'tools.png', 'DefaultAddonProgram.png', isAction=False)
        #if not control.condVisibility('System.HasAddon(script.gratisred.artwork)'):
        #    self.addDirectoryItem('script.gratisred.artwork - Install Addon', 'installAddon&id=script.gratisred.artwork', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #else:
        #    self.addDirectoryItem('script.gratisred.artwork - Open Settings', 'open_settings&query=0.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        if not control.condVisibility('System.HasAddon(script.trakt)'):
            self.addDirectoryItem('script.trakt - Install Addon', 'installAddon&id=script.trakt', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        else:
            self.addDirectoryItem('script.trakt - Open Settings', 'open_settings&id=script.trakt', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        if not control.condVisibility('System.HasAddon(plugin.video.youtube)'):
            self.addDirectoryItem('plugin.video.youtube - Install Addon', 'installAddon&id=plugin.video.youtube', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        else:
            self.addDirectoryItem('plugin.video.youtube - Open Settings', 'open_settings&id=plugin.video.youtube', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #if not control.condVisibility('System.HasAddon(plugin.video.json_iptv)'):
        #    self.addDirectoryItem('plugin.video.json_iptv - Install Addon', 'installAddon&id=plugin.video.json_iptv', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        #else:
        #    self.addDirectoryItem('plugin.video.json_iptv - Open Settings', 'open_settings&id=plugin.video.json_iptv', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        if not control.condVisibility('System.HasAddon(service.subtitles.a4ksubtitles)'):
            self.addDirectoryItem('service.subtitles.a4ksubtitles - Install Addon', 'installAddon&id=service.subtitles.a4ksubtitles', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        else:
            self.addDirectoryItem('service.subtitles.a4ksubtitles - Open Settings', 'open_settings&id=service.subtitles.a4ksubtitles', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
        self.endDirectory()


    def views(self):
        try:
            items = [('Movies', 'movies')]
            items += [('TV Shows', 'tvshows')]
            items += [('Seasons', 'seasons')]
            items += [('Episodes', 'episodes')]
            select = control.selectDialog([i[0] for i in items], 'Setup ViewTypes')
            if select == -1:
                return
            content = items[select][1]
            title = 'Click Here To Save View'
            url = '%s?action=add_view&content=%s' % (sysaddon, content)
            poster = control.addonPoster()
            banner = control.addonBanner()
            fanart = control.addonFanart()
            #item = control.item(label=title) # Could probably swap it all back and remove the kodi_v20 changes as none of this seems to give any issues or errors.
            ##New Starts
            try:
                item = control.item(label=title, offscreen=True)
            except:
                item = control.item(label=title)
            ##New Ends
            item.setArt({'icon': poster, 'thumb': poster, 'poster': poster, 'banner': banner})
            item.setProperty('Fanart_Image', fanart)
            ##New Starts
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': title})
            else:
                item.setInfo(type='Video', infoLabels={'title': title})
            ##New Ends
            #item.setInfo(type='Video', infoLabels={'title': title}) # Seems to be a useless line of code lol. (been commented out since before the kodi_v20 changes.)
            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
            ## Added in to help those to disable the TopBar lol.
            self.addDirectoryItem('Force Open SideMenu/SlideMenu', 'open_sidemenu', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
            control.content(syshandle, content)
            control.directory(syshandle, cacheToDisc=True)
            from resources.lib.modules import views
            views.setView(content, {})
        except:
            return


    def clearCache(self):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clear Cache?')
        if not yes:
            return
        cache.cache_clear()
        control.infoDialog('Cache Cleared.', sound=True, icon='INFO')


    def clearCacheMeta(self):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clear Meta Cache?')
        if not yes:
            return
        cache.cache_clear_meta()
        control.infoDialog('Meta Cache Cleared.', sound=True, icon='INFO')


    def clearCacheProviders(self):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clear Providers Cache?')
        if not yes:
            return
        cache.cache_clear_providers()
        control.infoDialog('Providers Cache Cleared.', sound=True, icon='INFO')


    def clearCacheSearch(self, select):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clear All Search Cache?')
        if not yes:
            return
        cache.cache_clear_search(select)
        control.infoDialog('All Search Cache Cleared.', sound=True, icon='INFO')


    def clearCacheAll(self):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clear All Cache?')
        if not yes:
            return
        cache.cache_clear_all()
        control.infoDialog('All Cache Cleared.', sound=True, icon='INFO')


    def refreshTraktCache(self):
        # Bound to the "Refresh Trakt Cache" menu entry inside My Trakt.
        # Only drops the dedicated ``trakt_cache`` table (see
        # modules/trakt_cache.py) so the 12h TMDb / meta caches stay
        # intact - fast and non-destructive.  No confirm dialog: this is
        # an everyday convenience, not a dangerous operation.
        from resources.lib.modules import trakt_cache
        if trakt_cache.clear():
            control.infoDialog('Trakt Cache Refreshed.', sound=True, icon='INFO')
            control.refresh()
        else:
            control.infoDialog('Trakt Cache Refresh Failed.', sound=True, icon='ERROR')


    def cleanSettings(self):
        from resources.lib.modules import cache
        yes = control.yesnoDialog('Clean Old Settings?')
        if not yes:
            return
        cache.clean_settings()
        control.infoDialog('Old Settings Cleaned.', sound=True, icon='INFO')


    def clearDebugLog(self):
        yes = control.yesnoDialog('Clear Debug Log?')
        if not yes:
            return
        log_utils.empty_log()
        control.infoDialog('Debug Log Cleared.', sound=True, icon='INFO')


    def clearViewTypes(self):
        from resources.lib.modules import views
        yes = control.yesnoDialog('Clear All ViewTypes?')
        if not yes:
            return
        views.deleteView()
        control.infoDialog('All ViewTypes Cleared.', sound=True, icon='INFO')


    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        artPath = control.artPath()
        fanart = control.addonFanart()
        thumb = os.path.join(artPath, thumb) if not (artPath == None or thumb == None) else icon
        cm = []
        cm.append(('[B]View Changelog[/B]', 'RunPlugin(%s?action=view_changelog)' % sysaddon))
        cm.append(('[B]Clean Tools Widget[/B]', 'RunPlugin(%s?action=cleantools_widget)' % sysaddon))
        if queue == True:
            cm.append(('Queue Item', 'RunPlugin(%s?action=queue_item)' % sysaddon))
        if not context == None:
            cm.append((context[0], 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        try:
            item = control.item(label=name, offscreen=True)
        except:
            item = control.item(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'fanart': fanart})
        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def addDirectory(self, items, queue=False, isFolder=True):
        if items == None or len(items) == 0:
            control.idle()
            #sys.exit()
        sysfanart = control.addonFanart()
        for i in items:
            try:
                url = '%s?action=%s&url=%s' % (sysaddon, i['action'], i['url'])
                title = i['title']
                icon = i['image'] if 'image' in i and not i['image'] == (None or 'None' or '0') else 'DefaultVideo.png'
                fanart = i['fanart'] if 'fanart' in i and not i['fanart'] == (None or 'None' or '0') else sysfanart
                try:
                    item = control.item(label=title, offscreen=True)
                except:
                    item = control.item(label=title)
                item.setProperty('IsPlayable', 'true')
                item.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
            except Exception:
                #log_utils.log('addDirectory', 1)
                pass
        self.endDirectory()


    def endDirectory(self, cached=True):
        control.content(syshandle, 'addons')
        control.directory(syshandle, cacheToDisc=cached)


