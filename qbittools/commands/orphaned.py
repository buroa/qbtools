#!/usr/bin/env python3

import qbittools
import os

def __init__(args, logger):
    client = qbittools.qbit_client(args)
    completed_dir = qbittools.config.save_path

    torrent_list = client.torrents.info()
    completed_dir_list = completed_dir.split(os.sep)

    qbittorrent_files = set()
    for torrent in torrent_list:
        torrent_files = torrent['content_path']
        if os.path.isfile(torrent_files):
            torrent_path_list = torrent_files.split(os.sep)
            merged_list = [value for value in torrent_path_list if value not in completed_dir_list]
            if len(merged_list) > 2:
                torrent_files = os.path.dirname(torrent_files)
            qbittorrent_files.add(torrent_files)
        if os.path.isdir(torrent_files):
            qbittorrent_files.add(torrent_files)

    folders = [folder for folder in os.listdir(completed_dir) if os.path.isdir(os.path.join(completed_dir, folder))]
    for folder in folders:
        folder_path = os.path.join(completed_dir, folder)
        contents = os.listdir(folder_path)
        for item in contents:
            item_path = os.path.join(folder_path, item)
            if item_path not in qbittorrent_files:
                if not args.confirm:
                    logger.info(f"Skipping deletion of {item_path}")

def add_arguments(subparser):
    parser = subparser.add_parser('orphaned')
    parser.add_argument('--confirm', action='store_true', help='Confirm deletion of orphaned files')
    qbittools.add_default_args(parser)
