#!/usr/bin/env python3

import tldextract

import qbittools

INDEXER_SPECS = {
    'animez': {
        'name': 'animez',
        'urls': ['animez.to', 'animetorrents.me'],
        'required_seed_ratio': 1.0,
        'required_seed_days': 1.0,
    },
    'avistaz': {
        'name': 'avistaz',
        'urls': ['avistaz.to'],
        'required_seed_ratio': 1.0,
        'required_seed_days': 10.5,
    },
    'blutopia': {
        'name': 'blutopia',
        'urls': ['blutopia.cc', 'blutopia.xyz'],
        'required_seed_ratio': 0,
        'required_seed_days': 7.5,
    },
    'cinemaz': {
        'name': 'cinemaz',
        'urls': ['cinemaz.to'],
        'required_seed_ratio': 1.0,
        'required_seed_days': 10.5,
    },
    'divteam': {
        'name': 'divteam',
        'urls': ['divteam.com'],
        'required_seed_ratio': 0,
        'required_seed_days': 2.0,
    },
    'exoticaz': {
        'name': 'exoticaz',
        'urls': ['exoticaz.to'],
        'required_seed_ratio': 1.0,
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
        'urls': ['hd-space.club'],
        'required_seed_ratio': 0,
        'required_seed_days': 3.0,
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
        'required_seed_days': 4.0,
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
    'torrentleech': {
        'name': 'torrentleech',
        'urls': ['tleechreload.org', 'torrentleech.org'],
        'required_seed_ratio': 1.05,
        'required_seed_days': 10.5,
    },
    'torrentland': {
        'name': 'torrentland',
        'urls': ['torrentland.li'],
        'required_seed_ratio': 0,
        'required_seed_days': 4.0,
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
        'required_seed_days': 3.0,
    },
}

DHT_MATCHES = [
    '** [DHT] **',
    '** [PeX] **',
    '** [LSD] **'
]

def filter_indexer_by_args(indexer_list):
    results = []
    for indexer_name in indexer_list:
        indexer_spec = INDEXER_SPECS.get(indexer_name)
        if indexer_spec:
            results.append(indexer_spec)
    return results

def filter_indexer_by_url(indexer_list, domain):
    for indexer in indexer_list:
        if domain in indexer['urls']:
            return indexer
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

def __init__(args, logger):
    client = qbittools.qbit_client(args)
    ignore_categories = [item for sublist in args.ignore_category for item in sublist]

    indexers = [item for sublist in args.indexer for item in sublist]
    if not args.all_indexers:
        logger.info(f"Using specific indexers '{' '.join(indexers)}'")
        indexers = filter_indexer_by_args(indexers)
    else:
        logger.info(f"Using all indexers")
        indexers = filter_indexer_by_args(list(INDEXER_SPECS.keys()))

    logger.info(f"Checking for expired torrents in qBittorrent")
    extractTLD = tldextract.TLDExtract(cache_dir=None)

    torrents_info = client.torrents.info()
    for torrent in torrents_info:
        if torrent['category'] in ignore_categories:
            logger.debug(f"Skipping torrent {torrent['name']} due to ignore category {torrent['category']}")
            continue

        real_trackers = list(filter(lambda s: not s.url in DHT_MATCHES, torrent.trackers))
        domain = extractTLD(sorted(real_trackers, key=lambda x: x.url)[0].url).registered_domain

        indexer = filter_indexer_by_url(indexers, domain)
        if indexer:
            if torrent['ratio'] >= indexer['required_seed_ratio'] and indexer['required_seed_ratio'] != 0:
                if args.delete:
                    logger.info(f"Removing torrent {torrent['name']} ({domain}) with matching indexer {indexer['name']} due to an expired ratio ({round(torrent['ratio'], 2)})")
                    torrent.delete(delete_files=False)
                else:
                    logger.info(f"Tagging torrent {torrent['name']} ({domain}) with matching indexer {indexer['name']} due to an expired ratio ({round(torrent['ratio'], 2)})")
                    client.torrents_add_tags(tags='expired', torrent_hashes=torrent['hash'])
            elif torrent['seeding_time'] >= seconds(indexer['required_seed_days']):
                if args.delete:
                    logger.info(f"Removing torrent {torrent['name']} ({domain}) with matching indexer {indexer['name']} due to an expired seeding time ({dhms(torrent['seeding_time'])})")
                    torrent.delete(delete_files=False)
                else:
                    logger.info(f"Tagging torrent {torrent['name']} ({domain}) with matching indexer {indexer['name']} due to an expired seeding time ({dhms(torrent['seeding_time'])})")
                    client.torrents_add_tags(tags='expired', torrent_hashes=torrent['hash'])

def add_arguments(subparser):
    parser = subparser.add_parser('expired')
    parser.add_argument('--all-indexers', action='store_true', help='Include all indexers, ignores --indexer arg', required=False)
    parser.add_argument('--indexer', nargs='*', action='append', metavar='myindexer', default=[], help='Indexer, can be repeated multiple times', required=False)
    parser.add_argument('--ignore-category', nargs='*', action='append', metavar='mycategory', default=[], help='Ignore category, can be repeated multiple times', required=False)
    parser.add_argument('--delete', action='store_true', help='Delete torrent when expired, otherwise tag it with expired', required=False)

    qbittools.add_default_args(parser)
