#!/usr/bin/env python3

# need pip3 install qbittorrent-api

import argparse
import qbittorrentapi
import time
import logging
import sys

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%I:%M:%S %p')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', metavar='12345', help='port', required=True)
    parser.add_argument('-s', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', metavar='username', required=False)
    parser.add_argument('-P', metavar='password', required=False)
    args = parser.parse_args()

    client = qbittorrentapi.Client(host=f"{args.s}:{args.p}", username=args.U, password=args.P)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

    iterations = 0
    timeout = 5

    while True:
        iterations += 1
        if iterations == 11: iterations = 1

        torrents = client.torrents.info(status_filter="downloading")
        if len(torrents) > 0: logger.info('--------------------------')

        for t in torrents:
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            expired = t.time_active > 60 * 5

            if expired and (not working or t.num_seeds == 0) and t.progress == 0:
                logger.info(f"[{t.name}] is inactive for too long, not reannouncing...")
            elif not working:
                if t.time_active < 60:
                    logger.info(f"[{t.name}] is not working, active for {t.time_active}s, reannouncing...")
                    t.reannounce()
                else:
                    logger.info(f"[{t.name}] is not working, active for {t.time_active}s, deleted from tracker")
            elif t.num_seeds == 0 and t.progress == 0:
                if t.time_active < 120 or (t.time_active >= 120 and iterations % 2 == 0):
                    logger.info(f"[{t.name}] has no seeds, active for {t.time_active}s, reannouncing...")
                    t.reannounce()
                else:
                    logger.info(f"[{t.name}] has no seeds, active for {t.time_active}s, waiting {(2 - iterations % 2) * timeout}s...")
            elif t.num_seeds == 0 and t.progress > 0:
                if iterations % 10 == 0:
                    logger.info(f"[{t.name}] is active, but has no seeds, active for {t.time_active}s, progress: {round(t.progress * 100, 1)}%, reannouncing...")
                    t.reannounce()
                else:
                    logger.info(f"[{t.name}] is active, but has no seeds, active for {t.time_active}s, progress: {round(t.progress * 100, 1)}%, waiting {(10 - iterations % 10) * timeout}s...")
            else:
                logger.info(f"[{t.name}] is active, progress: {round(t.progress * 100, 1)}%")
        time.sleep(timeout)

if __name__ == "__main__":
        main()
