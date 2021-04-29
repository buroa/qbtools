#!/usr/bin/env python3

from _version import __version__
from packaging.version import Version, parse
import git, requests
import os, tempfile, sys, zipfile, shutil, subprocess
from pathlib import Path
from tqdm import tqdm
import qbittools

def download_version(ver):
    url = f"https://gitlab.com/AlexKM/qbittools/-/jobs/artifacts/{ver}/download?job=release"
    temp_dir = tempfile.mkdtemp()
    download_file = Path(temp_dir, "qbittools.zip")
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

def extract_archive(path, dest):
    with zipfile.ZipFile(path, "r") as z:
        z.extract("qbittools", dest)
        return Path(dest, "qbittools")

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
    raw = git.cmd.Git().ls_remote("--tags", "--refs", url).split('\n')

    remote_refs = list(map(lambda x: tuple(x.split('\t')), raw))
    remote_refs = sorted(list(map(lambda ref: (ref[0], ref[1].replace("refs/tags/", "")), remote_refs)), key=lambda x: Version(x[1]), reverse=True)

    cur_ver = Version(__version__)
    latest_ver = Version(remote_refs[0][1])
    logger.info(f"Current version: {cur_ver}")
    logger.info(f"Latest version: {latest_ver}")

    if cur_ver == latest_ver:
        logger.info(f"You use the latest {cur_ver} version, no update needed")
    elif cur_ver < latest_ver:
        logger.info(f"Update available, this will replace {old_bin} with a new version.")
        if not confirm():
            return

        download = download_version(latest_ver)
        if not download:
            return

        archive, temp_dir = download
        new_bin = extract_archive(archive, temp_dir)
        logger.info(f"Extracted binary to {new_bin}")
        logger.info(f"Replacing {old_bin} with {new_bin}")

        shutil.copymode(old_bin, new_bin)
        subprocess.Popen(["mv", "-f", new_bin, old_bin])
        
        sys.exit()

def add_arguments(subparser):
    parser = subparser.add_parser('upgrade')
