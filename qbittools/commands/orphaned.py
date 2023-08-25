#!/usr/bin/env python3

import os
import shutil
from fnmatch import fnmatch

import qbittools

def __init__(args, logger):
    logger.info(f"Checking for orphaned files on disk not in qBittorrent...")

    client = qbittools.qbit_client(args)

    completed_dir = str(qbittools.config.save_path)
    completed_dir_list = completed_dir.split(os.sep)
    exclude_patterns = [i for s in args.exclude_pattern for i in s]

    logger.info(f"Gathering a list of all torrents in qBittorrent...")
    qbittorrent_items = set()
    for torrent in client.torrents.info():
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
    logger.info(f"Done gathering {len(qbittorrent_items)} torrents in qBittorrent")

    logger.info(f"Deleting orphaned files on disk not in qBittorrent...")
    folders = [folder for folder in os.listdir(completed_dir) if os.path.isdir(os.path.join(completed_dir, folder))]
    for folder in folders:
        folder_path = os.path.join(completed_dir, folder)
        contents = os.listdir(folder_path)
        for item in contents:
            item_path = os.path.join(folder_path, item)
            if not any(fnmatch(item, pattern) or fnmatch(item_path, pattern) for pattern in exclude_patterns):
                if item_path not in qbittorrent_items:
                    if not args.dry_run:
                        try:
                            if os.path.isfile(item_path):
                                logger.info(f"Deleting file {item_path}...")
                                os.remove(item_path)
                                logger.info(f"Deleted file {item_path}")
                            elif os.path.isdir(item_path):
                                logger.info(f"Deleting folder {item_path}...")
                                shutil.rmtree(item_path)
                                logger.info(f"Deleted folder {item_path}")
                            else:
                                logger.debug(f"{item_path} does not exist")
                        except Exception as e:
                            logger.error(f"An error occurred: {e}")
                    else:
                        logger.info(f"The flag --dry-run is set, skipping item {item_path}...")

            else:
                logger.info(f"Skipping {item_path} because it matches an exclude pattern...")
    #TODO: Add more stats like total reclaimed data, total items deleted, etc.
    logger.info(f"Done deleting orphaned files on disk not in qBittorrent")

def add_arguments(subparser):
    """
    Description:
        Search for files on disk that are not in qBittorrent and delete them. Pair this with the prune command to delete torrents that are not in qBittorrent.
    Usage:
        qbittools.py orphaned --help
    Example:
        # Delete all files in the completed directory that are not in qBittorrent and don't match the exclude patterns
        qbittools.py orphaned --exclude-pattern "*_unpackerred" --exclude-pattern "*/manual/*" --dry-run
    """
    parser = subparser.add_parser('orphaned')

    parser.add_argument('--exclude-pattern', nargs='*', action='append', metavar='mypattern', default=[], help='Exclude pattern, can be repeated multiple times', required=False)

    parser.add_argument('--dry-run', action='store_true', help='Do not delete any data on disk', default=False, required=False)

    qbittools.add_default_args(parser)
