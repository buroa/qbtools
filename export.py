#!/usr/bin/env python3

import argparse, logging, sys, os.path, shutil
from pathlib import Path
import qbittorrentapi

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%I:%M:%S %p')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', metavar='~/.local/share/qBittorrent/BT_backup', default='~/.local/share/qBittorrent/BT_backup', help='Path to qBittorrent .torrent files', required=False)
    parser.add_argument('-o', '--output', metavar='~/export', help='Path to where to save exported torrents', required=True)
    parser.add_argument('-c', '--category', metavar='mycategory', help='Filter by category', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', help='Filter by tags', required=False)

    parser.add_argument('-p', '--port', metavar='12345', help='port', required=True)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)
    args = parser.parse_args()

    client = qbittorrentapi.Client(host=f"{args.server}:{args.port}", username=args.username, password=args.password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

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

if __name__ == "__main__":
    main()
