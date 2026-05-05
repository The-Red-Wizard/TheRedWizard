# -*- coding: utf-8 -*-

import re

from six.moves.urllib_parse import quote_plus

from resources.lib.indexers import navigator
from resources.lib.indexers import movies

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import workers

#control.moderator()


class listings:
    def __init__(self):
        self.list = []
        self.items = []
        self.stations_link = 'https://www.tvpassport.com/tv-listings/stations/%s'
        self.movies_today_link = 'https://www.tvpassport.com/tv-listings/movies'
        self.logo_image_link = 'https://www.tvpassport.com/resource/img/'
        self.base_image_link = 'https://repo.redwizard.xyz/images/gratis.red/tvpassport.channels/'
        self.channels_list = [
            ('Movies on TV Today Highlights', 'self.movies_today_link', 'tv-passport-logo.png'),
            ('AMC', 'amc-eastern-feed/177$$$amc/35317', 's10021_h15_ab.png'),
            ('B4U Movies', 'b4u-movies-north-america/4006', 's25529_h9_ab.png'),
            ('BBC America', 'bbc-america-east/615', 's18332_h15_aa.jpg'),
            ('BET', 'bet-eastern-feed/323$$$bet-her/6837', 's10051_h15_ad.jpg'),
            ('Bounce', 'bounce-network/14312', 's73067_h15_ab.png'),
            #('Bravo', 'bravo-usa-eastern-feed646$$$bravo-canada/160', 's17610_h15_ag.png'),
            ('BYU', 'byu-brigham-young-university/3332', 's21855_h15_ab.jpg'),
            ('Cine Estelar', 'cine-estelar/6830', 's62125_h15_aa.jpg'),
            ('Cine Latino', 'cinelatino-usa/3081', 's15296_h9_ab.jpg'),
            ('Cine Mexicano', 'cine-mexicano/4469', 's44714_h15_aa.png'),
            ('Cinemax', 'cinemax-eastern-feed/632$$$cinemax-pacific-feed/1215', 's10120_h15_ab.jpg'),
            ('Cinemax Action', 'cinemax-action-eastern/1377', '18433-9002.jpg'),
            ('Cinemax Classics', 'cinemax-classics-eastern/636', '25620-C828.jpg'),
            ('Cinemax Hits', 'cinemax-hits-eastern/634', '10121-4F12.jpg'),
            ('Cinemax Spanish', 'cinemax-spanish/9962', 's25623_h15_ad.jpg'),
            #('CLEO TV', 'cleo-tv/33138', 's110288_h15_aa.jpg'),
            ('CMT', 'cmt-us-eastern-feed/1076', 's10138_h15_ab.jpg'),
            #('Comedy Central', 'comedy-central-us-eastern-feed/647', 's10149_h15_ab.jpg'),
            #('Comet TV', 'comet-tv/16811', 's97051_h15_ab.png'),
            ('Crave1-4', 'crave1-east/72$$$crave2-east/86$$$crave3-east/85$$$crave4/320', 's10191_h15_ab.jpg'),
            ('De Pelicula', 'de-pelicula/4419$$$de-pelicula-clasico/4420', 's16288_h15_ac.jpg'),
            #('Defy (KAJR-LD) Des Moines', 'defy-kajrld-des-moines-ia/26055', 's159206_h15_aa.jpg'),
            #('Disney', 'disney-eastern-feed/595$$$disney-pacific-feed/1271', 's10171_h15_ae.png'),
            #('Disney Junior', 'disney-junior-usa-east/6867', 's74796_h15_ad.png'),
            #('Disney XD', 'disney-xd-usa-eastern-feed/1053', 's18279_h15_aa.png'),
            #('Documentary Channel', 'documentary-channel-canada/462', 's26784_h15_aa.jpg'),
            ('E! Entertainment', 'e-entertainment-usa-eastern-feed/617', 's10989_h15_aa.jpg'),
            ('El Rey Network', 'el-rey-network/11399', 's124328_h15_ab.jpg'),
            ('ELLE Fictions', 'elle-fictions/101', 's15675_h9_ac.png'),
            ('FLIX', 'flix-eastern/1399', 's10201_h15_aa.jpg'),
            ('FMC Family Movie Classics', 'fmc-family-movie-classics/36900', 's122068_h15_aa.jpg'),
            ('Freeform', 'freeform-east-feed/1011', 's10093_h15_ae.png'),
            ('FUSE TV', 'fuse-tv-eastern-feed/1486', 's14929_h15_ac.jpg'),
            ('FX', 'fx-networks-east-coast/652', 's14321_h15_aa.jpg'),
            ('FX Movie Channel', 'fx-movie-channel/1308', 's70253_h15_aa.jpg'),
            ('FXX', 'fxx-usa-eastern/1952', 's17927_h15_aa.jpg'),
            ('GAC Family', 'gac-family-east/1051', 's16062_h15_ad.jpg'),
            ('Grit', 'grit-network/14377', '89922-2BE84.jpg'),
            ('Hallmark', 'hallmark-eastern-feed/1052', 's11221_h15_aa.jpg'),
            #('Hallmark Mystery', 'hallmark-mystery-eastern/4453', 's61522_h15_ab.jpg'),
            ('HBO', 'hbo-eastern-feed/614$$$hbo-pacific-feed/1472', 's10240_h15_aa.jpg'),
            ('HBO 1', 'hbo1/84', 's61557_h15_ab.jpg'),
            ('HBO Comedy', 'hbo-comedy-east/629', 's18429_h15_aa.jpg'),
            ('HBO Drama', 'hbo-drama-hbo-3-eastern/1651', '10243-5006.jpg'),
            ('HBO Hits', 'hbo-hits-eastern-feed/626$$$hbo-hits-pacific-feed/2205', '10241-5002.jpg'),
            ('HBO Latino', 'hbo-latino-hbo-7-eastern/631', 's24553_h9_ab.jpg'),
            ('HBO Movies', 'hbo-movies-east/630', '18431-8FFE.jpg'),
            ('HDNet Movies', 'hdnet-movies/4267', 's33668_h15_ae.jpg'),
            ('Hollywood Suite 2100s+', 'hollywood-suite-2010s/8887', '73578-23ED4.jpg'),
            #('ICI (CBFT)', 'ici-cbft-montreal-qc/196', 's16371_h15_ae.png'),
            #('Independent Film Channel', 'independent-film-channel-us/1966', 's14873_h15_ac.jpg'),
            ('INDIEplex', 'indieplex-eastern/2340', 's49751_h15_ab.jpg'),
            #('INSP', 'insp/1082', 's11066_h15_ac.jpg'),
            ('IVC Network', 'ivc-network-international/18867', 's97002_h15_aa.jpg'),
            #('Laff', 'laff-network/20169', '92091-2CF76.png'),
            ('Lifetime', 'lifetime-network-us-eastern-feed/654$$$lifetime-tv-canada/1148', 's10918_h15_ac.png'),
            ('Lifetime Movies', 'lifetime-movies-east/1333', 's18480_h15_ad.jpg'),
            #('Link TV', 'link-tv/3750', 's21450_h15_aa.png'),
            ('MAX', 'max/306', 's17591_h15_aa.jpg'),
            #('MGM', 'mgm-hd-usa/6107', 's58530_h15_aa.jpg'),
            ('MGM+', 'mgm-east/7609', 's65669_h15_ae.png'),
            ('MGM+ Drive-In', 'mgm-drivein/11487', 's68409_h15_ad.png'),
            ('MGM+ Hits', 'mgm-hits-east/11485', 's73075_h15_ad.png'),
            ('MGM+ Marquee', 'mgm-marquee/11486', 's74320_h15_ac.png'),
            ('MOVIEplex', 'movieplex-eastern/1066', 's15295_h15_aa.jpg'),
            ('MovieTime', 'movietime/464', 's27125_h15_aa.png'),
            #('OuterMax', 'outermax-eastern/2270', 's25622_h15_ab.jpg'),
            ('Paramount Network', 'paramount-network-usa-eastern-feed/1030', 's11163_h15_ac.jpg'),
            ('Paramount+ With Showtime', 'paramount-with-showtime-eastern-feed/665$$$paramount-with-showtime-west/10734', 's11115_h15_ad.jpg'),
            ('RETROplex', 'retroplex-eastern/2342', 's49767_h15_aa.jpg'),
            ('Rewind', 'rewind/1149', 's27126_h15_aa.jpg'),
            #('Showcase', 'showcase-canada/62', 's53711_h15_aa.jpg'),
            ('Showtime 2', 'showtime-2-eastern/1387', 's11116_h15_aa.png'),
            ('Showtime Extreme', 'showtime-extreme-eastern/1615', 's18086_h15_aa.jpg'),
            ('Showtime Family Zone', 'showtime-family-zone-eastern/1956', 's25274_h15_ac.jpg'),
            ('Showtime Next', 'showtime-next-eastern/2272', 's25270_h15_ac.jpg'),
            ('Showtime Showcase', 'showtime-showcase-eastern/2271', 's16153_h15_aa.png'),
            ('Showtime Women', 'showtime-women-eastern/2273', 's25272_h15_ac.jpg'),
            ('SHOxBET', 'shoxbet-eastern/2077', 's20622_h15_ad.jpg'),
            ('Silver Screen Classics', 'silver-screen-classics/2115', 's34290_h15_aa.png'),
            ('Slice', 'slice/60', 's15181_h15_ab.jpg'),
            ('Sony Cine', 'sony-cine/10967', 's109720_h15_aa.png'),
            ('Sony Movies', 'sony-movies/17063', 's69091_h15_ab.png'),
            ('Starz', 'starz-eastern/583$$$starz-pacific/1217', 's12719_h15_ac.png'),
            ('Starz1', 'starz1-east/55', 's14947_h15_ae.jpg'),
            ('Starz Cinema', 'starz-cinema-eastern/2680', 's19634_h15_ac.jpg'),
            ('Starz Comedy', 'starz-comedy-eastern/4223', 's34901_h15_ac.jpg'),
            ('Starz Edge', 'starz-edge-eastern/2120', 's16311_h15_ab.jpg'),
            ('Starz Encore', 'starz-encore-eastern/667$$$starz-encore-pacific/1218', 's10178_h15_ac.jpg'),
            ('Starz Encore Action', 'starz-encore-action-eastern/2078', 's14871_h15_ab.jpg'),
            ('Starz Encore Black', 'starz-encore-black-eastern/4206', 's14870_h15_ac.jpg'),
            ('Starz Encore Classic', 'starz-encore-classic-eastern/2080', 's14764_h15_ac.jpg'),
            ('Starz Encore Family', 'starz-encore-family-eastern/2128', 's14886_h15_ab.jpg'),
            ('Starz Encore Suspense', 'starz-encore-suspense-eastern/1958', 's14766_h15_ab.jpg'),
            ('Starz Encore Westerns', 'starz-encore-westerns-eastern/1959', 's14765_h15_ac.jpg'),
            ('Starz In Black', 'starz-in-black-eastern/1957', 's16833_h15_ac.jpg'),
            ('Starz Kids & Family', 'starz-kids-family-eastern/1194', 's19635_h15_ab.jpg'),
            #('Sun TV Tamil', 'sun-tv-tamil/13642', 's31634_h15_aa.png'),
            ('Super Channel Fuse', 'super-channel-fuse/4833', 's58870_h15_ab.png'),
            ('Super Channel Heart & Home', 'super-channel-heart-home/4834', 's58889_h15_ab.png'),
            ('Super Channel Vault', 'super-channel-vault/4835', 's58884_h15_ac.png'),
            ('Syfy', 'syfy-eastern-feed/596', 's11097_h15_ae.png'),
            ('TMC', 'tmc-us-eastern-feed/666$$$tmc-us-pacific-feed/1222', 's11160_h15_aa.jpg'),
            ('TMC Xtra', 'tmc-xtra-eastern/4350$$$tmc-xtra-pacific/4351', 's17663_h15_aa.jpg'),
            ('TNT', 'tnt-eastern-feed/347', 's11164_h15_ac.jpg'),
            ('Turner Classic Movies', 'turner-classic-movies-usa/176$$$turner-classic-movies-canada/2847', 's12852_h15_ab.jpg'),
            #('TV Asia', 'tv-asia-canadian-feed/14212', 's76773_h9_ac.jpg'),
            ('TVA', 'tva-cftm-montreal/106', 's16367_h15_ab.png'),
            ('ViendoMovies', 'viendomovies/4470', 's52208_h15_aa.png'),
            #('Vision TV', 'vision-tv-eastern/17', 's11220_h15_ab.png'),
            ('W (WTN)', 'w-wtn-east/64', 's15024_h15_ab.png')#,
            #('YTV', 'ytv-youth-television-east/15', 's12045_h9_ab.png')
        ]


    def root(self):
        try:
            for i in self.channels_list:
                if i[0] == 'Movies on TV Today Highlights':
                    action = 'tvpassport_movies_today_list'
                    image = self.logo_image_link + i[2]
                else:
                    action = 'tvpassport_stations_movies_list'
                    image = self.base_image_link + i[2]
                self.list.append({'title': client_utils.replaceHTMLCodes(i[0]), 'url': i[1], 'image': image, 'action': action})
            navigator.navigator().addDirectory(self.list)
            return self.list
        except Exception:
            return self.list


    def movies_items_list(self, i):
        try:
            query = '%s&year=%s' % (quote_plus(i[0]), i[1])
            url = movies.movies().tmdb_search_link % query
            item = movies.movies().get(url, create_directory=False)[0]
            self.list.append(item)
        except Exception:
            pass


    def stations_items_list(self, u):
        try:
            link = self.stations_link % u
            results = client.scrapePage(link, timeout='30').text
            results = re.findall(r'<strong>.+?">(.+?)</a> [(](\d{4})[)]</strong>', results)
            for result_t, result_y in results:
                try:
                    title = client_utils.replaceHTMLCodes(result_t)
                    year = result_y
                    check = (title, year)
                    if check in self.items:
                        continue
                    self.items.append((title, year))
                except:
                    pass
        except Exception:
            pass


    def stations_movies_list(self, url):
        try:
            threadsA = []
            if '$$$' in url:
                url = url.split('$$$')
                for u in url:
                    threadsA.append(workers.Thread(self.stations_items_list, u))
            else:
                threadsA.append(workers.Thread(self.stations_items_list, url))
            [i.start() for i in threadsA]
            [i.join() for i in threadsA]
            threadsB = []
            for i in range(0, len(self.items)):
                threadsB.append(workers.Thread(self.movies_items_list, self.items[i]))
            [i.start() for i in threadsB]
            [i.join() for i in threadsB]
            movies.movies().movieDirectory(self.list)
            return self.list
        except Exception:
            return self.list


    def movies_today_list(self, url):
        try:
            html = client.scrapePage(self.movies_today_link, timeout='30').text
            results = client_utils.parseDOM(html, 'h2', attrs={'class': 'h4'})
            results = [(client_utils.parseDOM(i, 'a'), client_utils.parseDOM(i, 'small')) for i in results]
            results = [(i[0][0], i[1][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0]
            for result in results:
                try:
                    title = result[0]
                    title = client_utils.replaceHTMLCodes(title)
                    year = result[1]
                    check = (title, year)
                    if check in self.items:
                        continue
                    self.items.append((title, year))
                except:
                    pass
            threads = []
            for i in range(0, len(self.items)):
                threads.append(workers.Thread(self.movies_items_list, self.items[i]))
            [i.start() for i in threads]
            [i.join() for i in threads]
            movies.movies().movieDirectory(self.list)
            return self.list
        except Exception:
            return self.list


