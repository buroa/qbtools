#!/usr/bin/env python3

import argparse, logging, sys
import qbittorrentapi

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    logger = logging.getLogger('qbit_add')

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', nargs='+', metavar='my.torrent', help='torrents path', required=True)
    parser.add_argument('-o', '--output', metavar='/home/user/downloads', help='download folder', required=False)
    parser.add_argument('-c', '--category', metavar='mycategory', help='category to assign', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', default=[], help='tags to assign, qBit 4.3.2+', required=False)
    parser.add_argument('--skip-checking', action='store_true', help='skip checking')
    parser.add_argument('--add-paused', action='store_true', help='add paused')
    parser.add_argument('--dl-limit', type=int, help='download limit in KiB/s', default=0, required=False)
    parser.add_argument('--up-limit', type=int, help='upload limit in KiB/s', default=0, required=False)

    parser.add_argument('-p', '--port', metavar='12345', help='port', required=True)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)
    args = parser.parse_args()

    if not args.output and not args.category:
        logger.error('Either category or output folder should be chosen!')
        exit(1)

    client = qbittorrentapi.Client(host=f"{args.server}:{args.port}", username=args.username, password=args.password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

    if args.category:
       logger.info(client.torrents_add(
           category=args.category, 
           torrent_files=args.input, 
           tags=','.join(args.tags), 
           is_skip_checking=args.skip_checking, 
           is_paused=args.add_paused,
           download_limit=args.dl_limit * 1024,
           upload_limit=args.up_limit * 1024
        ))
    else:
       logger.info(client.torrents_add(
           save_path=args.output,
           use_auto_torrent_management=False,
           torrent_files=args.input,
           tags=','.join(args.tags),
           is_skip_checking=args.skip_checking,
           is_paused=args.add_paused,
           download_limit=args.dl_limit * 1024,
           upload_limit=args.up_limit * 1024
        ))
if __name__ == "__main__":
        main()
