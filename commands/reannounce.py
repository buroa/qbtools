#!/usr/bin/env python3

import time

def __init__(args, logger, client):
    iterations = 0
    timeout = 5

    while True:
        iterations += 1
        if iterations == 11: iterations = 1

        torrents = client.torrents.info(status_filter="downloading")
        if len(torrents) > 0: logger.info('--------------------------')

        for t in torrents:
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            expired = t.time_active > 60 * 60

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

def add_arguments(subparser):
    subparser.add_parser('reannounce')
