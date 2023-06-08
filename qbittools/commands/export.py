#!/usr/bin/env python3

import os, shutil, tldextract
from pathlib import Path
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    if args.tags:
        matches = list(filter(lambda x: any(y in x.tags for y in args.tags), client.torrents.info(category=args.category)))
        torrents = list(map(lambda x: (x.hash, x.name, x.trackers), matches))
    else:
        torrents = list(map(lambda x: (x.hash, x.name, x.trackers), client.torrents.info(category=args.category)))
        
    logger.info(f"Matched {len(torrents)} torrents")
    Path(args.output).expanduser().mkdir(parents=True, exist_ok=True)

    for h, name, trackers in torrents:
        from_path = Path(args.input, f"{h}.torrent").expanduser()
        if not from_path.exists():
            logger.error(f"{os.fsencode(from_path).decode('utf8', 'replace')} doesn't exist!")
            continue

        pattern = ""

        tracker_matches = list(filter(lambda x: len(tldextract.extract(x.url).registered_domain) > 0, trackers))

        if len(tracker_matches) > 0:
            domain = tldextract.extract(tracker_matches[0].url).registered_domain
            pattern += f"[{domain}]"

        if args.category:
            pattern += f" [{args.category}]"

        pattern += f" {os.fsencode(name).decode('utf8', 'replace')} [{h}].torrent"
        to_path = Path(args.output, pattern.strip()).expanduser()

        shutil.copy2(from_path, to_path)
        logger.info(f"Exported {os.fsencode(to_path).decode('utf8', 'replace')}")
    logger.info('Done')

def add_arguments(subparser):
    parser = subparser.add_parser('export')
    qbittools.add_default_args(parser)
    parser.add_argument('-i', '--input', metavar='~/.local/share/qBittorrent/BT_backup', default='~/.local/share/qBittorrent/BT_backup', help='Path to qBittorrent .torrent files', required=False)
    parser.add_argument('-o', '--output', metavar='~/export', help='Path to where to save exported torrents', required=True)
    parser.add_argument('-c', '--category', metavar='mycategory', help='Filter by category', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', help='Filter by tags', required=False)
