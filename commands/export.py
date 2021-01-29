#!/usr/bin/env python3

import os.path, shutil
from pathlib import Path

def __init__(args, logger, client):
    if args.tags:
        matches = list(filter(lambda x: any(y in x.tags for y in args.tags), client.torrents.info(category=args.category)))
        hashes = list(map(lambda x: (x.hash, x.name), matches))
    else:
        hashes = list(map(lambda x: (x.hash, x.name), client.torrents.info(category=args.category)))
        
    logger.info(f"Matched {len(hashes)} torrents")
    Path(args.output).expanduser().mkdir(parents=True, exist_ok=True)

    for h, name in hashes:
        from_f = Path(args.input, f"{h}.torrent").expanduser()

        pattern = f"{name} [{h}].torrent"
        if args.category: pattern = f"[{args.category}] {pattern}"
        to_f = Path(args.output, pattern).expanduser()

        if not from_f.exists():
            logger.error(f"{from_f} doesn't exist!")
            continue

        shutil.copy2(from_f, to_f)
        logger.info(f"Exported {pattern}")
    logger.info('Done')

def add_arguments(subparser):
    parser = subparser.add_parser('export')
    parser.add_argument('-i', '--input', metavar='~/.local/share/qBittorrent/BT_backup', default='~/.local/share/qBittorrent/BT_backup', help='Path to qBittorrent .torrent files', required=False)
    parser.add_argument('-o', '--output', metavar='~/export', help='Path to where to save exported torrents', required=True)
    parser.add_argument('-c', '--category', metavar='mycategory', help='Filter by category', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', help='Filter by tags', required=False)
