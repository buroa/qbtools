#!/usr/bin/env python3

import argparse, logging, sys, collections
import qbittorrentapi

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--old', metavar='oldpasskey', help='Old passkey', required=True)
    parser.add_argument('--new', metavar='newpasskey', help='New passkey', required=True)
    parser.add_argument('-d', '--dry-run', action='store_true')

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

if __name__ == "__main__":
    main()
