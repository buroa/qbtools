#!/usr/bin/env python3

import argparse, logging, sys, pkgutil, collections
import qbittorrentapi
from commands import *

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%I:%M:%S %p')
    logger = logging.getLogger('qbitools')

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', metavar='12345', help='port', required=True)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)
    subparsers = parser.add_subparsers(dest='command')

    for _, cmd, _ in pkgutil.iter_modules(['commands']):
        getattr(globals()[cmd], 'add_arguments')(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit()

    client = qbittorrentapi.Client(host=f"{args.server}:{args.port}", username=args.username, password=args.password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

    cmd = getattr(globals()[args.command], '__init__')(args, logger, client)
if __name__ == "__main__":
    main()
