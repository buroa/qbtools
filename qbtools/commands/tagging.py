import tldextract
import collections

from qbtools import utils
from datetime import datetime


DEFAULT_TAGS = [
    "activity:",
    "added:",
    "dupe",
    "expired",
    "not-linked",
    "not-working",
    "unregistered",
    "tracker-down",
    "domain:",
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
    logger.info(f"Tagging torrents in qBittorrent...")

    tags = collections.defaultdict(list)
    content_paths = []

    today = datetime.today()
    extractTLD = tldextract.TLDExtract(cache_dir=None)

    trackers = app.config.get("trackers", [])
    trackers = {y: x for x in trackers for y in x["urls"]}

    unregistered_matches = app.config.get("unregistered_matches", UNREGISTERED_MATCHES)
    maintenance_matches = app.config.get("maintenance_matches", MAINTENANCE_MATCHES)

    exclude_categories = [i for s in app.exclude_category for i in s]
    if exclude_categories:
        torrents = list(
            filter(lambda x: x.category not in exclude_categories, torrents)
        )

    exclude_tags = [i for s in app.exclude_tag for i in s]
    if exclude_tags:
        torrents = list(
            filter(
                lambda x: any(y not in x.tags for y in exclude_tags), torrents
            )
        )

    torrents = app.client.torrents.info()

    for t in torrents:
        tags_to_add = []
        filtered = []

        url = t.tracker
        if not url:
            filtered = [s for s in t.trackers if s.tier >= 0] # Expensive
            if not filtered:
                continue
            url = filtered[0].url

        domain = extractTLD(url).registered_domain
        tracker = trackers.get(domain)

        if app.added_on:
            added_on = datetime.fromtimestamp(t.added_on)
            diff = today - added_on

            if diff.days == 0:
                tags_to_add.append("added:1d")
            elif diff.days <= 7:
                tags_to_add.append("added:7d")
            elif diff.days <= 30:
                tags_to_add.append("added:30d")
            elif diff.days <= 180:
                tags_to_add.append("added:180d")
            elif diff.days > 180:
                tags_to_add.append("added:>180d")

        if app.last_activity:
            last_activity = datetime.fromtimestamp(t.last_activity)
            diff = datetime.today() - last_activity

            if diff.days == 0:
                tags_to_add.append("activity:1d")
            elif diff.days <= 7:
                tags_to_add.append("activity:7d")
            elif diff.days <= 30:
                tags_to_add.append("activity:30d")
            elif diff.days <= 180:
                tags_to_add.append("activity:180d")
            elif diff.days > 180:
                tags_to_add.append("activity:>180d")

        if app.sites:
            if tracker:
                tags_to_add.append(f"site:{tracker['name']}")
            else:
                tags_to_add.append(f"site:unmapped")

        if app.domains:
            tags_to_add.append(f"domain:{domain}")

        if (app.unregistered or app.tracker_down or app.not_working) and filtered:
            tracker_messages = [z.msg.upper() for z in filtered]
            if app.unregistered and any(
                x in msg for msg in tracker_messages for x in unregistered_matches
            ):
                tags_to_add.append("unregistered")
            elif app.tracker_down and any(
                x in msg for msg in tracker_messages for x in maintenance_matches
            ):
                tags_to_add.append("tracker-down")
            elif app.not_working:
                tags_to_add.append("not-working")

        if app.expired and tracker and t.state_enum.is_complete:
            if (
                tracker["required_seed_ratio"] != 0
                and t.ratio >= tracker["required_seed_ratio"]
            ):
                tags_to_add.append("expired")
            elif tracker["required_seed_days"] != 0 and t.seeding_time >= utils.seconds(
                tracker["required_seed_days"]
            ):
                tags_to_add.append("expired")

        if app.duplicates:
            if t.content_path in content_paths and not t.content_path == t.save_path:
                tags_to_add.append("dupe")
            content_paths.append(t.content_path)

        if app.not_linked and not utils.is_linked(t.content_path):
            tags_to_add.append("not-linked")

        for tag in tags_to_add:
            tags[tag].append(t)

    empty_tags = list(
        filter(
            lambda tag: tag not in tags and any(tag.lower().startswith(x.lower()) for x in DEFAULT_TAGS),
            app.client.torrents_tags()
        )
    )
    if empty_tags:
        app.client.torrents_delete_tags(tags=empty_tags)
        logger.info(f"Removed {len(empty_tags)} old tags from qBittorrent")

    for tag, tagged in tags.items():
        old_torrents = [t.hash for t in torrents if tag in t.tags and not t in tagged]
        if old_torrents:
            app.client.torrents_remove_tags(tags=tag, torrent_hashes=old_torrents)
            logger.info(f"Untagged {len(old_torrents)} old torrents with tag: {tag}")

        new_torrents = [t.hash for t in tagged if not tag in t.tags]
        if new_torrents:
            app.client.torrents_add_tags(tags=tag, torrent_hashes=new_torrents)
            logger.info(f"Tagged {len(new_torrents)} new torrents with tag: {tag}")

    logger.info("Finished tagging torrents in qBittorrent")


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
        "--domains", action="store_true", help="Tag torrents with tracker domains"
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Tag torrents with the same content path",
    )
    parser.add_argument(
        "--expired",
        action="store_true",
        help="Tag torrents that have expired an ratio or seeding time, use with filtering by category/tag",
    )
    parser.add_argument(
        "--last-activity",
        action="store_true",
        help="Tag torrents with last activity date (last 24h, 7 days, 30 days, etc)",
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
        "--sites", action="store_true", help="Tag torrents with known site names"
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
