#!/usr/bin/env python3

import collections
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args.server, args.port, args.username, args.password)

    trackers = collections.defaultdict(int)

    for t in client.torrents.info():
        matches = list(map(lambda x: x.url, filter(lambda s: args.old in s.url, t.trackers)))
        found = len(matches) > 0

        if not found: continue

        for url in matches:
            trackers[url] += 1
            if not args.dry_run: t.edit_tracker(url, url.replace(args.old, args.new))

    for url in trackers:
        if args.dry_run:
            logger.info(f"Would replace [{url}] to [{url.replace(args.old, args.new)}] in {trackers[url]} torrents")
        else:
            logger.info(f"Replaced [{url}] to [{url.replace(args.old, args.new)}] in {trackers[url]} torrents")

    if len(trackers) == 0: logger.error(f"Not found any torrents matching {args.old} passkey")

def add_arguments(subparser):
    parser = subparser.add_parser('update_passkey')
    parser.add_argument('--old', metavar='oldpasskey', help='Old passkey', required=True)
    parser.add_argument('--new', metavar='newpasskey', help='New passkey', required=True)
    parser.add_argument('-d', '--dry-run', action='store_true')
    qbittools.add_default_args(parser)
