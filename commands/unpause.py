#!/usr/bin/env python3

import pathlib, hashlib, os
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    torrents = client.torrents.info(status_filter="downloading")
    active = len(list(filter(lambda x: x.state == 'downloading' and x.dlspeed > args.dl_ignore_limit * 1024, torrents)))

    if active > 0:
        logger.error(f"There are still {active} active downloads")
        return

    for t in client.torrents.info():
        if 'temp_paused' in t.tags and (t.state == 'pausedUP' or t.state == 'pausedDL'):
            t.resume()
            t.remove_tags(['temp_paused'])
            logger.info(f"Resumed {t.name}")

    client.torrents_delete_tags(tags=['temp_paused'])

def add_arguments(subparser):
    parser = subparser.add_parser('unpause')
    parser.add_argument('-d', '--dl-ignore-limit', type=int, help='Doesn\'t count active torrents with download speed under specified KiB/s for unpausing', default=0, required=False)
    qbittools.add_default_args(parser)
