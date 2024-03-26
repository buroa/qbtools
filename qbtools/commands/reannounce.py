import time
import qbtools


def __init__(args, logger):
    client = qbtools.qbit_client(args)

    iterations = 0
    timeout = 5

    def process_downloading():
        torrents = client.torrents.info(status_filter="downloading", sort="time_active")

        for t in torrents:
            invalid = len(list(filter(lambda s: s.status == 4, t.trackers))) > 0
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0
            expired = t.time_active > 60 * 60

            if expired and (not working or t.num_seeds == 0) and t.progress == 0:
                logger.warning(
                    f"[{t.name}] is inactive for too long, not reannouncing..."
                )

            elif (invalid or not working) and t.time_active < 60:
                if invalid and args.pause_resume:
                    logger.warning(
                        f"[{t.name}] is invalid, active for {t.time_active}s, pausing/resuming..."
                    )
                    t.pause()
                    t.resume()

                logger.info(
                    f"[{t.name}] is not working, active for {t.time_active}s, reannouncing..."
                )
                t.reannounce()

            elif t.num_seeds == 0 and t.progress == 0:
                if t.time_active < 120 or (
                    t.time_active >= 120 and iterations % 2 == 0
                ):
                    logger.info(
                        f"[{t.name}] has no seeds, active for {t.time_active}s, reannouncing..."
                    )
                    t.reannounce()
                else:
                    wait = (2 - iterations % 2) * timeout
                    logger.info(
                        f"[{t.name}] has no seeds, active for {t.time_active}s, waiting {wait}..."
                    )

    def process_seeding():
        torrents = client.torrents.info(status_filter="seeding", sort="time_active")

        for t in torrents:
            if t.time_active > 300:
                continue

            invalid = len(list(filter(lambda s: s.status == 4, t.trackers))) > 0
            working = len(list(filter(lambda s: s.status == 2, t.trackers))) > 0

            if invalid or not working:
                if invalid and args.pause_resume:
                    logger.warning(
                        f"[{t.name}] is invalid, active for {t.time_active}s, pausing/resuming..."
                    )
                    t.pause()
                    t.resume()

                logger.info(
                    f"[{t.name}] is not working, active for {t.time_active}s, reannouncing..."
                )
                t.reannounce()

    logger.info("Starting reannounce process...")

    while True:
        iterations += 1
        if iterations == 11:
            iterations = 1

        try:
            process_downloading()
            if args.process_seeding:
                process_seeding()
        except Exception as e:
            logger.error(e)

        time.sleep(timeout)


def add_arguments(subparser):
    parser = subparser.add_parser("reannounce")
    parser.add_argument(
        "--pause-resume",
        action="store_true",
        help="Pause+resume torrents that are invalid.",
    )
    parser.add_argument(
        "--process-seeding",
        action="store_true",
        help="Include seeding torrents for reannouncements.",
    )
    qbtools.add_default_args(parser)
