#!/usr/bin/env python3

import pathlib, os
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)
    active = len(list(filter(lambda x: x.dlspeed > args.max_downloads_speed_ignore_limit * 1024 and x.state == 'downloading', client.torrents.info(status_filter="downloading"))))

    if args.max_downloads != 0 and active >= args.max_downloads:
        logger.info(f"Reached max downloads: {active}")
        return

    to_add = []

    for t in args.torrents:
        p = pathlib.Path(os.fsdecode(t)).expanduser()

        if p.is_dir():
            contents = list(p.glob('*.torrent'))
            to_add += list(map(lambda x: os.fsdecode(x), contents))
        elif p.is_file():
            to_add.append(os.fsdecode(p))

    if args.pause_active:
        for t in client.torrents.info(status_filter="active"):
            if t.state != 'uploading':
                continue

            if t.upspeed > args.pause_active_upspeed_ignore_limit * 1024:
                t.add_tags(['temp_paused'])
                t.pause()
                logger.info(f"Paused {t.name} in {t.state} state, upspeed: {t.upspeed / 1024} KiB/s")
                continue

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
        ratio_limit=args.ratio_limit,
        seeding_time_limit=args.seeding_time_limit
    )

    logger.info(f"Adding torrents: {resp}")

def add_arguments(subparser):
    parser = subparser.add_parser('add')
    qbittools.add_default_args(parser)
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
    parser.add_argument('--ratio-limit', type=float, help='max ratio limit, qBit 4.3.4+', default=-2, required=False)
    parser.add_argument('--seeding-time-limit', type=int, help='seeding time limit in minutes, qBit 4.3.4+', default=-2, required=False)
    parser.add_argument('--max-downloads', type=int, help='Max downloads limit', default=0, required=False)
    parser.add_argument('--max-downloads-speed-ignore-limit', type=int, help='Doesn\'t count downloads with download speed under specified KiB/s for max limit', default=0, required=False)
    parser.add_argument('--pause-active', action='store_true', help='Pause active torrents temporarily')
    parser.add_argument('--pause-active-upspeed-ignore-limit', type=int, help='Doesn\'t count active torrents with upload speed under specified KiB/s for pausing', default=0, required=False)
    parser.set_defaults(tmm=None, root_folder=None)
