#!/usr/bin/env python3

import commands.utils as utils

import qbittools

def __init__(args, logger):
    logger.info(f"Checking for torrents with expired tag in qBittorrent...")

    client = qbittools.qbit_client(args)

    filtered_torrents = client.torrents.info()
    filtered_torrents = list(filter(lambda x: 'expired' in x.tags, filtered_torrents))
    if args.ignore_category:
        ignore_categories = [item for sublist in args.ignore_category for item in sublist]
        filtered_torrents = list(filter(lambda x: x.category not in ignore_categories, filtered_torrents))
    if args.ignore_tag:
        ignore_tags = [item for sublist in args.ignore_tag for item in sublist]
        filtered_torrents = list(filter(lambda x: any(y not in x.tags for y in ignore_tags), filtered_torrents))

    for t in filtered_torrents:
        logger.info(f"Removed torrent {t['name']} with tags [{t.tags}] due to an expired ratio ({round(t['ratio'], 2)}) or expired seeding time ({utils.dhms(t['seeding_time'])})")
        if not args.dry_run:
            t.delete(delete_files=args.with_data)

    logger.info(f"Deleted {len(filtered_torrents)} torrents with an expired tag")

def add_arguments(subparser):
    """
    Description:
        Delete torrents that have an expired tag. Pair this with the tagging command to tag torrents that have expired.
    Usage:
        qbittools.py expired --help
    """
    parser = subparser.add_parser('expired')

    parser.add_argument('--ignore-category', nargs='*', action='append', metavar='mycategory', default=[], help='Ignore all torrent with this category, can be repeated multiple times', required=False)
    parser.add_argument('--ignore-tag', nargs='*', action='append', metavar='mytag', default=[], help='Ignore all torrents with this tag, can be repeated multiple times', required=False)

    parser.add_argument('--dry-run', action='store_true', help='Do not delete torrents', default=False, required=False)
    parser.add_argument('--with-data', action='store_true', help='Delete torrents with data', default=False, required=False)

    qbittools.add_default_args(parser)
