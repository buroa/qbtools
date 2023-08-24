#!/usr/bin/env python3

import collections
from datetime import datetime
import tldextract
from tqdm import tqdm
import qbittorrentapi
import commands.utils as utils

import qbittools

DEFAULT_TAGS = [
    'activity:',
    'added:',
    'dupe',
    'not-linked',
    'not-working',
    'unregistered',
    'tracker-down',
    'domain:',
    'site:',
]

UNREGISTERED_MATCHES = [
    'unregistered',
    'not authorized',
    'not registered',
    'not found',
    'not exist',
    'unknown',
    'uploaded',
    'upgraded',
    'season pack',
    'packs are available',
    'pack is available',
    'internal available',
    'season pack out',
    'dead',
    'dupe',
    'complete season uploaded',
    'problem with',
    'specifically banned',
    'trumped',
    'torrent existiert nicht',
    'i\'m sorry dave, i can\'t do that' # weird stuff from racingforme
]

MAINTENANCE_MATCHES = [
    'tracker is down',
    'maintenance'
]

DHT_MATCHES = [
    '** [DHT] **',
    '** [PeX] **',
    '** [LSD] **'
]

SITE_MAPPINGS = {
    'animetorrents.me': { 'urls': ['animetorrents.me'] },
    'avistaz': { 'urls': ['avistaz.to'] },
    'beyond-hd': { 'urls': ['beyond-hd.me'] },
    'blutopia': { 'urls': ['blutopia.cc', 'blutopia.xyz'] },
    'broadcasthenet': { 'urls': ['landof.tv'] },
    'cinemaz': { 'urls': ['cinemaz.to'] },
    'exoticaz': { 'urls': ['exoticaz.to'] },
    'filelist': { 'urls': ['filelist.io', 'flro.org'] },
    'hd-space': { 'urls': ['hd-space.pw'] },
    'hd-torrents': { 'urls': ['hdts-announce.ru'] },
    'iptorrents': { 'urls': ['bgp.technology', 'empirehost.me', 'stackoverflow.tech'] },
    'karagarga': { 'urls': ['karagarga.in'] },
    'kraytracker': { 'urls': ['kraytracker.com'] },
    'morethantv': { 'urls': ['morethantv.me'] },
    'myanonamouse': { 'urls': ['myanonamouse.net'] },
    'myspleen': { 'urls': ['myspleen.org'] },
    'orpheus': { 'urls': ['home.opsfet.ch'] },
    'passthepopcorn': { 'urls': ['passthepopcorn.me'] },
    'privatehd': { 'urls': ['privatehd.to'] },
    'redacted': { 'urls': ['flacsfor.me'] },
    'scenetime': { 'urls': ['scenetime.com'] },
    'torrentday': { 'urls': ['jumbohostpro.eu', 'td-peers.com'] },
    'torrentleech': { 'urls': ['tleechreload.org', 'torrentleech.org'] },
    'torrentseeds': { 'urls': ['torrentseeds.org'] },
    'uhdbits': { 'urls': ['uhdbits.org'] },
}

def site_name(domain, site_matches):
    for site, data in site_matches.items():
        if any(domain in url for url in data['urls']):
            return site
    return None

def __init__(args, logger):
    client = qbittools.qbit_client(args)
    today = datetime.today()
    extractTLD = tldextract.TLDExtract(cache_dir=None)

    tag_hashes = collections.defaultdict(list)
    tag_sizes = collections.defaultdict(int)
    content_paths = []

    if args.move_unregistered:
        try:
            client.torrents_create_category('unregistered')
        except qbittorrentapi.exceptions.Conflict409Error as e:
            pass

    logger.info('Collecting tags info...')
    filtered_torrents = client.torrents.info()

    if args.categories:
        filtered_torrents = list(filter(lambda x: x.category in args.categories, filtered_torrents))

    if args.tags:
        filtered_torrents = list(filter(lambda x: any(y in x.tags for y in args.tags), filtered_torrents))

    tags_to_delete = list(filter(lambda tag: any(tag.lower().startswith(x.lower()) for x in DEFAULT_TAGS), client.torrents_tags()))

    if tags_to_delete:
        hashes = list(map(lambda t: t.hash, filtered_torrents))
        client.torrents_remove_tags(tags=tags_to_delete, torrent_hashes=hashes)

        logger.info('Pruning old tags...')

        empty_tags = list(filter(lambda tag: len(list(filter(lambda t: tag in t.tags, client.torrents.info()))) == 0, tqdm(tags_to_delete)))
        client.torrents_delete_tags(tags=empty_tags)

    logger.info('Collecting torrents info...')
    for t in tqdm(filtered_torrents):
        tags_to_add = []

        if args.added_on:
            added_on = datetime.fromtimestamp(t.added_on)
            diff = today - added_on

            if diff.days == 0:
                tags_to_add.append('added:24h')
            elif diff.days <= 7:
                tags_to_add.append('added:7d')
            elif diff.days <= 30:
                tags_to_add.append('added:30d')
            elif diff.days > 30:
                tags_to_add.append('added:>30d')

        if args.last_activity:
            last_activity = datetime.fromtimestamp(t.last_activity)
            diff = datetime.today() - last_activity

            if t.last_activity == -1:
                tags_to_add.append('activity:never')
            elif diff.days == 0:
                tags_to_add.append('activity:24h')
            elif diff.days <= 7:
                tags_to_add.append('activity:7d')
            elif diff.days <= 30:
                tags_to_add.append('activity:30d')
            elif diff.days <= 180:
                tags_to_add.append('activity:180d')
            elif diff.days > 180:
                tags_to_add.append('activity:>180d')

        if args.sites or args.trackers or args.unregistered or args.tracker_down or args.not_working:
            # trackers call is expensive for large amount of torrents
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            real_trackers = list(filter(lambda s: not s.url in DHT_MATCHES, t.trackers))

            if (args.domains or args.sites) and len(real_trackers) > 0:
                domain = extractTLD(sorted(real_trackers, key=lambda x: x.url)[0].url).registered_domain
                if len(domain) > 0:
                    if args.domains:
                        tags_to_add.append(f"domain:{domain}")
                    if args.sites:
                        site = site_name(domain, SITE_MAPPINGS)
                        if site:
                            tags_to_add.append(f"site:{site}")
                        else:
                            tags_to_add.append(f"site:unknown")

            if not working:
                unregistered_matched = any(rt.msg.lower().startswith(x.lower()) for x in UNREGISTERED_MATCHES for rt in real_trackers)
                maintenance_matched = any(rt.msg.lower().startswith(x.lower()) for x in MAINTENANCE_MATCHES for rt in real_trackers)

                if args.unregistered and unregistered_matched:
                    tags_to_add.append('unregistered')

                    if args.move_unregistered and t.time_active > 60 and not t.category == 'unregistered':
                        t.set_category(category='unregistered')
                elif args.tracker_down and maintenance_matched:
                    tags_to_add.append('tracker-down')
                elif args.not_working:
                    tags_to_add.append('not-working')

        if args.duplicates:
            match = [(infohash, path, size) for infohash, path, size in content_paths if path == t.content_path and not t.content_path == t.save_path]
            if match:
                tags_to_add.append("dupe")
                tag_hashes["dupe"].append(match[0][0])
                if args.size:
                    tag_sizes["dupe"] += match[0][2]

            content_paths.append((t.hash, t.content_path, t.size))

        if args.not_linked and not utils.is_linked(t.content_path):
            tags_to_add.append("not-linked")

        for tag in tags_to_add:
            tag_hashes[tag].append(t.hash)
            if args.size:
                tag_sizes[tag] += t.size

    logger.info('Adding tags...')

    if len(tag_hashes) == 0:
        logger.info('Nothing to add, quitting')
    else:
        for tag in tqdm(tag_hashes):
            if args.size:
                size = utils.format_bytes(tag_sizes[tag])
                client.torrents_add_tags(tags=f"{tag} [{size}]", torrent_hashes=tag_hashes[tag])
            else:
                client.torrents_add_tags(tags=tag, torrent_hashes=tag_hashes[tag])
        logger.info('Done')

def add_arguments(subparser):
    parser = subparser.add_parser('tagging')

    parser.add_argument('-c', '--categories', nargs='*', metavar='mycategory', help='Filter by categories', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', help='Filter by tags', required=False)

    parser.add_argument('--move-unregistered', action='store_true', help='Move unregistered torrents to unregistered category. Must be used with --unregistered')
    parser.add_argument('--not-working', action='store_true', help='Tag torrents with not working tracker status. Significantly increases script execution time')
    parser.add_argument('--unregistered', action='store_true', help='Tag torrents with unregistered tracker status message. Significantly increases script execution time')
    parser.add_argument('--duplicates', action='store_true', help='Tag torrents with the same content path')
    parser.add_argument('--added-on', action='store_true', help='Tag torrents with added date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--last-activity', action='store_true', help='Tag torrents with last activity date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--domains', action='store_true', help='Tag torrents with tracker domains. Significantly increases script execution time')
    parser.add_argument('--tracker-down', action='store_true', help='Tag torrents with temporarily down trackers. Significantly increases script execution time')
    parser.add_argument('--size', action='store_true', help='Add size of tagged torrents to created tags')
    parser.add_argument('--not-linked', action='store_true', help='Tag torrents with files without hardlinks or symlinks, use with filtering by category/tag. Significantly increases script execution time')
    parser.add_argument('--sites', action='store_true', help='Tag torrents with known site names. Significantly increases script execution time')

    qbittools.add_default_args(parser)
