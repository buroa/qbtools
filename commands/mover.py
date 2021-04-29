#!/usr/bin/env python3

import collections
from datetime import datetime
import tldextract
from tqdm import tqdm
import qbittools
import qbittorrentapi
import sys

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    try:
        client.torrents_create_category(args.destination)
    except qbittorrentapi.exceptions.Conflict409Error as e:
        pass

    torrent_hashes = collections.defaultdict(list)
    logger.info('Collecting torrents...')

    for t in tqdm(client.torrents.info(filter='completed')):
        if t.category in args.source:
            completion_on = datetime.fromtimestamp(t.completion_on)
            completed_diff = datetime.today() - completion_on

            last_activity = datetime.fromtimestamp(t.last_activity)
            last_activity_diff = datetime.today() - last_activity

            if completed_diff.total_seconds() > args.completion_threshold * 60 and last_activity_diff.total_seconds() > args.active_threshold:
                torrent_hashes[t.category].append(t.hash)

    if len(torrent_hashes) == 0:
        logger.info('Nothing to do, exiting')
        sys.exit()

    logger.info('Changing categories...')
    for cat in tqdm(torrent_hashes):
        client.torrents_set_category(args.destination, torrent_hashes=torrent_hashes[cat])

def add_arguments(subparser):
    parser = subparser.add_parser('mover')
    parser.add_argument('source', nargs='+', metavar='category1 category2', help='A list of categories to move to another category')
    parser.add_argument('-d', '--destination', metavar='mycategory', help='A category in which all torrents will be moved', required=True)
    parser.add_argument('--active-threshold', type=int, help='Move only torrents with last activity more than N seconds ago', default=60, required=False)
    parser.add_argument('--completion-threshold', type=int, help='Move only torrents completed more than N minutes ago', default=60, required=False)
    qbittools.add_default_args(parser)
