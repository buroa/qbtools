#!/usr/bin/env python3

def __init__(args, logger, client):
    if not args.output and not args.category:
        logger.error('Either category or output folder should be chosen!')
        exit(1)

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

def add_arguments(subparser):
    parser = subparser.add_parser('add')
    parser.add_argument('input', nargs='+', metavar='my.torrent', help='torrents path')
    parser.add_argument('-o', '--output', metavar='/home/user/downloads', help='download folder', required=False)
    parser.add_argument('-c', '--category', metavar='mycategory', help='category to assign', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', default=[], help='tags to assign, qBit 4.3.2+', required=False)
    parser.add_argument('--skip-checking', action='store_true', help='skip checking')
    parser.add_argument('--add-paused', action='store_true', help='add paused')
    parser.add_argument('--dl-limit', type=int, help='download limit in KiB/s', default=0, required=False)
    parser.add_argument('--up-limit', type=int, help='upload limit in KiB/s', default=0, required=False)
