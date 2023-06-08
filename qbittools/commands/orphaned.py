#!/usr/bin/env python3

import collections
from datetime import datetime
import tldextract
from tqdm import tqdm
import qbittools
import qbittorrentapi
import os, operator, sys
import pathlib3x as pathlib
import commands.utils as utils

def confirm(text):
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(text).lower()
    return answer == "y"

def is_dir_empty(path):
    with os.scandir(path) as scan:
        return next(scan, None) is None

def delete_empty_dirs(folders, force=False):
    qbittools.logger.info(f"Collecting empty directories...")
    fs_dirs = [pathlib.Path(path) / name for folder in folders for path, subdirs, files in os.walk(folder) for name in subdirs if is_dir_empty(pathlib.Path(path) / name)]

    if len(fs_dirs) == 0:
        qbittools.logger.info('None found')
        return

    for path in fs_dirs:
        print(path)

    if not force and not confirm('OK to delete all including parent directories if these are empty too [Y/N]? '):
        return

    for folder in folders:
        for path, subdirs, files in os.walk(folder, topdown=False):
            for name in subdirs:
                dir_path = pathlib.Path(path) / name

                if is_dir_empty(dir_path):
                    qbittools.logger.info(f"Removing {os.fsencode(dir_path).decode('utf8', 'replace')}")
                    dir_path.rmdir()

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    folders = {qbittools.config.save_path}
    folders |= {category.savePath for category in client.torrents_categories().values() if category.savePath != '' and not qbittools.config.save_path.is_relative_to(category.savePath)}
    logger.info(f"Download folders: {list(map(str, folders))}")
    logger.info('Collecting files from download folders...')
    fs_files = {pathlib.Path(path) / name for folder in tqdm(folders) for path, subdirs, files in os.walk(folder) for name in files}

    logger.info('Collecting files from qBittorrent...')
    qbit_files = {pathlib.Path(torrent.save_path) / file.name for torrent in tqdm(client.torrents.info()) for file in torrent.files}
    diff = fs_files - qbit_files

    if len(diff) == 0:
        logger.info('Nothing to delete')
        delete_empty_dirs(folders, args.force)
        return


    logger.info('Preparing list of orphaned files...')
    files_and_sizes = ((path, path.stat().st_size) for path in tqdm(diff))
    sorted_files_with_size = sorted(files_and_sizes, key = operator.itemgetter(1), reverse=True)

    total_size = sum(size for file, size in sorted_files_with_size)
    print(f"Total size: {utils.format_bytes(total_size)}")

    for file, size in sorted_files_with_size:
        print(f"{utils.format_bytes(size)}\t{os.path.relpath(os.fsencode(file).decode('utf8', 'replace'), qbittools.config.save_path)}")

    if not args.force and not confirm('OK to delete all [Y/N]? '):
        return

    for file, size in sorted_files_with_size:
        logger.info(f"Removing {os.fsencode(file).decode('utf8', 'replace')}")
        file.unlink()
    delete_empty_dirs(folders, args.force)

def add_arguments(subparser):
    parser = subparser.add_parser('orphaned')
    parser.add_argument('--force', action='store_true', help='Delete without asking')
    qbittools.add_default_args(parser)
