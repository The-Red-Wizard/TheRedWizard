# -*- coding: utf-8 -*-
#
# Curated list of popular TVmaze networks and web channels.
# Source: https://api.tvmaze.com/networks  &  /webchannels
#
# Each entry is (Display Name, "/?network=<id>" / "/?webchannel=<id>").
# The "/?network=" / "/?webchannel=" prefix is appended to
# tvshows.tvmaze_link  ("https://api.tvmaze.com")  so it ends up as a
# URL the new API-based  tvmaze_list()  can recognise and filter on.
#
# The list is intentionally hand-picked (popular English-language outlets)
# rather than the full ~3000-entry dump from TVmaze - we want a usable,
# scrollable directory, not a 5-minute load.
#
# v1.0.4 - All network/webchannel IDs verified against the live TVmaze
# API.  Previously many IDs were simply wrong (e.g. FX was pointed at
# Cinemax, BBC Two at FX, FXX at ITV1, Channel 4 at BBC America, etc.)
# which is why several "Networks" entries opened either empty or showing
# the wrong network's shows.

# Traditional TV networks
networks = [
    ('ABC (US)',                        '/shows?page=0&network=3'),
    ('AMC (US)',                        '/shows?page=0&network=20'),
    ('A&E (US)',                        '/shows?page=0&network=29'),
    ('Adult Swim (US)',                 '/shows?page=0&network=10'),
    ('BBC America (US)',                '/shows?page=0&network=15'),
    ('BBC One (GB)',                    '/shows?page=0&network=12'),
    ('BBC Two (GB)',                    '/shows?page=0&network=37'),
    ('BBC Three (GB)',                  '/shows?page=0&network=49'),
    ('BBC Four (GB)',                   '/shows?page=0&network=51'),
    ('CBS (US)',                        '/shows?page=0&network=2'),
    ('Channel 4 (GB)',                  '/shows?page=0&network=45'),
    ('Cinemax (US)',                    '/shows?page=0&network=19'),
    ('Comedy Central (US)',             '/shows?page=0&network=23'),
    ('Discovery (US)',                  '/shows?page=0&network=66'),
    ('Disney Channel (US)',             '/shows?page=0&network=78'),
    ('Disney XD (US)',                  '/shows?page=0&network=25'),
    ('FOX (US)',                        '/shows?page=0&network=4'),
    ('FX (US)',                         '/shows?page=0&network=13'),
    ('FXX (US)',                        '/shows?page=0&network=47'),
    ('Freeform (US)',                   '/shows?page=0&network=26'),
    ('HBO (US)',                        '/shows?page=0&network=8'),
    ('History (US)',                    '/shows?page=0&network=53'),
    ('ITV1 (GB)',                       '/shows?page=0&network=35'),
    ('ITV2 (GB)',                       '/shows?page=0&network=54'),
    ('ITV4 (GB)',                       '/shows?page=0&network=310'),
    ('Lifetime (US)',                   '/shows?page=0&network=18'),
    ('MTV (US)',                        '/shows?page=0&network=22'),
    ('NBC (US)',                        '/shows?page=0&network=1'),
    ('National Geographic (US)',        '/shows?page=0&network=42'),
    ('Nickelodeon (US)',                '/shows?page=0&network=27'),
    ('PBS (US)',                        '/shows?page=0&network=85'),
    ('Paramount+ with Showtime (US)',   '/shows?page=0&network=9'),
    ('STARZ (US)',                      '/shows?page=0&network=17'),
    ('Sky Atlantic (GB)',               '/shows?page=0&network=113'),
    ('SundanceTV (US)',                 '/shows?page=0&network=33'),
    ('Syfy (US)',                       '/shows?page=0&network=16'),
    ('TBS (US)',                        '/shows?page=0&network=32'),
    ('TLC (US)',                        '/shows?page=0&network=80'),
    ('TNT (US)',                        '/shows?page=0&network=14'),
    ('The CW (US)',                     '/shows?page=0&network=5'),
    ('USA Network (US)',                '/shows?page=0&network=30'),
    ('VH1 (US)',                        '/shows?page=0&network=55'),
]

# Streaming / web channels
webchannels = [
    ('Acorn TV',                        '/shows?page=0&webchannel=129'),
    ('Amazon Freevee',                  '/shows?page=0&webchannel=251'),
    ('Apple TV+',                       '/shows?page=0&webchannel=310'),
    ('BBC iPlayer',                     '/shows?page=0&webchannel=26'),
    ('BritBox',                         '/shows?page=0&webchannel=269'),
    ('CW Seed',                         '/shows?page=0&webchannel=13'),
    ('Crackle',                         '/shows?page=0&webchannel=4'),
    ('Crunchyroll',                     '/shows?page=0&webchannel=20'),
    ('DC Universe',                     '/shows?page=0&webchannel=187'),
    ('Disney+',                         '/shows?page=0&webchannel=287'),
    ('Funimation',                      '/shows?page=0&webchannel=89'),
    ('HBO Go',                          '/shows?page=0&webchannel=22'),
    ('HBO Max',                         '/shows?page=0&webchannel=329'),
    ('Hulu',                            '/shows?page=0&webchannel=2'),
    ('Netflix',                         '/shows?page=0&webchannel=1'),
    ('Paramount+',                      '/shows?page=0&webchannel=107'),
    ('Peacock',                         '/shows?page=0&webchannel=347'),
    ('Prime Video',                     '/shows?page=0&webchannel=3'),
    ('Quibi',                           '/shows?page=0&webchannel=325'),
    ('Shudder',                         '/shows?page=0&webchannel=213'),
    ('Stan',                            '/shows?page=0&webchannel=64'),
    ('Tubi',                            '/shows?page=0&webchannel=401'),
    ('YouTube',                         '/shows?page=0&webchannel=21'),
    ('discovery+',                      '/shows?page=0&webchannel=173'),
]
