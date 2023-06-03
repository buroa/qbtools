#!/usr/bin/env python3

import time
import qbittools

def __init__(args, logger):
    client = qbittools.qbit_client(args)

    iterations = 0
    timeout = 5
    logger.info("Started reannounce process")

    while True:
        iterations += 1
        if iterations == 11: iterations = 1

        torrents = client.torrents.info(status_filter="downloading", sort="time_active")
        for t in torrents:
            invalid = len(list(filter(lambda s: s.status == 4, t.trackers))) > 0
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            expired = t.time_active > 60 * 60

            if expired and (not working or t.num_seeds == 0) and t.progress == 0:
                logger.warning("[%s] is inactive for too long, not reannouncing...", t.name)

            elif (invalid or not working) and t.time_active < 60:
                if invalid:
                    logger.warning("[%s] is invalid, active for %ss, pausing/resuming...", t.name, t.time_active)
                    t.pause()
                    t.resume()

                logger.info("[%s] is not working, active for %ss, reannouncing...", t.name, t.time_active)
                t.reannounce()

            elif t.num_seeds == 0 and t.progress == 0:
                if t.time_active < 120 or (t.time_active >= 120 and iterations % 2 == 0):
                    logger.info("[%s] has no seeds, active for %ss, reannouncing...", t.name, t.time_active)
                    t.reannounce()
                else:
                    wait = (2 - iterations % 2) * timeout
                    logger.info("[%s] has no seeds, active for %ss, waiting %s...", t.name, t.time_active, wait)

        torrents = client.torrents.info(status_filter="seeding", sort="time_active")
        for t in torrents:
            if t.time_active > 300:
                continue
            
            invalid = len(list(filter(lambda s: s.status == 4, t.trackers))) > 0
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0

            if invalid or not working:
                if invalid:
                    logger.warning("[%s] is invalid, active for %ss, pausing/resuming...", t.name, t.time_active)
                    t.pause()
                    t.resume()

                logger.info("[%s] is not working, active for %ss, reannouncing...", t.name, t.time_active)
                t.reannounce()

        time.sleep(timeout)

def add_arguments(subparser):
    parser = subparser.add_parser("reannounce")
    qbittools.add_default_args(parser)
