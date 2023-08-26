#TODO: Move to JSON config file and let it be user provided
INDEXER_SPECS = {
    'aither': {
        'name': 'aither',
        'urls': ['aither.cc'],
        'required_seed_ratio': 0,
        'required_seed_days': 5.5,
    },
    'alpharatio': {
        'name': 'alpharatio',
        'urls': ['alpharatio.cc'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 7.5,
    },
    'animetorrents.me': {
        'name': 'animetorrents',
        'urls': ['animetorrents.me'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    'animez': {
        'name': 'animez',
        'urls': ['animez.to', 'animetorrents.me'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 1.5,
    },
    'anthelion': {
        'name': 'anthelion',
        'urls': ['anthelion.me'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    'avistaz': {
        'name': 'avistaz',
        'urls': ['avistaz.to'],
        'required_seed_ratio': 1.0,
        'required_seed_days': 10.5,
    },
    'beyond-hd': {
        'name': 'beyond-hd',
        'urls': ['beyond-hd.me'],
        'required_seed_ratio': 0,
        'required_seed_days': 30.5,
    },
    'blutopia': {
        'name': 'blutopia',
        'urls': ['blutopia.cc', 'blutopia.xyz'],
        'required_seed_ratio': 0,
        'required_seed_days': 7.5,
    },
    'broadcasthenet': {
        'name': 'broadcasthenet',
        'urls': ['landof.tv'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 5.5,
    },
    'cinemaz': {
        'name': 'cinemaz',
        'urls': ['cinemaz.to'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'divteam': {
        'name': 'divteam',
        'urls': ['divteam.com'],
        'required_seed_ratio': 0,
        'required_seed_days': 2.5,
    },
    'exoticaz': {
        'name': 'exoticaz',
        'urls': ['exoticaz.to'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'filelist': {
        'name': 'filelist',
        'urls': ['filelist.io', 'flro.org'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 2.5,
    },
    'hd-olimpo': {
        'name': 'hd-olimpo',
        'urls': ['hd-olimpo.club'],
        'required_seed_ratio': 0,
        'required_seed_days': 3.5,
    },
    'hd-space': {
        'name': 'hd-space',
        'urls': ['hd-space.pw'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'hd-torrents': {
        'name': 'hd-torrents',
        'urls': ['hdts-announce.ru'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'iptorrents': {
        'name': 'iptorrents',
        'urls': ['bgp.technology', 'empirehost.me', 'stackoverflow.tech'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 14.5,
    },
    'karagarga': {
        'name': 'karagarga',
        'urls': ['karagarga.in'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    'kraytracker': {
        'name': 'kraytracker',
        'urls': ['kraytracker.com'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 2.5,
    },
    'morethantv': {
        'name': 'morethantv',
        'urls': ['morethantv.me'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 7.5,
    },
    'myanonamouse': {
        'name': 'myanonamouse',
        'urls': ['myanonamouse.net'],
        'required_seed_ratio': 0,
        'required_seed_days': 3.5,
    },
    'myspleen': {
        'name': 'myspleen',
        'urls': ['myspleen.org'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    'orpheus': {
        'name': 'orpheus',
        'urls': ['home.opsfet.ch'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    # TODO: Discover seeding requirements
    'passthepopcorn': {
        'name': 'passthepopcorn',
        'urls': ['passthepopcorn.me'],
        'required_seed_ratio': 0,
        'required_seed_days': 0,
    },
    'privatehd': {
        'name': 'privatehd',
        'urls': ['privatehd.to'],
        'required_seed_ratio': 1.0,
        'required_seed_days': 10.5,
    },
    'redbits': {
        'name': 'redbits',
        'urls': ['redbits.xyz'],
        'required_seed_ratio': 0,
        'required_seed_days': 4.5,
    },
    'redacted': {
        'name': 'redacted',
        'urls': ['flacsfor.me'],
        'required_seed_ratio': 1.05, # Only site ratio
        'required_seed_days': 0,
    },
    'scenetime': {
        'name': 'scenetime',
        'urls': ['scenetime.com'],
        'required_seed_ratio': 0,
        'required_seed_days': 3.5,
    },
    'torrentday': {
        'name': 'torrentday',
        'urls': ['jumbohostpro.eu', 'td-peers.com'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 3.5,
    },
    'torrentland': {
        'name': 'torrentland',
        'urls': ['torrentland.li'],
        'required_seed_ratio': 0,
        'required_seed_days': 4.5,
    },
    'torrentleech': {
        'name': 'torrentleech',
        'urls': ['tleechreload.org', 'torrentleech.org'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'torrentseeds': {
        'name': 'torrentseeds',
        'urls': ['torrentseeds.org'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 5.5,
    },
    'xbytesv2': {
        'name': 'xbytesv2',
        'urls': ['xbytesv2.li'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 3.5,
    },
    'uhdbits': {
        'name': 'uhdbits',
        'urls': ['uhdbits.org'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 7.5,
    },
}

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while size > power:
        size /= power
        n += 1
    formatted = round(size, 2)
    return f"{formatted} {power_labels[n]}"

def filter_tracker_by_domain(domain):
    for _, specs in INDEXER_SPECS.items():
        if any(domain in url for url in specs['urls']):
            return specs
    return None

def seconds(days: int) -> int:
    seconds_in_a_day = 86400
    seconds = days * seconds_in_a_day
    return seconds

def days(seconds: int) -> int:
    seconds_in_a_day = 86400
    days = seconds / seconds_in_a_day
    return days

def dhms(total_seconds: int) -> str:
    seconds = total_seconds % 60
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60
    days = total_hours // 24
    hours = total_hours % 24
    return f"{days}d{hours}h{minutes}m{seconds}s"
