#!/usr/bin/env python3

import time
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    iterations = 0
    timeout = 5
    logger.info('Started reannounce process')

    while True:
        iterations += 1
        if iterations == 11: iterations = 1

        torrents = client.torrents.info(status_filter="downloading")

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
        time.sleep(timeout)

def add_arguments(subparser):
    parser = subparser.add_parser('reannounce')
    qbittools.add_default_args(parser)
