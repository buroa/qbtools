#!/usr/bin/env python3

import commands.utils as utils

import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    filtered_torrents = client.torrents.info()

    exclude_categories = [i for s in args.exclude_category for i in s]
    if len(exclude_categories):
        filtered_torrents = list(filter(lambda x: x.category not in exclude_categories, filtered_torrents))
    include_tags = [i for s in args.include_tag for i in s]
    if len(include_tags):
        filtered_torrents = list(filter(lambda x: all(y in x.tags for y in include_tags), filtered_torrents))
    exclude_tags = [i for s in args.exclude_tag for i in s]
    if len(exclude_tags):
        filtered_torrents = list(filter(lambda x: not any(y in x.tags for y in exclude_tags), filtered_torrents))

    logger.info(f"Deleting torrents with tags [{' AND '.join(include_tags)}] but does not contain tags [{' OR '.join(exclude_tags)}]...")
    for t in filtered_torrents:
        logger.info(f"Removed torrent {t['name']} with category [{t.category}] and tags [{t.tags}] and ratio [{round(t['ratio'], 2)}] and seeding time [{utils.dhms(t['seeding_time'])}]")
        if not args.dry_run:
            t.delete(delete_files=args.with_data)

    logger.info(f"Deleted {len(filtered_torrents)} torrents")

def add_arguments(subparser):
    """
    Description:
        Prune torrents that have matching tags. Pair this with the tagging command to tag torrents.
    Usage:
        qbittools.py prune --help
    Example:
        # Delete torrents with the tag 'expired' and 'added:30d', however if the torrent also has the tags 'site:oink' or 'site:whatcd' exclude it from being deleted
        qbittools.py prune --include-tag expired --include-tag added:30d --exclude-tag site:oink --exclude-tag site:whatcd --dry-run
    """
    parser = subparser.add_parser('prune')

    parser.add_argument('--include-tag', nargs='*', action='append', metavar='mytag', default=[], help='Include torrents containing all of these tags, can be repeated multiple times', required=True)
    parser.add_argument('--exclude-tag', nargs='*', action='append', metavar='mytag', default=[], help='Exclude torrents containing any of these tags, can be repeated multiple times', required=False)
    parser.add_argument('--exclude-category', nargs='*', action='append', metavar='mycategory', default=[], help='Exclude torrents in this category, can be repeated multiple times', required=False)

    parser.add_argument('--dry-run', action='store_true', help='Do not delete torrents', default=False, required=False)
    parser.add_argument('--with-data', action='store_true', help='Delete torrents with data', default=False, required=False)

    qbittools.add_default_args(parser)
