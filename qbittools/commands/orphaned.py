#!/usr/bin/env python3

import qbittools
import os
import shutil
from fnmatch import fnmatch

def __init__(args, logger):
    client = qbittools.qbit_client(args)
    completed_dir = str(qbittools.config.save_path)

    torrent_list = client.torrents.info()
    completed_dir_list = completed_dir.split(os.sep)

    logger.info(f"Checking for orphaned files in qBittorrent")
    logger.info(f"Not deleting files in {completed_dir} that are in qBittorrent")
    logger.info(f"Use --confirm to delete files in {completed_dir} that are not in qBittorrent")
    logger.info(f"Ignoring file/folder patterns '{' '.join(args.ignore_patterns)}'")

    logger.info(f"Getting a list of all torrents 'content_path' in qBittorrent")
    qbittorrent_items = set()
    for torrent in torrent_list:
        item_path = torrent['content_path']
        if os.path.isfile(item_path):
            # Account for the fact that an item's data may be in a subdirectory of the completed/$category directory
            # e.g. completed/$category/$name/$name.mkv
            torrent_path_list = item_path.split(os.sep)
            merged_list = [value for value in torrent_path_list if value not in completed_dir_list]
            if len(merged_list) > 2:
                item_path = os.path.dirname(item_path)
            qbittorrent_items.add(item_path)
        if os.path.isdir(item_path):
            qbittorrent_items.add(item_path)

    logger.info(f"Found {len(qbittorrent_items)} total items in qBittorrent")

    logger.info(f"Get a list of all files and folders in the completed directory")
    folders = [folder for folder in os.listdir(completed_dir) if os.path.isdir(os.path.join(completed_dir, folder))]
    for folder in folders:
        folder_path = os.path.join(completed_dir, folder)
        contents = os.listdir(folder_path)
        for item in contents:
            item_path = os.path.join(folder_path, item)
            if not any(fnmatch(item, pattern) or fnmatch(item_path, pattern) for pattern in args.ignore_patterns.split()):
                if item_path not in qbittorrent_items:
                    if not args.confirm:
                        logger.info(f"Skipping deletion of {item_path}")
                    else:
                        try:
                            if os.path.isfile(item_path):
                                logger.info(f"Deleting file {item_path}")
                                os.remove(item_path)
                            elif os.path.isdir(item_path):
                                logger.info(f"Deleting folder {item_path}")
                                shutil.rmtree(item_path)
                            else:
                                logger.debug(f"{item_path} does not exist.")
                        except Exception as e:
                            logger.error(f"An error occurred: {e}")
            else:
                logger.info(f"Skipping {item_path} because it matches an ignore pattern")

    logger.info(f"Completed checking for orphaned files in qBittorrent")

def add_arguments(subparser):
    parser = subparser.add_parser('orphaned')
    parser.add_argument('--confirm', action='store_true', help='Confirm deletion of orphaned files', required=False)
    parser.add_argument('-i', '--ignore-patterns', nargs='*', metavar='mypattern', default=[], help='Ignore patterns, split by a whitespace', required=False)
    qbittools.add_default_args(parser)
