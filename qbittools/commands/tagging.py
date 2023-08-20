#!/usr/bin/env python3

import collections
from datetime import datetime
import tldextract
from tqdm import tqdm
import qbittools
import qbittorrentapi
import commands.utils as utils

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    today = datetime.today()
    default_tags = [
        'Not Working',
        'added:',
        'Unregistered',
        'Tracker Down',
        't:',
        'Duplicates',
        'activity:',
        'Not Linked'
    ]

    unregistered_matches = [
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
        'i\'m sorry dave, i can\'t do that' # weird stuff from racingforme
    ]
    
    maintenance_matches = [
        'tracker is down',
        'maintenance'
    ]

    dht_matches = [
        '** [DHT] **',
        '** [PeX] **',
        '** [LSD] **'
    ]

    tag_hashes = collections.defaultdict(list)
    tag_sizes = collections.defaultdict(int)
    content_paths = []

    if args.move_unregistered:
        try:
            client.torrents_create_category('Unregistered')
        except qbittorrentapi.exceptions.Conflict409Error as e:
            pass

    logger.info('Collecting tags info...')
    filtered_torrents = client.torrents.info()
    all_torrents = client.torrents.info()

    if args.categories:
        filtered_torrents = list(filter(lambda x: x.category in args.categories, filtered_torrents))

    if args.tags:
        filtered_torrents = list(filter(lambda x: any(y in x.tags for y in args.tags), filtered_torrents))

    tags_to_delete = list(filter(lambda tag: any(tag.lower().startswith(x.lower()) for x in default_tags), client.torrents_tags()))

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

        if args.trackers or args.unregistered or args.tracker_down or args.not_working:
            # trackers call is expensive for large amount of torrents
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            real_trackers = list(filter(lambda s: not s.url in dht_matches, t.trackers))
            
            if args.trackers and len(real_trackers) > 0:
                domain = tldextract.extract(sorted(real_trackers, key=lambda x: x.url)[0].url).registered_domain
                if len(domain) > 0:
                    tags_to_add.append(f"t:{domain}")

            if not working:
                unregistered_matched = any(rt.msg.lower().startswith(x.lower()) for x in unregistered_matches for rt in real_trackers)
                maintenance_matched = any(rt.msg.lower().startswith(x.lower()) for x in maintenance_matches for rt in real_trackers)

                if args.unregistered and unregistered_matched:
                    tags_to_add.append('Unregistered')

                    if args.move_unregistered and t.time_active > 60 and not t.category == 'Unregistered':
                        t.set_category(category='Unregistered')
                elif args.tracker_down and maintenance_matched:
                    tags_to_add.append('Tracker Down')
                elif args.not_working:
                    tags_to_add.append('Not Working')

        if args.duplicates:
            match = [(infohash, path, size) for infohash, path, size in content_paths if path == t.content_path and not t.content_path == t.save_path]
            if match:
                tags_to_add.append("Duplicates")
                tag_hashes["Duplicates"].append(match[0][0])
                if args.size:
                    tag_sizes["Duplicates"] += match[0][2]

            content_paths.append((t.hash, t.content_path, t.size))
        
        if args.not_linked and not utils.is_linked(t.content_path):
            tags_to_add.append("Not Linked")

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

    parser.add_argument('--move-unregistered', action='store_true', help='Move unregistered torrents to Unregistered category. Must be used with --unregistered')
    parser.add_argument('--not-working', action='store_true', help='Tag torrents with not working tracker status. Significantly increases script execution time')
    parser.add_argument('--unregistered', action='store_true', help='Tag torrents with unregistered tracker status message. Significantly increases script execution time')
    parser.add_argument('--duplicates', action='store_true', help='Tag torrents with the same content path')
    parser.add_argument('--added-on', action='store_true', help='Tag torrents with added date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--last-activity', action='store_true', help='Tag torrents with last activity date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--trackers', action='store_true', help='Tag torrents with tracker domains. Significantly increases script execution time')
    parser.add_argument('--tracker-down', action='store_true', help='Tag torrents with temporarily down trackers. Significantly increases script execution time')
    parser.add_argument('--size', action='store_true', help='Add size of tagged torrents to created tags')
    parser.add_argument('--not-linked', action='store_true', help='Tag torrents with files without hardlinks or symlinks, use with filtering by category/tag. Significantly increases script execution time')
    
    qbittools.add_default_args(parser)
