import time


def __init__(app, logger):
    logger.info("Starting reannounce process...")

    retries = {}

    def process_torrents(status):
        torrents = app.client.torrents.info(status_filter=status, sort="time_active")
        torrents_retries = retries.get(status, {})

        if torrents:
            torrents = list(filter(lambda t: t.time_active <= app.max_age, torrents))

        if not torrents:
            torrents_retries.clear()

        for t in torrents:
            if t.tracker:
                continue

            peers = t.num_seeds + t.num_leechs
            if peers:
                logger.debug(
                    f"Torrent {t.name} ({t.hash}) has {peers} peer(s) - not reannouncing"
                )
                continue

            torrent_retries = torrents_retries.get(t.hash, 0)
            if torrent_retries >= app.max_retries:
                logger.debug(
                    f"Torrent {t.name} ({t.hash}) has reached {torrent_retries} reannounce tries - not reannouncing",
                )
                continue

            t.reannounce()
            torrents_retries[t.hash] = torrent_retries + 1
            logger.info(
                f"Reannounced torrent {t.name} ({t.hash}) {torrent_retries}/{app.max_retries}",
            )

        retries[status] = torrents_retries

    while True:
        try:
            process_torrents(status="stalled_downloading")
            if app.process_seeding:
                process_torrents(status="stalled_uploading")
        except Exception as e:
            logger.error(e)

        time.sleep(app.interval)


def add_arguments(command, subparser):
    """
    Description:
        Reannounce torrents that have invalid trackers.
    Usage:
        qbtools.py reannounce --help
    """
    parser = subparser.add_parser(command)
    parser.add_argument(
        "--max-age",
        type=int,
        default=3600,
        help="The maximum age of a torrent in seconds to reannounce.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=18,
        help="The maximum number of reannounce retries for a torrent.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="The interval to process reannouncements in seconds.",
    )
    parser.add_argument(
        "--process-seeding",
        action="store_true",
        help="Process seeding torrents as well.",
    )
