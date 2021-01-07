#!/usr/bin/env python3

# pip3 install qbittorrent-api tldextract tqdm

import qbittorrentapi
import tldextract
import argparse
from datetime import datetime
import collections
from tqdm import tqdm

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while size > power:
        size /= power
        n += 1
    formatted = round(size, 2)
    return f"{formatted} {power_labels[n]}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', metavar='56423', required=True)
    parser.add_argument('-s', metavar='127.0.0.1', default='127.0.0.1', required=False)
    parser.add_argument('-u', metavar='username', required=False)
    parser.add_argument('-pw', metavar='password', required=False)
    args = parser.parse_args()

    client = qbittorrentapi.Client(host=f"{args.s}:{args.p}", username=args.u, password=args.pw)
    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)

    torrent_list = client.torrents.info()
    today = datetime.today()
    tracker_exceptions = ['** [DHT] **', '** [PeX] **', '** [LSD] **']
    default_tags = ['Not Working', 'added:', 'Unregistered', 't:']

    #print(client.torrents_tags())
    tags_to_delete = list(filter(lambda tag: any(x in tag for x in default_tags), client.torrents_tags()))
    client.torrents_remove_tags(tags=tags_to_delete, torrent_hashes='all')
    client.torrents_delete_tags(tags=tags_to_delete)

    tag_hashes = collections.defaultdict(list)
    tag_sizes = collections.defaultdict(int)
    #client.torrents_pause(torrent_hashes='all')

    print('Collecting tags...')
    for torrent in tqdm(torrent_list):
        tags_to_add = []
        #print(torrent)

        trackers = list(filter(lambda s: not s.url in tracker_exceptions, torrent.trackers))
        working = len(list(filter(lambda s: s.status == 2, trackers))) > 0

        if not working:
            tags_to_add.append('Not Working')

        added_on = datetime.fromtimestamp(torrent.added_on)
        diff = today - added_on

        if diff.days == 0:
            tags_to_add.append('added:24h')
            #if diff.seconds/3600 <= 1:
            #    tags_to_add.append('added:1h')
            #if diff.seconds/3600 <= 6:
            #    tags_to_add.append('added:6h')
            #if diff.seconds/3600 <= 12:
            #    tags_to_add.append('added:12h')

        if diff.days <= 7:
            tags_to_add.append('added:7d')

        if diff.days <= 30:
            tags_to_add.append('added:30d')

        for tracker in trackers:
            domain = tldextract.extract(tracker.url).registered_domain
            if len(domain) > 0:
                tags_to_add.append(f"t:{domain}")

            matches = ['unregistered', 'not registered', 'not found', 'not exist']
            if any(x in tracker.msg.lower() for x in matches):
                tags_to_add.append('Unregistered')

        for t in tags_to_add:
            tag_hashes[t].append(torrent.hash)
            tag_sizes[t] += torrent.size

    print('Adding tags...')
    for tag in tqdm(tag_hashes):
        size = format_bytes(tag_sizes[tag])
        client.torrents_add_tags(tags=f"{tag} [{size}]", torrent_hashes=tag_hashes[tag])

if __name__ == "__main__":
    main()
