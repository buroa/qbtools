import tldextract
import collections

from qbtools import utils
from datetime import datetime
from qbittorrentapi import TrackerStatus


DEFAULT_TAGS = [
    "activity:",
    "added:",
    "dupe",
    "expired",
    "not-linked",
    "not-working",
    "unregistered",
    "tracker-down",
    "site:",
]

UNREGISTERED_MATCHES = [
    "UNREGISTERED",
    "TORRENT NOT FOUND",
    "TORRENT IS NOT",
    "NOT REGISTERED",
    "NOT EXIST",
    "UNKNOWN TORRENT",
    "TRUMP",
    "RETITLED",
    "INFOHASH NOT FOUND",  # blutopia
    "TORRENT HAS BEEN DELETED",  # blutopia
    "DEAD",
    "DUPE",
    "COMPLETE SEASON UPLOADED",
    "PROBLEM",
    "SPECIFICALLY BANNED",
    "OTHER",
    "NUKED",
    "INVALID INFOHASH",
]

MAINTENANCE_MATCHES = [
    "DOWN",
    "UNREACHABLE",
    "BAD GATEWAY",
    "TRACKER UNAVILABLE",
]


def __init__(app, logger):
    logger.info("Tagging torrents in qBittorrent...")

    today = datetime.today()
    torrents = app.client.torrents.info()
    config = app.config.get("trackers", [])
    config = {y: x for x in config for y in x["urls"]}

    exclude_categories = [i for s in app.exclude_category for i in s]
    if exclude_categories:
        torrents = list(
            filter(lambda x: x.category not in exclude_categories, torrents)
        )

    exclude_tags = [i for s in app.exclude_tag for i in s]
    if exclude_tags:
        torrents = list(
            filter(lambda x: any(y not in x.tags for y in exclude_tags), torrents)
        )

    extractTLD = tldextract.TLDExtract(cache_dir=None)
    tags = collections.defaultdict(list)
    paths = []

    for t in torrents:
        tags_to_add = []
        trackers = list(filter(lambda s: s.tier >= 0, t.trackers))  # Expensive

        url = t.tracker
        if not url and trackers:
            url = trackers[0].url

        tracker = config.get(extractTLD(url).registered_domain)

        if app.added_on:
            tags_to_add.append(calculate_date_tags("added", t.added_on, today))

        if app.last_activity:
            tags_to_add.append(calculate_date_tags("activity", t.last_activity, today))

        if app.sites:
            if tracker:
                tags_to_add.append(f"site:{tracker['name']}")
            else:
                tags_to_add.append(f"site:unmapped")

        if app.unregistered or app.tracker_down or app.not_working:
            if not any(s.status is TrackerStatus.WORKING for s in trackers):
                messages = [z.msg.upper() for z in trackers]
                if app.unregistered and any(
                    match in msg for msg in messages for match in UNREGISTERED_MATCHES
                ):
                    tags_to_add.append("unregistered")
                elif app.tracker_down and any(
                    match in msg for msg in messages for match in MAINTENANCE_MATCHES
                ):
                    tags_to_add.append("tracker-down")
                elif app.not_working:
                    tags_to_add.append("not-working")

        if app.expired and tracker and t.state_enum.is_complete:
            if (
                tracker["required_seed_ratio"]
                and t.ratio >= tracker["required_seed_ratio"]
            ):
                tags_to_add.append("expired")
            elif tracker["required_seed_days"] and t.seeding_time >= utils.seconds(
                tracker["required_seed_days"]
            ):
                tags_to_add.append("expired")

        if app.duplicates:
            if t.content_path in paths and not t.content_path == t.save_path:
                tags_to_add.append("dupe")
            else:
                paths.append(t.content_path)

        if app.not_linked and not utils.is_linked(t.content_path):
            tags_to_add.append("not-linked")

        for tag in tags_to_add:
            tags[tag].append(t)

    for tag, tagged in sorted(tags.items()):
        old_hashes = [t.hash for t in torrents if tag in t.tags and not t in tagged]
        new_hashes = [t.hash for t in tagged if not tag in t.tags]

        if old_hashes:
            app.client.torrents_remove_tags(tags=tag, torrent_hashes=old_hashes)

        if new_hashes:
            app.client.torrents_add_tags(tags=tag, torrent_hashes=new_hashes)

        if old_hashes or new_hashes:
            logger.info(
                f"{tag} - untagged {len(old_hashes)} old and tagged {len(new_hashes)} new"
            )

    empty_tags = list(
        filter(
            lambda tag: tag not in tags
            and any(tag.lower().startswith(x.lower()) for x in DEFAULT_TAGS),
            app.client.torrents_tags(),
        )
    )
    if empty_tags:
        app.client.torrents_delete_tags(tags=empty_tags)
        logger.info(f"Removed {len(empty_tags)} old tags from qBittorrent")

    logger.info("Finished tagging torrents in qBittorrent")


def calculate_date_tags(prefix, timestamp, today):
    diff = today - datetime.fromtimestamp(timestamp)
    if diff.days == 0:
        return f"{prefix}:1d"
    elif diff.days <= 7:
        return f"{prefix}:7d"
    elif diff.days <= 30:
        return f"{prefix}:30d"
    elif diff.days <= 180:
        return f"{prefix}:180d"
    else:
        return f"{prefix}:>180d"


def add_arguments(command, subparser):
    """
    Description:
        Tag torrents. This command can be used to tag torrents with various tags, such as torrents that have not been active for a while, torrents that have not been working for a while, torrents that have expired an ratio or seeding time, torrents that have the same content path, etc.
    Usage:
        qbtools.py tagging --help
    Example:
        # Tag torrents
        qbtools.py tagging --exclude-category manual --added-on --expired --last-activity --sites --unregistered
    """
    parser = subparser.add_parser(command)
    parser.add_argument(
        "--exclude-category",
        nargs="*",
        action="append",
        metavar="mycategory",
        default=[],
        help="Exclude all torrent with this category, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--exclude-tag",
        nargs="*",
        action="append",
        metavar="mytag",
        default=[],
        help="Exclude all torrents with this tag, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--added-on",
        action="store_true",
        help="Tag torrents with added date (last 24h, 7 days, 30 days, etc)",
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Tag torrents with the same content path",
    )
    parser.add_argument(
        "--expired",
        action="store_true",
        help="Tag torrents that have an expired ratio or seeding time (defined in config.yaml)",
    )
    parser.add_argument(
        "--last-activity",
        action="store_true",
        help="Tag torrents with last activity date (last 1d, 7 days, 30 days, etc)",
    )
    parser.add_argument(
        "--not-linked",
        action="store_true",
        help="Tag torrents with files without hardlinks or symlinks, use with filtering by category/tag",
    )
    parser.add_argument(
        "--not-working",
        action="store_true",
        help="Tag torrents with not working tracker status",
    )
    parser.add_argument(
        "--sites",
        action="store_true",
        help="Tag torrents with site names (defined in config.yaml)",
    )
    parser.add_argument(
        "--tracker-down",
        action="store_true",
        help="Tag torrents with temporarily down trackers",
    )
    parser.add_argument(
        "--unregistered",
        action="store_true",
        help="Tag torrents with unregistered tracker status message",
    )
