#!/usr/bin/env python3

from _version import __version__
from packaging.version import Version, parse
import requests, platform
import os, tempfile, sys, shutil, subprocess
from pathlib import Path
from tqdm import tqdm
from dulwich import porcelain
import qbittools

def download_version(ver, name):
    url = f"https://gitlab.com/api/v4/projects/23524151/packages/generic/qbittools/{ver}/{name}"
    temp_dir = tempfile.mkdtemp()
    download_file = Path(temp_dir, "qbittools")
    qbittools.logger.info(f"Downloading {url} to {download_file}")

    r = requests.get(url, stream=True)
    if r.status_code != requests.codes.ok:
        qbittools.logger.error(f"Invalid status code: {r.status_code}")
        return

    total_size_in_bytes = int(r.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(download_file, 'wb') as f:
        for data in r.iter_content(1024):
            progress_bar.update(len(data))
            f.write(data)

    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        qbittools.logger.error("ERROR, something went wrong")
        return

    return download_file, temp_dir

def confirm():
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("OK to proceed [Y/N]? ").lower()
    return answer == "y"

def __init__(args, logger):
    if not getattr(sys, 'oxidized', False):
        logger.error("Not a binary version, use git pull to upgrade")
        return
    
    old_bin = Path(sys.executable)
    if not old_bin.exists():
        logger.error("Current executable doesn't exist")
        return

    url = "https://gitlab.com/AlexKM/qbittools.git"
    remote_refs = porcelain.ls_remote(url)

    versions = list(map(lambda x: parse(x.decode("utf-8").replace("refs/tags/", "")), remote_refs))
    versions = list(filter(lambda x: isinstance(x, Version), versions))

    if len(versions) == 0:
        logger.error('Failed to find the latest version.')
        sys.exit(1)

    latest_version = max(versions)
    current_version = Version(__version__)
    logger.info(f"Current version: {current_version}")
    logger.info(f"Latest version: {latest_version}")

    if current_version == latest_version:
        logger.info(f"You use the latest {current_version} version, no update needed")
    elif current_version < latest_version:
        logger.info(f"Update available, this will replace {old_bin} with a new version.")
        if not confirm():
            return

        os = platform.uname().system.lower()
        arch = platform.uname().machine.lower()

        download = download_version(latest_version, f"qbittools_{os}_{arch}")
        if not download:
            return

        new_bin, temp_dir = download
        logger.info(f"Replacing {old_bin} with {new_bin}")

        shutil.copymode(old_bin, new_bin)
        subprocess.Popen(["mv", "-f", new_bin, old_bin])
        shutil.rmtree(temp_dir)
        
        sys.exit()

def add_arguments(subparser):
    parser = subparser.add_parser('upgrade')
