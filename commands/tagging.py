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
    default_tags = []

    unregistered_matches = ['unregistered', 'not registered', 'not found', 'not exist', 'unknown', 'uploaded', 'upgraded', 'season pack']
    maintenance_matches = ['tracker is down', 'maintenance']
    dht_matches = ['** [DHT] **', '** [PeX] **', '** [LSD] **']

    if args.not_working:
        default_tags.append('Not Working')

    if args.added_on:
        default_tags.append('added:')

    if args.unregistered:
        default_tags.append('Unregistered')

    if args.tracker_down:
        default_tags.append('Tracker Down')

    if args.trackers:
        default_tags.append('t:')

    if args.duplicates:
        default_tags.append('Duplicates')

    if args.last_activity:
        default_tags.append('activity:')

    tags_to_delete = list(filter(lambda tag: any(x in tag for x in default_tags), client.torrents_tags()))
    if tags_to_delete:
        client.torrents_remove_tags(tags=tags_to_delete, torrent_hashes='all')
        client.torrents_delete_tags(tags=tags_to_delete)

    tag_hashes = collections.defaultdict(list)
    tag_sizes = collections.defaultdict(int)
    content_paths = []

    if args.move_unregistered:
        try:
            client.torrents_create_category('Unregistered')
        except qbittorrentapi.exceptions.Conflict409Error as e:
            pass

    logger.info('Collecting tags...')
    for t in tqdm(client.torrents.info()):
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

        working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
        real_trackers = list(filter(lambda s: not s.url in dht_matches, t.trackers))

        if args.trackers and len(real_trackers) > 0:
            domain = tldextract.extract(real_trackers[0].url).registered_domain
            if len(domain) > 0:
                tags_to_add.append(f"t:{domain}")

        if args.unregistered and not working:
            if any(x in t.msg.lower() for x in unregistered_matches for t in real_trackers):
                tags_to_add.append('Unregistered')

                if args.move_unregistered and t.time_active > 60 and not t.category == 'Unregistered':
                    t.set_category(category='Unregistered')
        elif args.tracker_down and not working:
            if any(x in t.msg.lower() for x in maintenance_matches for t in real_trackers):
                tags_to_add.append('Tracker Down')
        elif args.not_working and not working:
            tags_to_add.append('Not Working')

        if args.duplicates:
            match = [(infohash, path, size) for infohash, path, size in content_paths if path == t.content_path and not t.content_path == t.save_path]
            if match:
                tags_to_add.append("Duplicates")
                tag_hashes["Duplicates"].append(match[0][0])
                tag_sizes["Duplicates"] += match[0][2]

            content_paths.append((t.hash, t.content_path, t.size))

        for tag in tags_to_add:
            tag_hashes[tag].append(t.hash)
            tag_sizes[tag] += t.size

    logger.info('Adding tags...')

    if len(tag_hashes) == 0:
        logger.info('Nothing to add, quitting')
    else:
        for tag in tqdm(tag_hashes):
            size = utils.format_bytes(tag_sizes[tag])
            client.torrents_add_tags(tags=f"{tag} [{size}]", torrent_hashes=tag_hashes[tag])

def add_arguments(subparser):
    parser = subparser.add_parser('tagging')
    parser.add_argument('--move-unregistered', action='store_true', help='Move unregistered torrents to Unregistered category')
    parser.add_argument('--not-working', action='store_true', help='Tag torrents with not working tracker status')
    parser.add_argument('--unregistered', action='store_true', help='Tag torrents with unregistered tracker status message')
    parser.add_argument('--duplicates', action='store_true', help='Tag torrents with the same content path')
    parser.add_argument('--added-on', action='store_true', help='Tag torrents with added date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--last-activity', action='store_true', help='Tag torrents with last activity date (last 24h, 7 days, 30 days, etc)')
    parser.add_argument('--trackers', action='store_true', help='Tag torrents with tracker domains')
    parser.add_argument('--tracker-down', action='store_true', help='Tag torrents with temporarily down trackers')
    qbittools.add_default_args(parser)
