import time
import qbtools


def __init__(args, logger):
    client = qbtools.qbit_client(args)

    max_tries = 18
    max_age = 3600
    interval = 5
    retries = {}

    def process_torrents(status):
        torrents = client.torrents.info(status_filter=status, sort="time_active")
        torrents_retries = retries.get(status, {})

        if not torrents:
            torrents_retries.clear()

        for t in torrents:
            invalid = len(list(filter(lambda s: s.status == 4, t.trackers))) > 0
            if not invalid:
                continue

            if t.time_active > max_age:
                logger.debug("Torrent %s has been active for %s seconds - not reannouncing", t.name, t.time_active)
                continue

            peers = t.num_seeds + t.num_leechs
            if peers > 0:
                logger.debug("Torrent %s already has %d peer(s) - not reannouncing", t.name, peers)
                continue

            torrent_retries = torrents_retries.get(t.hash, 0)
            if torrent_retries >= max_tries:
                logger.debug("Torrent %s has reached %s reannounce tries - not reannouncing", t.name, retries)
                continue

            logger.info("Reannouncing torrent %s", t.name)
            t.reannounce()
            torrents_retries[t.hash] = torrent_retries + 1

        retries[status] = torrents_retries

    while True:
        try:
            process_torrents(status="downloading")
            if args.process_seeding:
                process_torrents(status="uploading")
        except Exception as e:
            logger.error(e)

        time.sleep(interval)


def add_arguments(subparser):
    """
    Description:
        Reannounce torrents that have invalid trackers.
    Usage:
        qbtools.py reannounce --help
    """
    parser = subparser.add_parser("reannounce")
    parser.add_argument(
        "--process-seeding",
        action="store_true",
        help="Include seeding torrents for reannouncements.",
    )
    qbtools.add_default_args(parser)
