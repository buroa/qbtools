#!/usr/bin/env python3

import pathlib, hashlib, os
from bencoder import bencode, bdecode, bdecode2

def __init__(args, logger, client):
    to_add = []
    hashes = []

    for t in args.torrents:
        p = pathlib.Path(os.fsdecode(t))

        if p.is_dir():
            contents = list(p.glob('*.torrent'))
            to_add += list(map(lambda x: os.fsdecode(x)), contents)
            hashes += list(map(lambda x: torrent_hash(x), contents))
        elif p.is_file():
            to_add.append(os.fsdecode(p))
            infohash = torrent_hash(p)
            hashes.append(infohash)

    resp = client.torrents_add(
        torrent_files=to_add,
        save_path=args.save_path,
        cookie=args.cookie,
        category=args.category,
        is_skip_checking=args.skip_checking,
        is_paused=args.add_paused,
        is_root_folder=args.root_folder,
        rename=args.rename,
        download_limit=args.dl_limit * 1024,
        upload_limit=args.up_limit * 1024,
        use_auto_torrent_management=args.tmm,
        is_sequential_download=args.sequential,
        is_first_last_piece_priority=args.first_last_piece_prio,
        tags=','.join(args.tags),
    )

    logger.info(f"Adding torrents: {resp}")

    if resp == 'Ok.':
        logger.info('Setting share limits')
        client.torrents_set_share_limits(ratio_limit=args.ratio_limit, seeding_time_limit=args.seeding_time_limit, torrent_hashes=hashes)

def torrent_hash(filepath):
    with filepath.open('rb') as f:
        torrent = bdecode(f.read())
        info = torrent[b'info']
        return hashlib.sha1(bencode(info)).hexdigest()

def add_arguments(subparser):
    parser = subparser.add_parser('add')
    parser.add_argument('torrents', nargs='+', metavar='my.torrent', help='torrents path')
    parser.add_argument('-o', '--save-path', metavar='/home/user/downloads', help='Download folder', required=False)
    parser.add_argument('--cookie', help='Cookie sent to download the .torrent file', required=False)
    parser.add_argument('-c', '--category', metavar='mycategory', help='Category for the torrent', required=False)
    parser.add_argument('-t', '--tags', nargs='*', metavar='mytag', default=[], help='Tags for the torrent, split by a whitespace, qBit 4.3.2+', required=False)
    parser.add_argument('--skip-checking', action='store_true', help='Skip hash checking')
    parser.add_argument('--add-paused', action='store_true', help='Add torrents in the paused state')
    parser.add_argument('--root-folder', action='store_true', dest='root_folder', help='Create the root folder')
    parser.add_argument('--no-root-folder', action='store_false', dest='root_folder', help='Don\'t create the root folder')
    parser.add_argument('--rename', help='New name for torrent(s)', required=False)
    parser.add_argument('--dl-limit', type=int, help='Download limit in KiB/s', default=0, required=False)
    parser.add_argument('--up-limit', type=int, help='Upload limit in KiB/s', default=0, required=False)
    parser.add_argument('--tmm', action='store_true', dest='tmm', help='Enable Automatic Torrent Management')
    parser.add_argument('--no-tmm', action='store_false', dest='tmm', help='Disable Automatic Torrent Management')
    parser.add_argument('--sequential', action='store_true', help='Enable sequential download')
    parser.add_argument('--first-last-piece-prio', action='store_true', help='Prioritize download first last piece')
    parser.add_argument('--ratio-limit', type=float, help='max ratio limit', default=-2, required=False)
    parser.add_argument('--seeding-time-limit', type=int, help='seeding time limit in minutes', default=-2, required=False)
    parser.set_defaults(tmm=None, root_folder=None)
